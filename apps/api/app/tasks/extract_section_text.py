import asyncio
import logging
import time
from datetime import datetime, timezone

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings
from app.tasks.celery_app import celery_app
from app.services.s3 import get_s3
from app.services.ai_text import extract_text, EXTRACTION_MODEL

logger = logging.getLogger(__name__)


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _extract_section_text(section_id: str):
    logger.info("[extract_section_text] START section_id=%s", section_id)

    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]

    try:
        sec = await db.sections.find_one({"_id": ObjectId(section_id)})
        if not sec:
            logger.warning("[extract_section_text] section %s not found in DB", section_id)
            return {"error": "Section not found"}

        logger.info("[extract_section_text] section found: croppedImageKey=%s", sec.get("croppedImageKey"))

        cropped_key = sec.get("croppedImageKey")
        if not cropped_key:
            logger.warning("[extract_section_text] section %s has no cropped image", section_id)
            return {"error": "No cropped image"}

        s3 = get_s3()
        logger.info("[extract_section_text] downloading image from S3: bucket=%s key=%s", settings.minio_bucket, cropped_key)
        try:
            obj = s3.get_object(settings.minio_bucket, cropped_key)
            image_data = obj.read()
            logger.info("[extract_section_text] image downloaded: %d bytes", len(image_data))
        except Exception as e:
            logger.error("[extract_section_text] failed to download %s: %s", cropped_key, e)
            return {"error": f"Failed to download image: {e}"}

        logger.info("[extract_section_text] calling extract_text (OpenRouter)...")
        start_time = time.monotonic()
        try:
            result = await extract_text(image_data, db=db)
            elapsed = int((time.monotonic() - start_time) * 1000)
            logger.info("[extract_section_text] extract_text completed: text=%d chars, confidence=%.2f, model=%s, time=%dms",
                        len(result.text), result.confidence, result.model, elapsed)
        except ValueError as e:
            error_str = str(e)
            if "API key not configured" in error_str:
                logger.error("[extract_section_text] OpenRouter API key not configured: %s", e)
                error_msg = "AI service not configured. Please set OPENROUTER_API_KEY."
            else:
                logger.error("[extract_section_text] extraction failed: %s", e)
                error_msg = error_str
            await db.ai_text_extractions.update_one(
                {"sectionId": section_id},
                {"$set": {
                    "sectionId": section_id,
                    "extractedText": "",
                    "confidence": 0.0,
                    "model": "unknown",
                    "processingTimeMs": 0,
                    "status": "failed",
                    "rawResponse": {"error": error_msg},
                    "createdAt": datetime.now(timezone.utc),
                    "updatedAt": datetime.now(timezone.utc),
                }},
                upsert=True,
            )
            await db.sections.update_one(
                {"_id": ObjectId(section_id)},
                {"$set": {"extractionStatus": "failed"}},
            )
            return {"error": error_msg}
        except Exception as e:
            elapsed = int((time.monotonic() - start_time) * 1000)
            error_str = str(e)
            if "429" in error_str or "Too Many Requests" in error_str:
                error_msg = "Too many requests. Try again later."
                logger.warning("[extract_section_text] %s section_id=%s", error_msg, section_id)
            elif "401" in error_str or "Unauthorized" in error_str:
                error_msg = "Authentication failed. Check API key."
                logger.warning("[extract_section_text] %s section_id=%s", error_msg, section_id)
            elif "503" in error_str or "Service Unavailable" in error_str:
                error_msg = "Service unavailable. Try again later."
                logger.warning("[extract_section_text] %s section_id=%s", error_msg, section_id)
            else:
                error_msg = "AI extraction failed. Try again."
                logger.error("[extract_section_text] extraction FAILED for %s after %dms: %s", section_id, elapsed, e, exc_info=True)
            await db.ai_text_extractions.update_one(
                {"sectionId": section_id},
                {"$set": {
                    "sectionId": section_id,
                    "extractedText": "",
                    "confidence": 0.0,
                    "model": EXTRACTION_MODEL,
                    "processingTimeMs": elapsed,
                    "status": "failed",
                    "rawResponse": {"error": error_msg},
                    "createdAt": datetime.now(timezone.utc),
                    "updatedAt": datetime.now(timezone.utc),
                }},
                upsert=True,
            )
            await db.sections.update_one(
                {"_id": ObjectId(section_id)},
                {"$set": {"extractionStatus": "failed"}},
            )
            return {"error": error_msg}

        logger.info("[extract_section_text] saving result to ai_text_extractions collection...")
        await db.ai_text_extractions.update_one(
            {"sectionId": section_id},
            {"$set": {
                "sectionId": section_id,
                "extractedText": result.text,
                "confidence": result.confidence,
                "model": result.model,
                "processingTimeMs": result.processing_time_ms,
                "status": "completed",
                "rawResponse": result.raw_response,
                "createdAt": datetime.now(timezone.utc),
                "updatedAt": datetime.now(timezone.utc),
            }},
            upsert=True,
        )

        logger.info("[extract_section_text] updating section document with aiExtractedText...")
        await db.sections.update_one(
            {"_id": ObjectId(section_id)},
            {"$set": {
                "aiExtractedText": result.text,
                "extractionStatus": "extracted",
            }},
        )

        logger.info("[extract_section_text] DONE section_id=%s confidence=%.2f time=%dms",
                     section_id, result.confidence, result.processing_time_ms)

        return {
            "section_id": section_id,
            "text": result.text,
            "confidence": result.confidence,
        }

    finally:
        client.close()


@celery_app.task(bind=True, max_retries=3)
def extract_section_text(self, section_id: str):
    logger.info("[extract_section_text] TASK STARTED section_id=%s task_id=%s", section_id, self.request.id)
    try:
        result = run_async(_extract_section_text(section_id))
        logger.info("[extract_section_text] TASK COMPLETED section_id=%s result=%s", section_id, result)
        return result
    except Exception as e:
        logger.error("[extract_section_text] TASK FAILED section_id=%s: %s", section_id, e, exc_info=True)
        raise
