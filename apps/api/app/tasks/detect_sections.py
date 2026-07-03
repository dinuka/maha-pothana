import asyncio
import logging

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

from app.tasks.celery_app import celery_app
from app.config import settings
from app.services.s3 import get_s3
from app.services.detection import detect_page_sections

logger = logging.getLogger(__name__)


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _detect_sections(page_id: str):
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]

    try:
        page = await db.pages.find_one({"_id": ObjectId(page_id)})
        if not page:
            logger.warning("detect_sections page_id=%s not found", page_id)
            return {"error": "Page not found"}

        await db.pages.update_one(
            {"_id": ObjectId(page_id)},
            {"$set": {"status": "PROCESSING"}},
        )

        page_width = page.get("width", 0)
        page_height = page.get("height", 0)
        image_key = page.get("imageKey")

        sections_data = None

        if image_key:
            try:
                s3 = get_s3()
                obj = s3.get_object(settings.minio_bucket, image_key)
                image_data = obj.read()

                sections_data = detect_page_sections(
                    image_data=image_data,
                    page_width=page_width,
                    page_height=page_height,
                )
                logger.info(
                    "detect_sections page_id=%s detected %d sections from image %s",
                    page_id,
                    len(sections_data),
                    image_key,
                )
            except Exception as e:
                logger.warning(
                    "detect_sections page_id=%s image analysis failed: %s, using fallback",
                    page_id,
                    e,
                )

        if not sections_data:
            sections_data = detect_page_sections(
                image_data=b"",
                page_width=page_width,
                page_height=page_height,
            )
            logger.info(
                "detect_sections page_id=%s using %d fallback sections",
                page_id,
                len(sections_data),
            )

        existing_count = await db.sections.count_documents({"page.id": page_id})
        if existing_count > 0:
            await db.sections.delete_many({"page.id": page_id})

        for sec in sections_data:
            await db.sections.insert_one({
                "page": {"id": page_id},
                "sectionOrder": sec["sectionOrder"],
                "type": sec["type"],
                "x": sec["x"],
                "y": sec["y"],
                "width": sec["width"],
                "height": sec["height"],
                "confidence": sec.get("confidence", 0.5),
                "originalText": None,
                "croppedImageKey": None,
            })

        await db.pages.update_one(
            {"_id": ObjectId(page_id)},
            {"$set": {"status": "PENDING"}},
        )

        return {"page_id": page_id, "sections": len(sections_data)}

    except Exception as e:
        logger.error("detect_sections page_id=%s failed: %s", page_id, e, exc_info=True)
        await db.pages.update_one(
            {"_id": ObjectId(page_id)},
            {"$set": {"status": "DETECTION_FAILED"}},
        )
        return {"error": str(e)}

    finally:
        client.close()


@celery_app.task(bind=True, max_retries=3)
def detect_sections(self, page_id: str):
    logger.info("detect_sections started page_id=%s", page_id)
    return run_async(_detect_sections(page_id))
