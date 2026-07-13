from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime, timezone

from app.db.client import get_db
from app.models.page_status import PageStatus, parse_page_status, with_translation_progress
from app.models.review_status import compute_review_status
from app.schemas.page import PageResponse, PageListItem, PageListResponse, PageImageResponse
from app.schemas.book_organization import (
    PageReorderRequest,
    PageReorderResponse,
    ReorderedPageRef,
    AddPageRequest,
    DeletePageResponse,
    PageWithProgress,
    PageListStats,
    PaginationInfo,
    FilteredPageListResponse,
    PageHistoryResponse,
    SectionEditHistoryEntry,
    SectionEditHistorySnapshot,
)
from app.schemas.refs import BookRef, SectionRef, TranslatorRef, ApprovedByRef
from app.schemas.translation import TranslationResponse
from app.services.page_progress import count_section_translation_progress
from app.services.s3 import get_presigned_url
from app.tasks.detect_sections import detect_sections
from app.tasks.crop_sections import crop_sections
from app.tasks.recompute_book_stats import recompute_book_stats_task
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/api/books/{book_id}/pages")
async def list_pages(
    book_id: str,
    status: str | None = Query(None),
    sort: str = Query("PAGE_NUMBER"),
    filter: str | None = Query(None, alias="filter"),
    review_status: str | None = Query(None, alias="reviewStatus"),
    sort_by: str | None = Query(None, alias="sort_by"),
    sort_order: str = Query("asc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(35, ge=1, le=200),
    page: int = Query(1, ge=1),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """List pages with optional filter, sort, and pagination support."""
    filter_param = filter or status or "all"
    use_aggregation = (
        filter_param not in ("all", "ALL", None)
        or review_status not in ("all", "ALL", None)
        or sort == "PROGRESS"
    )
    sort_field = sort_by or "pageNumber"
    sort_dir = 1 if sort_order == "asc" else -1

    if sort == "PROGRESS":
        sort_field = "translation_percent"

    if use_aggregation:
        # Callers pass skip/limit (offset-based), not page — derive page from skip so
        # the aggregation path's $skip/$limit stages actually advance on scroll instead
        # of always returning the first window.
        effective_page = (skip // limit) + 1 if skip else page
        return await _list_pages_with_aggregation(
            db, book_id, filter_param, sort_field, sort_dir, effective_page, limit, review_status
        )

    mongo_filter: dict = {"book.id": book_id}
    if status and status != "ALL":
        mongo_filter["status"] = status

    total = await db.pages.count_documents(mongo_filter)

    cursor = db.pages.find(mongo_filter).sort(sort_field, sort_dir).skip(skip).limit(limit)
    pages = await cursor.to_list(length=limit)

    page_ids = [str(page["_id"]) for page in pages]
    progress_by_page = await count_section_translation_progress(db, page_ids)

    items = []
    for page_doc in pages:
        page_id = str(page_doc["_id"])
        section_count, translated_count, approved_count, rejected_count = progress_by_page.get(
            page_id, (0, 0, 0, 0)
        )
        stored_status = parse_page_status(page_doc.get("status"))
        display_status = with_translation_progress(stored_status, section_count, translated_count)
        review_status = compute_review_status(
            section_count, translated_count, approved_count, rejected_count > 0
        )
        thumbnail_key = page_doc.get("thumbnailKey")
        thumbnail_url = await get_presigned_url(thumbnail_key) if thumbnail_key else None
        items.append(
            PageListItem(
                id=page_id,
                pageNumber=page_doc["pageNumber"],
                originalPageNumber=page_doc.get("originalPageNumber", str(page_doc["pageNumber"])),
                status=display_status,
                sectionCount=section_count,
                translatedPercent=(translated_count / section_count * 100) if section_count else 0,
                thumbnailUrl=thumbnail_url,
                reviewStatus=review_status,
            )
        )
    return PageListResponse(items=items, total=total, skip=skip, limit=limit)


async def _list_pages_with_aggregation(
    db: AsyncIOMotorDatabase,
    book_id: str,
    filter_param: str,
    sort_field: str,
    sort_order: int,
    page: int,
    limit: int,
    review_status_param: str | None = None,
) -> FilteredPageListResponse:
    """List pages with computed translation status via aggregation pipeline."""
    pipeline: list[dict] = [
        {"$match": {"book.id": book_id}},
        {"$sort": {"order": 1}},
        {
            "$lookup": {
                "from": "sections",
                "let": {"page_id": {"$toString": "$_id"}},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$page.id", "$$page_id"]}}},
                    {
                        "$lookup": {
                            "from": "translations",
                            "let": {"sectionId": {"$toString": "$_id"}},
                            "pipeline": [
                                {"$match": {"$expr": {"$eq": ["$section.id", "$$sectionId"]}}},
                            ],
                            "as": "translations",
                        }
                    },
                    {
                        "$addFields": {
                            "approvedCount": {
                                "$size": {
                                    "$filter": {
                                        "input": "$translations",
                                        "cond": {"$eq": ["$$this.isApproved", True]},
                                    }
                                }
                            },
                            "translationCount": {"$size": "$translations"},
                            "hasTranslation": {"$gt": [{"$size": "$translations"}, 0]},
                            "hasApproval": {
                                "$gt": [
                                    {
                                        "$size": {
                                            "$filter": {
                                                "input": "$translations",
                                                "cond": {"$eq": ["$$this.isApproved", True]},
                                            }
                                        }
                                    },
                                    0,
                                ]
                            },
                            "hasRejection": {
                                "$and": [
                                    {"$gt": [{"$size": "$translations"}, 0]},
                                    {
                                        "$eq": [
                                            {
                                                "$size": {
                                                    "$filter": {
                                                        "input": "$translations",
                                                        "cond": {"$eq": ["$$this.rejected", True]},
                                                    }
                                                }
                                            },
                                            {"$size": "$translations"},
                                        ]
                                    },
                                    {
                                        "$eq": [
                                            {
                                                "$size": {
                                                    "$filter": {
                                                        "input": "$translations",
                                                        "cond": {"$eq": ["$$this.isApproved", True]},
                                                    }
                                                }
                                            },
                                            0,
                                        ]
                                    },
                                ]
                            },
                        }
                    },
                    {
                        "$group": {
                            "_id": None,
                            "totalSections": {"$sum": 1},
                            "approvedSections": {"$sum": "$approvedCount"},
                            "translationSum": {"$sum": "$translationCount"},
                            "translatedSections": {"$sum": {"$cond": ["$hasTranslation", 1, 0]}},
                            "approvedSectionsDistinct": {"$sum": {"$cond": ["$hasApproval", 1, 0]}},
                            "rejectedSections": {"$sum": {"$cond": ["$hasRejection", 1, 0]}},
                        }
                    },
                ],
                "as": "sections",
            }
        },
        {
            "$addFields": {
                "sectionCount": {
                    "$ifNull": [{"$arrayElemAt": ["$sections.totalSections", 0]}, 0]
                },
                "approvedSectionCount": {
                    "$ifNull": [{"$arrayElemAt": ["$sections.approvedSections", 0]}, 0]
                },
                "translationSum": {
                    "$ifNull": [{"$arrayElemAt": ["$sections.translationSum", 0]}, 0]
                },
                "translatedSectionCount": {
                    "$ifNull": [{"$arrayElemAt": ["$sections.translatedSections", 0]}, 0]
                },
                "approvedSectionCountDistinct": {
                    "$ifNull": [{"$arrayElemAt": ["$sections.approvedSectionsDistinct", 0]}, 0]
                },
                "rejectedSectionCount": {
                    "$ifNull": [{"$arrayElemAt": ["$sections.rejectedSections", 0]}, 0]
                },
            }
        },
        {
            "$addFields": {
                "computedStatus": {
                    "$switch": {
                        "branches": [
                            {"case": {"$eq": ["$sectionCount", 0]}, "then": "not_started"},
                            {
                                "case": {"$eq": ["$approvedSectionCount", "$sectionCount"]},
                                "then": "completed",
                            },
                            {
                                "case": {
                                    "$and": [
                                        {"$gt": ["$translationSum", 0]},
                                        {"$lt": ["$approvedSectionCount", "$sectionCount"]},
                                    ]
                                },
                                "then": "in_progress",
                            },
                        ],
                        "default": "not_started",
                    }
                },
                "translationPercent": {
                    "$cond": [
                        {"$gt": ["$sectionCount", 0]},
                        {
                            "$multiply": [
                                {"$divide": ["$approvedSectionCount", "$sectionCount"]},
                                100,
                            ]
                        },
                        0,
                    ]
                },
                # Mirrors compute_review_status()'s priority order exactly (rejected
                # wins over everything else, then not-started, etc). Must be kept in
                # sync with app/models/review_status.py if that priority chain changes.
                # Uses the section-distinct counts (approvedSectionCountDistinct,
                # rejectedSectionCount), not the doc-count-based approvedSectionCount
                # that drives the legacy computedStatus above.
                "reviewStatusComputed": {
                    "$switch": {
                        "branches": [
                            {"case": {"$gt": ["$rejectedSectionCount", 0]}, "then": "REJECTED"},
                            {"case": {"$eq": ["$sectionCount", 0]}, "then": "NOT_STARTED"},
                            {
                                "case": {"$eq": ["$translatedSectionCount", 0]},
                                "then": "NO_TRANSLATIONS",
                            },
                            {
                                "case": {"$lt": ["$translatedSectionCount", "$sectionCount"]},
                                "then": "PARTIALLY_TRANSLATED",
                            },
                            {
                                "case": {"$eq": ["$approvedSectionCountDistinct", 0]},
                                "then": "FULLY_TRANSLATED",
                            },
                            {
                                "case": {
                                    "$lt": ["$approvedSectionCountDistinct", "$sectionCount"]
                                },
                                "then": "PARTIALLY_APPROVED",
                            },
                        ],
                        "default": "FULLY_APPROVED",
                    }
                },
            }
        },
    ]

    if filter_param and filter_param != "all":
        pipeline.append({"$match": {"computedStatus": filter_param}})

    if review_status_param and review_status_param not in ("all", "ALL"):
        pipeline.append({"$match": {"reviewStatusComputed": review_status_param}})

    if sort_field == "translation_percent":
        pipeline.append({"$sort": {"translationPercent": sort_order}})
    else:
        pipeline.append({"$sort": {"order": sort_order}})

    # Stats aggregation
    stats_pipeline = pipeline.copy() + [
        {
            "$group": {
                "_id": None,
                "totalPages": {"$sum": 1},
                "totalSections": {"$sum": "$sectionCount"},
                "translatedSections": {"$sum": "$approvedSectionCount"},
            }
        }
    ]
    stats_result = await db.pages.aggregate(stats_pipeline).to_list(length=1)

    # Total count for pagination
    any_filter_active = (filter_param and filter_param != "all") or (
        review_status_param and review_status_param not in ("all", "ALL")
    )
    count_pipeline = [{"$match": {"book.id": book_id}}]
    if any_filter_active:
        # Re-run the full pipeline with just the filter(s) for count
        count_pipeline = pipeline[:-1] if pipeline else count_pipeline
    count_result = await db.pages.aggregate(
        count_pipeline + [{"$count": "total"}]
    ).to_list(length=1)
    total_count = count_result[0]["total"] if count_result else 0
    total_pages_agg = max(1, (total_count + limit - 1) // limit) if total_count > 0 else 0

    # Apply pagination
    pipeline.append({"$skip": (page - 1) * limit})
    pipeline.append({"$limit": limit})

    cursor = db.pages.aggregate(pipeline)
    agg_pages = await cursor.to_list(length=limit)

    page_list = []
    for p in agg_pages:
        thumbnail_key = p.get("thumbnailKey")
        thumbnail_url = await get_presigned_url(thumbnail_key) if thumbnail_key else None
        review_status = compute_review_status(
            p.get("sectionCount", 0),
            p.get("translatedSectionCount", 0),
            p.get("approvedSectionCountDistinct", 0),
            p.get("rejectedSectionCount", 0) > 0,
        )
        page_list.append(
            PageWithProgress(
                id=str(p["_id"]),
                pageNumber=p.get("pageNumber", 0),
                originalPageNumber=p.get("originalPageNumber", str(p.get("pageNumber", ""))),
                order=p.get("order", p.get("pageNumber", 0)),
                status=p.get("status", "PENDING"),
                thumbnailUrl=thumbnail_url,
                sectionCount=p.get("sectionCount", 0),
                approvedSectionCount=p.get("approvedSectionCount", 0),
                translationPercent=round(p.get("translationPercent", 0), 1),
                computedStatus=p.get("computedStatus", "not_started"),
                reviewStatus=review_status,
            )
        )

    stats_data = stats_result[0] if stats_result else {}
    total_sections = stats_data.get("totalSections", 0)
    translated_sections = stats_data.get("translatedSections", 0)
    page_list_stats = PageListStats(
        totalPages=stats_data.get("totalPages", total_count),
        totalSections=total_sections,
        translatedSections=translated_sections,
        pendingReviewSections=total_sections - translated_sections,
        overallPercent=round((translated_sections / max(total_sections, 1)) * 100, 1),
    )

    return FilteredPageListResponse(
        pages=page_list,
        pagination=PaginationInfo(
            page=page,
            limit=limit,
            total=total_count,
            totalPages=total_pages_agg,
        ),
        stats=page_list_stats,
    )


@router.put("/api/books/{book_id}/pages/reorder")
async def reorder_pages(
    book_id: str,
    body: PageReorderRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Batch reorder pages by updating the `order` field on each page document."""
    page_ids = [ObjectId(o.pageId) for o in body.orders]
    matching = await db.pages.count_documents({"_id": {"$in": page_ids}, "book.id": book_id})
    if matching != len(page_ids):
        raise HTTPException(400, "One or more pageIds do not belong to this book")

    orders_set = {o.order for o in body.orders}
    if len(orders_set) != len(body.orders):
        raise HTTPException(400, "Duplicate order values detected")

    from pymongo import UpdateOne
    ops = []
    for o in body.orders:
        ops.append(
            UpdateOne(
                {"_id": ObjectId(o.pageId), "book.id": book_id},
                {"$set": {"order": o.order, "updatedAt": datetime.now(timezone.utc)}},
            )
        )

    if ops:
        result = await db.pages.bulk_write(ops)
        if result.matched_count != len(ops):
            raise HTTPException(
                409,
                "Page order was modified by another editor. Please refresh and try again.",
            )

    cursor = db.pages.find({"_id": {"$in": page_ids}})
    updated_pages = await cursor.to_list(length=len(page_ids))
    page_refs = [
        ReorderedPageRef(
            id=str(p["_id"]),
            order=p.get("order", p.get("pageNumber", 0)),
            pageNumber=p.get("pageNumber", 0),
        )
        for p in updated_pages
    ]

    return PageReorderResponse(success=True, reorderedCount=len(page_refs), pages=page_refs)


@router.post("/api/books/{book_id}/pages")
async def add_page(
    book_id: str,
    body: AddPageRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Add a blank page after the specified order position."""
    book = await db.books.find_one({"_id": ObjectId(book_id)})
    if not book:
        raise HTTPException(404, "Book not found")

    current_count = await db.pages.count_documents({"book.id": book_id})
    if body.insertAfterOrder > current_count:
        raise HTTPException(400, "insertAfterOrder must be >= 0 and <= page count")

    from pymongo import UpdateOne
    shift_ops = []
    cursor = db.pages.find({"book.id": book_id, "order": {"$gt": body.insertAfterOrder}})
    pages_to_shift = await cursor.to_list(length=current_count)
    for p in pages_to_shift:
        shift_ops.append(
            UpdateOne(
                {"_id": p["_id"]},
                {"$set": {"order": p.get("order", 0) + 1}},
            )
        )
    if shift_ops:
        await db.pages.bulk_write(shift_ops)

    now = datetime.now(timezone.utc)
    new_page = {
        "book": {"id": book_id},
        "pageNumber": 0,
        "originalPageNumber": "inserted",
        "order": body.insertAfterOrder + 1,
        "imageKey": None,
        "thumbnailKey": None,
        "width": 0,
        "height": 0,
        "status": PageStatus.PENDING,
        "createdAt": now,
        "updatedAt": now,
    }
    result = await db.pages.insert_one(new_page)

    return {
        "id": str(result.inserted_id),
        "bookId": book_id,
        "pageNumber": 0,
        "originalPageNumber": "inserted",
        "order": body.insertAfterOrder + 1,
        "imageKey": None,
        "thumbnailKey": None,
        "status": PageStatus.PENDING,
        "createdAt": now,
    }


@router.delete("/api/pages/{page_id}")
async def delete_page(
    page_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Delete a page and cascade all child documents."""
    page = await db.pages.find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(404, "Page not found")

    book_id = page["book"]["id"]
    remaining_count = await db.pages.count_documents({"book.id": book_id})
    if remaining_count <= 1:
        raise HTTPException(
            400,
            "Cannot delete the only page of a book. A book must have at least one page.",
        )

    sections_cursor = db.sections.find({"page.id": page_id})
    sections = await sections_cursor.to_list(length=200)
    section_ids = [str(s["_id"]) for s in sections]

    # Delete in dependency order
    if section_ids:
        await db.translations.delete_many({"section.id": {"$in": section_ids}})
        await db.comments.delete_many({"section.id": {"$in": section_ids}})
        await db.ai_text_extractions.delete_many({"sectionId": {"$in": section_ids}})
        await db.transliterations.delete_many({"sectionId": {"$in": section_ids}})
        await db.sections.delete_many({"_id": {"$in": [ObjectId(sid) for sid in section_ids]}})

    await db.pages.delete_one({"_id": ObjectId(page_id)})

    # Compact order on remaining pages
    remaining_cursor = db.pages.find({"book.id": book_id}).sort("order", 1)
    remaining = await remaining_cursor.to_list(length=remaining_count - 1)

    from pymongo import UpdateOne
    compact_ops = []
    for i, p in enumerate(remaining, start=1):
        compact_ops.append(UpdateOne({"_id": p["_id"]}, {"$set": {"order": i}}))
    if compact_ops:
        await db.pages.bulk_write(compact_ops)

    return DeletePageResponse(
        success=True,
        deleted={
            "page": 1,
            "sections": len(sections),
            "translations": 0,
            "comments": 0,
            "aiTextExtractions": 0,
        },
    )


@router.get("/api/pages/{page_id}/history")
async def get_page_history(
    page_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Fetch section edit history for a page."""
    page = await db.pages.find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(404, "Page not found")

    cursor = db.section_edit_history.find({"pageId": page_id}).sort("timestamp", -1)
    history = await cursor.to_list(length=100)

    entries = []
    for h in history:
        entries.append(
            SectionEditHistoryEntry(
                id=str(h["_id"]),
                editorId=h.get("editorId", ""),
                editorName=h.get("editorName", "Unknown"),
                action=h.get("action", "UPDATE"),
                snapshot=SectionEditHistorySnapshot(
                    sections=h.get("snapshot", {}).get("sections", [])
                ),
                timestamp=h.get("timestamp", datetime.now(timezone.utc)),
            )
        )

    return PageHistoryResponse(pageId=page_id, history=entries)


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
    section_count, translated_count, _, _ = progress_by_page.get(page_id, (0, 0, 0, 0))
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


@router.get("/api/books/{book_id}/pages/{page_num}/image")
async def get_page_image(
    book_id: str, page_num: int, db: AsyncIOMotorDatabase = Depends(get_db)
) -> PageImageResponse:
    page = await db.pages.find_one({"book.id": book_id, "pageNumber": page_num})
    if not page:
        raise HTTPException(404, "Page not found")

    total_pages = await db.pages.count_documents({"book.id": book_id})

    image_key = page.get("imageKey")
    image_url = await get_presigned_url(image_key) if image_key else None

    return PageImageResponse(
        pageNumber=page["pageNumber"],
        imageUrl=image_url,
        totalPages=total_pages,
    )


@router.post("/api/pages/{page_id}/sections/detect")
async def trigger_detection(page_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    page = await db.pages.find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(404, "Page not found")
    detect_sections.delay(page_id)
    return {"status": PageStatus.PROCESSING}


@router.put("/api/pages/{page_id}/sections")
async def save_sections(
    page_id: str,
    body: list[dict],
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
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

    # Record in section edit history
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    editor_name = user.get("name", "Unknown") if user else "Unknown"
    await db.section_edit_history.insert_one({
        "pageId": page_id,
        "editorId": user_id,
        "editorName": editor_name,
        "action": "UPDATE",
        "snapshot": {"sections": sorted_sections},
        "timestamp": datetime.now(timezone.utc),
    })

    crop_sections.delay(page_id)

    if page.get("book"):
        recompute_book_stats_task.delay(page["book"]["id"])

    return {"status": PageStatus.SECTIONS_CONFIRMED}


@router.get("/api/books/{book_id}/pages/{page_num}/review")
async def get_page_review(
    book_id: str,
    page_num: int,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    page = await db.pages.find_one({"book.id": book_id, "pageNumber": page_num})
    if not page:
        raise HTTPException(404, "Page not found")

    sections_cursor = db.sections.find({"page.id": str(page["_id"])}).sort("sectionOrder", 1)
    sections = await sections_cursor.to_list(length=500)

    page_image_url = None
    if page.get("imageKey"):
        page_image_url = await get_presigned_url(page["imageKey"])

    result_sections = []
    section_count = len(sections)
    translated_section_count = 0
    approved_section_count = 0
    has_rejection = False
    for sec in sections:
        cropped_url = None
        if sec.get("croppedImageKey"):
            cropped_url = await get_presigned_url(sec["croppedImageKey"])

        trans_cursor = db.translations.find({"section.id": str(sec["_id"])}).sort("createdAt", 1)
        translations = await trans_cursor.to_list(length=100)

        section_approved = any(t.get("isApproved") for t in translations)
        if translations:
            translated_section_count += 1
        if section_approved:
            approved_section_count += 1
        if translations and not section_approved and all(t.get("rejected") for t in translations):
            has_rejection = True

        trans_result = []
        for t in translations:
            translator_user = await db.users.find_one({"_id": ObjectId(t["translator"]["id"])})
            trans_result.append(
                TranslationResponse(
                    id=str(t["_id"]),
                    section=SectionRef(id=str(t["section"]["id"])),
                    translator=TranslatorRef(id=t["translator"]["id"]),
                    translatorName=translator_user.get("name") if translator_user else None,
                    translatedText=t["translatedText"],
                    exactLetterTranslation=t.get("exactLetterTranslation"),
                    isApproved=t.get("isApproved", False),
                    isEditorOverride=t.get("isEditorOverride", False),
                    rejected=t.get("rejected", False),
                    approvedBy=ApprovedByRef(id=t["approvedBy"]["id"]) if t.get("approvedBy") else None,
                    createdAt=t.get("createdAt"),
                )
            )

        result_sections.append({
            "id": str(sec["_id"]),
            "pageNumber": page_num,
            "sectionOrder": sec["sectionOrder"],
            "type": sec.get("type", "PARAGRAPH"),
            "originalText": sec.get("originalText"),
            "aiExtractedText": sec.get("aiExtractedText"),
            "exactLetterTranslation": sec.get("exactLetterTranslation"),
            "autoTranslatedText": sec.get("autoTranslatedText"),
            "wordByWordMeaning": sec.get("wordByWordMeaning"),
            "fullMeaning": sec.get("fullMeaning"),
            "simplifiedMeaning": sec.get("simplifiedMeaning"),
            "croppedImageUrl": cropped_url,
            "translations": trans_result,
        })

    review_status = compute_review_status(
        section_count, translated_section_count, approved_section_count, has_rejection
    )

    return {
        "page": {
            "id": str(page["_id"]),
            "pageNumber": page_num,
            "imageUrl": page_image_url,
            "status": page.get("status"),
            "reviewed": page.get("reviewed", False),
            "reviewStatus": review_status,
        },
        "sections": result_sections,
    }


@router.post("/api/books/{book_id}/pages/{page_num}/finish-review")
async def finish_page_review(
    book_id: str,
    page_num: int,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    page = await db.pages.find_one({"book.id": book_id, "pageNumber": page_num})
    if not page:
        raise HTTPException(404, "Page not found")

    page_id = str(page["_id"])
    section_count, _, approved_count, _ = (
        await count_section_translation_progress(db, [page_id])
    ).get(page_id, (0, 0, 0, 0))
    if section_count == 0 or approved_count < section_count:
        raise HTTPException(
            400,
            "All sections must have an approved translation before finishing review",
        )

    await db.pages.update_one(
        {"_id": ObjectId(page_id)},
        {"$set": {"reviewed": True, "reviewedBy": user_id, "reviewedAt": datetime.now(timezone.utc)}},
    )

    return {"status": "ok", "reviewed": True}


@router.post("/api/pages/{page_id}/finalize")
async def finalize_page(page_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    page = await db.pages.find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(404, "Page not found")

    stored_status = parse_page_status(page.get("status"))
    if stored_status != PageStatus.SECTIONS_CONFIRMED:
        raise HTTPException(400, "Page sections must be confirmed before finalizing")

    section_count, _, approved_count, _ = (
        await count_section_translation_progress(db, [page_id])
    ).get(page_id, (0, 0, 0, 0))
    if section_count == 0 or approved_count < section_count:
        raise HTTPException(
            400,
            "All sections must have an approved translation before finalizing",
        )

    await db.pages.update_one(
        {"_id": ObjectId(page_id)}, {"$set": {"status": PageStatus.FINALIZED}}
    )

    return {"status": PageStatus.FINALIZED}
