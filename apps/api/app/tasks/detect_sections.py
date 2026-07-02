from app.tasks.celery_app import celery_app
from app.config import settings
from app.services.s3 import get_s3
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import asyncio


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
            return {"error": "Page not found"}

        s3 = get_s3()
        obj = s3.get_object(settings.minio_bucket, page["imageKey"])
        _page_image_data = obj.read()

        sections = [
            {
                "page": {"id": page_id},
                "sectionOrder": 0,
                "type": "PARAGRAPH",
                "x": 20,
                "y": 20,
                "width": page.get("width", 800) - 40,
                "height": 100,
                "originalText": None,
                "croppedImageKey": None,
            }
        ]

        for sec in sections:
            await db.sections.insert_one(sec)

        await db.pages.update_one({"_id": ObjectId(page_id)}, {"$set": {"status": "SECTIONS_CONFIRMED"}})
        return {"page_id": page_id, "sections": len(sections)}

    finally:
        client.close()


@celery_app.task(bind=True, max_retries=3)
def detect_sections(self, page_id: str):
    return run_async(_detect_sections(page_id))
