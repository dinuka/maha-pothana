from app.tasks.celery_app import celery_app
from app.config import settings
from app.models.page_status import PageStatus
from app.services.s3 import get_s3, upload_file
from app.services.pdf import (
    extract_page_count,
    render_page_as_image,
    render_page_as_thumbnail,
    get_page_dimensions,
)
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import asyncio
import io
import logging

logger = logging.getLogger(__name__)


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _split_pages(book_id: str):
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]

    try:
        book = await db.books.find_one({"_id": ObjectId(book_id)})
        if not book:
            logger.info("split_pages book_id=%s not found", book_id)
            return {"error": "Book not found"}

        s3 = get_s3()
        obj = s3.get_object(settings.minio_bucket, book["fileKey"])
        pdf_data = obj.read()
        logger.info("split_pages book_id=%s downloaded fileKey=%s bytes=%d", book_id, book["fileKey"], len(pdf_data))

        page_count = extract_page_count(pdf_data)
        logger.info("split_pages book_id=%s page_count=%d", book_id, page_count)

        for i in range(page_count):
            img_data = render_page_as_image(pdf_data, i)
            if img_data is None:
                logger.info("split_pages book_id=%s page=%d render failed, skipping", book_id, i + 1)
                continue

            width, height = get_page_dimensions(pdf_data, i)
            page_key = f"books/{book_id}/pages/{i + 1}.png"
            await upload_file(page_key, img_data, "image/png")

            thumbnail_key = None
            thumb_data = render_page_as_thumbnail(pdf_data, i)
            if thumb_data is not None:
                thumbnail_key = f"books/{book_id}/thumbnails/{i + 1}.png"
                await upload_file(thumbnail_key, thumb_data, "image/png")

            await db.pages.insert_one({
                "book": {"id": book_id},
                "pageNumber": i + 1,
                "originalPageNumber": str(i + 1),
                "imageKey": page_key,
                "thumbnailKey": thumbnail_key,
                "width": width,
                "height": height,
                "status": PageStatus.PENDING,
            })
            logger.info("split_pages book_id=%s page=%d uploaded key=%s size=%dx%d", book_id, i + 1, page_key, width, height)

        await db.books.update_one({"_id": ObjectId(book_id)}, {"$set": {"status": "READY"}})
        logger.info("split_pages book_id=%s completed pages=%d status=READY", book_id, page_count)
        return {"book_id": book_id, "pages": page_count}

    finally:
        client.close()


@celery_app.task(bind=True, max_retries=3)
def split_pages(self, book_id: str):
    logger.info("split_pages started book_id=%s", book_id)
    return run_async(_split_pages(book_id))
