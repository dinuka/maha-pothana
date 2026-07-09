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
    page_num: int | None = Query(None, alias="page"),
    status: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    book = await db.books.find_one({"_id": ObjectId(bookId)})
    if not book:
        raise HTTPException(404, "Book not found")

    match: dict = {"bookId": bookId}

    if status == "approved":
        match["action"] = "APPROVED"
    elif status == "rejected":
        match["action"] = "REJECTED"
    elif status == "submitted":
        match["action"] = "SUBMITTED"

    if translatorId:
        match["translatorId"] = translatorId

    if page_num is not None:
        match["pageNumber"] = page_num

    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(cursor.replace("Z", "+00:00"))
            match["createdAt"] = {"$lt": cursor_dt}
        except ValueError:
            pass

    items_cursor = db.translation_activity.find(match).sort("createdAt", -1).limit(limit + 1)
    items = await items_cursor.to_list(length=limit + 1)

    has_more = len(items) > limit
    items = items[:limit]

    result_items = [
        TranslationHistoryItem(
            translationId=item["translationId"],
            sectionId=item["sectionId"],
            pageNumber=item["pageNumber"],
            sectionOrder=item["sectionOrder"],
            translatorId=item["translatorId"],
            translatorName=item["translatorName"],
            translatedText=item["translatedText"],
            action=item["action"],
            performedBy=item.get("performedBy"),
            performedByName=item.get("performedByName"),
            createdAt=item["createdAt"],
        )
        for item in items
    ]

    next_cursor = None
    if has_more and result_items:
        next_cursor = result_items[-1].createdAt.isoformat()

    return TranslationHistoryResponse(
        items=result_items,
        nextCursor=next_cursor,
        hasMore=has_more,
    )
