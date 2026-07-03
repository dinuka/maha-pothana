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

        page_width = page.get("width", 800)
        page_height = page.get("height", 600)

        sections = [
            {
                "page": {"id": page_id},
                "sectionOrder": 0,
                "type": "HEADER",
                "x": max(20, int(page_width * 0.05)),
                "y": max(10, int(page_height * 0.02)),
                "width": max(100, int(page_width * 0.9)),
                "height": max(30, int(page_height * 0.08)),
                "originalText": None,
                "croppedImageKey": None,
            },
            {
                "page": {"id": page_id},
                "sectionOrder": 1,
                "type": "PARAGRAPH",
                "x": max(20, int(page_width * 0.05)),
                "y": max(50, int(page_height * 0.12)),
                "width": max(100, int(page_width * 0.9)),
                "height": max(50, int(page_height * 0.3)),
                "originalText": None,
                "croppedImageKey": None,
            },
            {
                "page": {"id": page_id},
                "sectionOrder": 2,
                "type": "PARAGRAPH",
                "x": max(20, int(page_width * 0.05)),
                "y": max(50, int(page_height * 0.45)),
                "width": max(100, int(page_width * 0.9)),
                "height": max(50, int(page_height * 0.3)),
                "originalText": None,
                "croppedImageKey": None,
            },
            {
                "page": {"id": page_id},
                "sectionOrder": 3,
                "type": "FOOTNOTE",
                "x": max(20, int(page_width * 0.05)),
                "y": max(50, int(page_height * 0.78)),
                "width": max(100, int(page_width * 0.6)),
                "height": max(20, int(page_height * 0.06)),
                "originalText": None,
                "croppedImageKey": None,
            },
            {
                "page": {"id": page_id},
                "sectionOrder": 4,
                "type": "PAGE_NUMBER",
                "x": max(50, int(page_width * 0.8)),
                "y": max(50, int(page_height * 0.88)),
                "width": max(30, int(page_width * 0.1)),
                "height": max(15, int(page_height * 0.04)),
                "originalText": None,
                "croppedImageKey": None,
            },
        ]

        for sec in sections:
            await db.sections.insert_one(sec)

        await db.pages.update_one({"_id": ObjectId(page_id)}, {"$set": {"status": "PENDING"}})
        return {"page_id": page_id, "sections": len(sections)}

    finally:
        client.close()


@celery_app.task(bind=True, max_retries=3)
def detect_sections(self, page_id: str):
    return run_async(_detect_sections(page_id))
