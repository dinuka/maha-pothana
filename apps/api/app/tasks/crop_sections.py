from app.tasks.celery_app import celery_app
from app.config import settings
from app.services.s3 import get_s3, upload_file
from app.services.crop import crop_section
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3)
def crop_sections(self, page_id: str):
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]

    try:
        page = run_async(db.pages.find_one({"_id": page_id}))
        if not page:
            return {"error": "Page not found"}

        s3 = get_s3()
        page_obj = s3.get_object(settings.minio_bucket, page["imageKey"])
        page_image_data = page_obj.read()
        book_id = page["bookId"]

        cursor = db.sections.find({"pageId": page_id})
        sections = list(run_async(cursor.to_list(length=1000)))

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
                upload_file(section_key, cropped, "image/png")
                run_async(
                    db.sections.update_one(
                        {"_id": sec["_id"]},
                        {"$set": {"croppedImageKey": section_key}},
                    )
                )
                cropped_count += 1

        return {"page_id": page_id, "sections_cropped": cropped_count}

    finally:
        client.close()
