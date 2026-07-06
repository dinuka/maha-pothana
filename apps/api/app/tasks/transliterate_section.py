import asyncio
import logging
from datetime import datetime, timezone

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings
from app.tasks.celery_app import celery_app
from app.services.ai_text import transliterate_text

logger = logging.getLogger(__name__)


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _transliterate_section(section_id: str, target_script: str):
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]

    try:
        cached = await db.transliterations.find_one({
            "sectionId": section_id,
            "targetScript": target_script,
        })
        if cached and cached.get("status") == "completed":
            return {
                "transliteratedText": cached["transliteratedText"],
                "cached": True,
            }

        sec = await db.sections.find_one({"_id": ObjectId(section_id)})
        if not sec:
            return {"error": "Section not found"}

        source_text = sec.get("aiExtractedText") or sec.get("originalText")
        if not source_text:
            return {"error": "No source text available"}

        page = await db.pages.find_one({"_id": ObjectId(sec["page"]["id"])})
        book_id = page["book"]["id"] if page else None
        source_script = "unknown"
        if book_id:
            book = await db.books.find_one({"_id": ObjectId(book_id)})
            if book:
                source_script = book.get("sourceLanguage", "unknown")

        try:
            result = await transliterate_text(
                source_text=source_text,
                source_script=source_script,
                target_script=target_script,
                db=db,
            )
        except ValueError as e:
            error_msg = str(e)
            logger.error("transliterate_section: failed for %s: %s", section_id, error_msg)
            await db.transliterations.update_one(
                {"sectionId": section_id, "targetScript": target_script},
                {"$set": {"status": "failed", "error": error_msg}},
            )
            return {"error": error_msg}
        except Exception as e:
            logger.error("transliterate_section: failed for %s: %s", section_id, e)
            await db.transliterations.update_one(
                {"sectionId": section_id, "targetScript": target_script},
                {"$set": {"status": "failed", "error": str(e)}},
            )
            return {"error": str(e)}

        await db.transliterations.update_one(
            {
                "sectionId": section_id,
                "targetScript": target_script,
            },
            {"$set": {
                "sectionId": section_id,
                "sourceScript": result.source_script,
                "targetScript": result.target_script,
                "transliteratedText": result.transliterated_text,
                "confidence": result.confidence,
                "model": result.model,
                "status": "completed",
                "rawResponse": result.raw_response,
                "createdAt": datetime.now(timezone.utc),
            }},
            upsert=True,
        )

        logger.info(
            "transliterate_section: completed section_id=%s target=%s",
            section_id, target_script,
        )

        return {
            "transliteratedText": result.transliterated_text,
            "cached": False,
        }

    finally:
        client.close()


@celery_app.task(bind=True, max_retries=3)
def transliterate_section(self, section_id: str, target_script: str):
    logger.info(
        "transliterate_section started section_id=%s target=%s",
        section_id, target_script,
    )
    return run_async(_transliterate_section(section_id, target_script))
