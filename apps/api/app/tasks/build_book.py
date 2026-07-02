from app.tasks.celery_app import celery_app
from app.config import settings
from app.services.s3 import get_s3, upload_file
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import asyncio
import logging

logger = logging.getLogger(__name__)


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _build_book(book_id: str):
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]

    try:
        book = await db.books.find_one({"_id": ObjectId(book_id)})
        if not book:
            logger.info("build_book book_id=%s not found", book_id)
            return {"error": "Book not found"}

        await db.book_builds.insert_one({
            "book": {"id": book_id},
            "fileKey": None,
            "status": "BUILDING",
        })

        await db.books.update_one({"_id": ObjectId(book_id)}, {"$set": {"status": "BUILDING"}})
        logger.info("build_book book_id=%s status=BUILDING", book_id)

        # Placeholder: in production, compile translations into PDF
        finalized_key = f"books/{book_id}/finalized.pdf"
        placeholder_pdf = b"%PDF-1.4 placeholder finalized book content"
        await upload_file(finalized_key, placeholder_pdf, "application/pdf")
        logger.info("build_book book_id=%s uploaded finalized key=%s", book_id, finalized_key)

        await db.books.update_one({"_id": ObjectId(book_id)}, {"$set": {"status": "COMPLETED"}})
        await db.book_builds.update_one(
            {"book.id": book_id, "status": "BUILDING"},
            {"$set": {"fileKey": finalized_key, "status": "COMPLETED"}},
        )
        logger.info("build_book book_id=%s completed status=COMPLETED", book_id)

        return {"book_id": book_id, "status": "COMPLETED"}

    except Exception as exc:
        logger.warning("build_book book_id=%s failed error=%s", book_id, exc)
        await db.books.update_one({"_id": ObjectId(book_id)}, {"$set": {"status": "READY"}})
        await db.book_builds.update_one(
            {"book.id": book_id, "status": "BUILDING"},
            {"$set": {"status": "FAILED"}},
        )
        raise exc

    finally:
        client.close()


@celery_app.task(bind=True, max_retries=3)
def build_book(self, book_id: str):
    logger.info("build_book started book_id=%s", book_id)
    return run_async(_build_book(book_id))
