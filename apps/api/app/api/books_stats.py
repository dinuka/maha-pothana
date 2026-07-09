from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import logging

from app.db.client import get_db
from app.schemas.stats import TranslationStatsResponse, TranslatorStatsResponse
from app.services.book_stats import get_book_stats_doc, get_translator_stats_doc
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/books/{book_id}/stats")
async def get_book_stats(
    book_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
) -> TranslationStatsResponse:
    book = await db.books.find_one({"_id": ObjectId(book_id)})
    if not book:
        raise HTTPException(404, "Book not found")

    return await get_book_stats_doc(db, book_id)


@router.get("/api/books/{book_id}/translators/stats")
async def get_translator_stats(
    book_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
) -> list[TranslatorStatsResponse]:
    book = await db.books.find_one({"_id": ObjectId(book_id)})
    if not book:
        raise HTTPException(404, "Book not found")

    return await get_translator_stats_doc(db, book_id)
