from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime

from app.db.client import get_db
from app.schemas.history import TranslationHistoryItem, TranslationHistoryResponse
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/api/translations/history")
async def get_translation_history(
    bookId: str = Query(...),
    translatorId: str | None = Query(None),
    language: str | None = Query(None),
    page_num: int | None = Query(None, alias="page"),
    status: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    # Verify book exists
    book = await db.books.find_one({"_id": ObjectId(bookId)})
    if not book:
        raise HTTPException(404, "Book not found")

    # Build match conditions
    match: dict = {}

    if status == "approved":
        match["isApproved"] = True
    elif status == "rejected":
        match["isApproved"] = False
    elif status == "submitted":
        # Translations that exist but haven't been approved or rejected
        # isApproved is False and there's a translation
        match["isApproved"] = False

    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(cursor.replace("Z", "+00:00"))
            match["createdAt"] = {"$lt": cursor_dt}
        except ValueError:
            pass

    # Build pipeline
    pipeline: list[dict] = []

    if match:
        pipeline.append({"$match": match})

    # Join with sections
    pipeline.extend([
        {"$lookup": {
            "from": "sections",
            "localField": "section.id",
            "foreignField": "_id",
            "as": "sec",
        }},
        {"$unwind": {"path": "$sec", "preserveNullAndEmptyArrays": True}},
    ])

    # Join with pages
    pipeline.extend([
        {"$lookup": {
            "from": "pages",
            "localField": "sec.page.id",
            "foreignField": "_id",
            "as": "pg",
        }},
        {"$unwind": {"path": "$pg", "preserveNullAndEmptyArrays": True}},
    ])

    # Filter by book
    pipeline.append({"$match": {"pg.book.id": bookId}})

    # Apply translator filter
    if translatorId:
        pipeline.append({"$match": {"translator.id": translatorId}})

    # Apply page number filter
    if page_num is not None:
        pipeline.append({"$match": {"pg.pageNumber": page_num}})

    # Apply language filter (match against book's translateLanguages)
    if language:
        # We can't directly filter translations by language since translations
        # don't store target language. We'll filter by checking if the book
        # has the language and the translation text contains it.
        # For now, skip language filter on translations since it's not stored.
        pass

    # Join with users for translator name
    pipeline.extend([
        {"$lookup": {
            "from": "users",
            "localField": "translator.id",
            "foreignField": "_id",
            "as": "translatorUser",
        }},
        {"$unwind": {"path": "$translatorUser", "preserveNullAndEmptyArrays": True}},
    ])

    # Join with users for performedBy name
    pipeline.extend([
        {"$lookup": {
            "from": "users",
            "localField": "approvedBy.id",
            "foreignField": "_id",
            "as": "performerUser",
        }},
        {"$unwind": {"path": "$performerUser", "preserveNullAndEmptyArrays": True}},
    ])

    # Sort and limit
    pipeline.extend([
        {"$sort": {"createdAt": -1}},
        {"$limit": limit + 1},
    ])

    cursor_result = db.translations.aggregate(pipeline)
    items = await cursor_result.to_list(length=limit + 1)

    has_more = len(items) > limit
    items = items[:limit]

    result_items = []
    for item in items:
        # Determine action based on isApproved
        if item.get("isApproved"):
            action = "APPROVED"
        elif item.get("approvedBy"):
            action = "REJECTED"
        else:
            action = "SUBMITTED"

        translator_user = item.get("translatorUser")
        performer_user = item.get("performerUser")
        sec = item.get("sec", {})
        pg = item.get("pg", {})

        result_items.append(TranslationHistoryItem(
            translationId=str(item["_id"]),
            sectionId=item.get("section", {}).get("id", ""),
            pageNumber=pg.get("pageNumber", 0) if pg else 0,
            sectionOrder=sec.get("sectionOrder", 0) if sec else 0,
            translatorId=item.get("translator", {}).get("id", ""),
            translatorName=translator_user.get("name", "Unknown") if translator_user else "Unknown",
            translatedText=item.get("translatedText", ""),
            action=action,
            performedBy=item.get("approvedBy", {}).get("id") if item.get("approvedBy") else None,
            performedByName=performer_user.get("name") if performer_user else None,
            createdAt=item.get("createdAt", datetime.min),
        ))

    next_cursor = None
    if has_more and result_items:
        next_cursor = result_items[-1].createdAt.isoformat()

    return TranslationHistoryResponse(
        items=result_items,
        nextCursor=next_cursor,
        hasMore=has_more,
    )
