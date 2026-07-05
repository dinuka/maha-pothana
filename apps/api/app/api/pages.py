from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.db.client import get_db
from app.models.page_status import PageStatus, parse_page_status, with_translation_progress
from app.schemas.page import PageResponse, PageListItem, PageListResponse
from app.schemas.refs import BookRef
from app.services.page_progress import count_section_translation_progress
from app.services.s3 import get_presigned_url
from app.tasks.detect_sections import detect_sections
from app.tasks.crop_sections import crop_sections
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/api/books/{book_id}/pages")
async def list_pages(
    book_id: str,
    status: str | None = Query(None),
    sort: str = Query("PAGE_NUMBER"),
    skip: int = Query(0, ge=0),
    limit: int = Query(35, ge=1, le=200),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> PageListResponse:
    mongo_filter: dict = {"book.id": book_id}
    if status and status != "ALL":
        mongo_filter["status"] = status

    total = await db.pages.count_documents(mongo_filter)

    # "PROGRESS" has no dedicated Mongo sort key yet: translatedPercent is computed
    # in-memory below, not stored, so both sort options resolve to pageNumber for now.
    cursor = db.pages.find(mongo_filter).sort("pageNumber", 1).skip(skip).limit(limit)
    pages = await cursor.to_list(length=limit)

    page_ids = [str(page["_id"]) for page in pages]
    progress_by_page = await count_section_translation_progress(db, page_ids)

    items = []
    for page in pages:
        page_id = str(page["_id"])
        section_count, translated_count, _ = progress_by_page.get(page_id, (0, 0, 0))
        stored_status = parse_page_status(page.get("status"))
        display_status = with_translation_progress(stored_status, section_count, translated_count)
        thumbnail_key = page.get("thumbnailKey")
        thumbnail_url = await get_presigned_url(thumbnail_key) if thumbnail_key else None
        items.append(
            PageListItem(
                id=page_id,
                pageNumber=page["pageNumber"],
                originalPageNumber=page.get("originalPageNumber", str(page["pageNumber"])),
                status=display_status,
                sectionCount=section_count,
                translatedPercent=(translated_count / section_count * 100) if section_count else 0,
                thumbnailUrl=thumbnail_url,
            )
        )
    return PageListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/api/books/{book_id}/pages/{page_num}")
async def get_page(book_id: str, page_num: int, db: AsyncIOMotorDatabase = Depends(get_db)):
    page = await db.pages.find_one({"book.id": book_id, "pageNumber": page_num})
    if not page:
        raise HTTPException(404, "Page not found")

    page_id = str(page["_id"])
    sections_cursor = db.sections.find({"page.id": page_id}).sort("sectionOrder", 1)
    sections = await sections_cursor.to_list(length=200)

    image_key = page.get("imageKey")
    image_url = await get_presigned_url(image_key) if image_key else None

    progress_by_page = await count_section_translation_progress(db, [page_id])
    section_count, translated_count, _ = progress_by_page.get(page_id, (0, 0, 0))
    stored_status = parse_page_status(page.get("status"))
    display_status = with_translation_progress(stored_status, section_count, translated_count)

    return {
        "page": PageResponse(
            id=page_id,
            book=BookRef(id=page["book"]["id"]),
            pageNumber=page["pageNumber"],
            originalPageNumber=page.get("originalPageNumber", str(page["pageNumber"])),
            imageKey=image_key,
            imageUrl=image_url,
            width=page.get("width", 0),
            height=page.get("height", 0),
            status=display_status,
            createdAt=page.get("createdAt"),
        ),
        "sections": [
            {
                "id": str(s["_id"]),
                "page": {"id": s["page"]["id"]},
                "sectionOrder": s["sectionOrder"],
                "type": s.get("type", "PARAGRAPH"),
                "x": s.get("x", 0),
                "y": s.get("y", 0),
                "width": s.get("width", 100),
                "height": s.get("height", 50),
                "originalText": s.get("originalText"),
                "croppedImageKey": s.get("croppedImageKey"),
            }
            for s in sections
        ],
    }


@router.post("/api/pages/{page_id}/sections/detect")
async def trigger_detection(page_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    page = await db.pages.find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(404, "Page not found")
    detect_sections.delay(page_id)
    return {"status": PageStatus.PROCESSING}


@router.put("/api/pages/{page_id}/sections")
async def save_sections(page_id: str, body: list[dict], db: AsyncIOMotorDatabase = Depends(get_db)):
    page = await db.pages.find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(404, "Page not found")

    await db.sections.delete_many({"page.id": page_id})

    sorted_sections = sorted(body, key=lambda s: (s.get("y", 0), s.get("x", 0)))

    for i, sec in enumerate(sorted_sections):
        await db.sections.insert_one({
            "page": {"id": page_id},
            "sectionOrder": sec.get("sectionOrder", i),
            "type": sec.get("type", "PARAGRAPH"),
            "x": sec.get("x", 0),
            "y": sec.get("y", 0),
            "width": sec.get("width", 100),
            "height": sec.get("height", 50),
            "originalText": sec.get("originalText"),
            "croppedImageKey": None,
        })

    await db.pages.update_one(
        {"_id": ObjectId(page_id)}, {"$set": {"status": PageStatus.SECTIONS_CONFIRMED}}
    )

    crop_sections.delay(page_id)

    return {"status": PageStatus.SECTIONS_CONFIRMED}


@router.post("/api/pages/{page_id}/finalize")
async def finalize_page(page_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    page = await db.pages.find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(404, "Page not found")

    stored_status = parse_page_status(page.get("status"))
    if stored_status not in (PageStatus.SECTIONS_CONFIRMED, PageStatus.FINALIZED):
        raise HTTPException(400, "Page sections must be confirmed before finalizing")

    section_count, _, approved_count = (
        await count_section_translation_progress(db, [page_id])
    ).get(page_id, (0, 0, 0))
    if section_count == 0 or approved_count < section_count:
        raise HTTPException(400, "All sections must have an approved translation before finalizing")

    await db.pages.update_one({"_id": ObjectId(page_id)}, {"$set": {"status": PageStatus.FINALIZED}})

    return {"status": PageStatus.FINALIZED}
