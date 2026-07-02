from app.tasks.celery_app import celery_app
from app.config import settings
from app.services.s3 import get_s3, upload_file
from app.services.crop import crop_section
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


async def _crop_sections(page_id: str):
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]

    try:
        page = await db.pages.find_one({"_id": ObjectId(page_id)})
        if not page:
            logger.info("crop_sections page_id=%s not found", page_id)
            return {"error": "Page not found"}

        s3 = get_s3()
        page_obj = s3.get_object(settings.minio_bucket, page["imageKey"])
        page_image_data = page_obj.read()
        book_id = page["book"]["id"]
        logger.info("crop_sections page_id=%s book_id=%s downloaded imageKey=%s bytes=%d", page_id, book_id, page["imageKey"], len(page_image_data))

        cursor = db.sections.find({"page.id": page_id})
        sections = await cursor.to_list(length=1000)
        logger.info("crop_sections page_id=%s found sections=%d", page_id, len(sections))

        cropped_count = 0
        for sec in sections:
            section_id = str(sec["_id"])
            cropped = crop_section(
                page_image_data,
                sec.get("x", 0),
                sec.get("y", 0),
                sec.get("width", 100),
                sec.get("height", 50),
            )
            if cropped:
                section_key = f"books/{book_id}/sections/{section_id}.png"
                await upload_file(section_key, cropped, "image/png")
                await db.sections.update_one(
                    {"_id": sec["_id"]},
                    {"$set": {"croppedImageKey": section_key}},
                )
                cropped_count += 1
                logger.info("crop_sections page_id=%s section_id=%s cropped key=%s", page_id, section_id, section_key)
            else:
                logger.info("crop_sections page_id=%s section_id=%s crop failed, skipping", page_id, section_id)

        logger.info("crop_sections page_id=%s completed cropped=%d/%d", page_id, cropped_count, len(sections))
        return {"page_id": page_id, "sections_cropped": cropped_count}

    finally:
        client.close()


@celery_app.task(bind=True, max_retries=3)
def crop_sections(self, page_id: str):
    logger.info("crop_sections started page_id=%s", page_id)
    return run_async(_crop_sections(page_id))
