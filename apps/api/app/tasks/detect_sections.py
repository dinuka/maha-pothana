from app.tasks.celery_app import celery_app
from app.config import settings
from app.services.s3 import get_s3
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3)
def detect_sections(self, page_id: str):
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]

    try:
        page = run_async(db.pages.find_one({"_id": page_id}))
        if not page:
            return {"error": "Page not found"}

        s3 = get_s3()
        obj = s3.get_object(settings.minio_bucket, page["imageKey"])
        _page_image_data = obj.read()

        sections = [
            {
                "pageId": page_id,
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
            run_async(db.sections.insert_one(sec))

        run_async(db.pages.update_one({"_id": page_id}, {"$set": {"status": "SECTIONS_CONFIRMED"}}))
        return {"page_id": page_id, "sections": len(sections)}

    finally:
        client.close()
