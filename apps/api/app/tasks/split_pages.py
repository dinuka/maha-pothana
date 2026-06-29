from app.tasks.celery_app import celery_app
from app.config import settings
from app.services.s3 import get_s3, upload_file
from app.services.pdf import extract_page_count, render_page_as_image, get_page_dimensions
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import io


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3)
def split_pages(self, book_id: str):
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]

    try:
        book = run_async(db.books.find_one({"_id": book_id}))
        if not book:
            return {"error": "Book not found"}

        s3 = get_s3()
        obj = s3.get_object(settings.minio_bucket, book["fileKey"])
        pdf_data = obj.read()

        page_count = extract_page_count(pdf_data)

        for i in range(page_count):
            img_data = render_page_as_image(pdf_data, i)
            if img_data is None:
                continue

            width, height = get_page_dimensions(pdf_data, i)
            page_key = f"books/{book_id}/pages/{i + 1}.png"
            upload_file(page_key, img_data, "image/png")

            run_async(
                db.pages.insert_one({
                    "bookId": book_id,
                    "pageNumber": i + 1,
                    "originalPageNumber": str(i + 1),
                    "imageKey": page_key,
                    "width": width,
                    "height": height,
                    "status": "PENDING",
                })
            )

        run_async(db.books.update_one({"_id": book_id}, {"$set": {"status": "READY"}}))
        return {"book_id": book_id, "pages": page_count}

    finally:
        client.close()
