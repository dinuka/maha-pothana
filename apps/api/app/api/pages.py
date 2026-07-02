from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.db.client import get_db
from app.schemas.page import PageResponse, PageListItem
from app.schemas.refs import BookRef
from app.services.s3 import get_presigned_url
from app.tasks.detect_sections import detect_sections
from app.tasks.crop_sections import crop_sections
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/api/books/{book_id}/pages")
async def list_pages(book_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    cursor = db.pages.find({"book.id": book_id}).sort("pageNumber", 1)
    pages = await cursor.to_list(length=10000)
    result = []
    for page in pages:
        section_count = await db.sections.count_documents({"page.id": str(page["_id"])})
        thumbnail_key = page.get("thumbnailKey")
        thumbnail_url = await get_presigned_url(thumbnail_key) if thumbnail_key else None
        result.append(
            PageListItem(
                id=str(page["_id"]),
                pageNumber=page["pageNumber"],
                originalPageNumber=page.get("originalPageNumber", str(page["pageNumber"])),
                status=page.get("status", "PENDING"),
                sectionCount=section_count,
                thumbnailUrl=thumbnail_url,
            )
        )
    return result


@router.get("/api/books/{book_id}/pages/{page_num}")
async def get_page(book_id: str, page_num: int, db: AsyncIOMotorDatabase = Depends(get_db)):
    page = await db.pages.find_one({"book.id": book_id, "pageNumber": page_num})
    if not page:
        raise HTTPException(404, "Page not found")

    sections_cursor = db.sections.find({"page.id": str(page["_id"])}).sort("sectionOrder", 1)
    sections = await sections_cursor.to_list(length=200)

    return {
        "page": PageResponse(
            id=str(page["_id"]),
            book=BookRef(id=page["book"]["id"]),
            pageNumber=page["pageNumber"],
            originalPageNumber=page.get("originalPageNumber", str(page["pageNumber"])),
            imageKey=page.get("imageKey"),
            width=page.get("width", 0),
            height=page.get("height", 0),
            status=page.get("status", "PENDING"),
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
    return {"status": "PROCESSING"}


@router.put("/api/pages/{page_id}/sections")
async def save_sections(page_id: str, body: list[dict], db: AsyncIOMotorDatabase = Depends(get_db)):
    page = await db.pages.find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(404, "Page not found")

    await db.sections.delete_many({"page.id": page_id})

    for sec in body:
        await db.sections.insert_one({
            "page": {"id": page_id},
            "sectionOrder": sec.get("sectionOrder", 0),
            "type": sec.get("type", "PARAGRAPH"),
            "x": sec.get("x", 0),
            "y": sec.get("y", 0),
            "width": sec.get("width", 100),
            "height": sec.get("height", 50),
            "originalText": sec.get("originalText"),
            "croppedImageKey": None,
        })

    await db.pages.update_one({"_id": ObjectId(page_id)}, {"$set": {"status": "SECTIONS_CONFIRMED"}})

    crop_sections.delay(page_id)

    return {"status": "SECTIONS_CONFIRMED"}
