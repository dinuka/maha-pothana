from app.tasks.celery_app import celery_app
from app.config import settings
from app.services.s3 import get_s3, upload_file
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3)
def build_book(self, book_id: str):
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]

    try:
        book = run_async(db.books.find_one({"_id": book_id}))
        if not book:
            return {"error": "Book not found"}

        run_async(
            db.book_builds.insert_one({
                "bookId": book_id,
                "fileKey": None,
                "status": "BUILDING",
            })
        )

        run_async(db.books.update_one({"_id": book_id}, {"$set": {"status": "BUILDING"}}))

        # Placeholder: in production, compile translations into PDF
        finalized_key = f"books/{book_id}/finalized.pdf"
        placeholder_pdf = b"%PDF-1.4 placeholder finalized book content"
        upload_file(finalized_key, placeholder_pdf, "application/pdf")

        run_async(
            db.books.update_one({"_id": book_id}, {"$set": {"status": "COMPLETED"}})
        )
        run_async(
            db.book_builds.update_one(
                {"bookId": book_id, "status": "BUILDING"},
                {"$set": {"fileKey": finalized_key, "status": "COMPLETED"}},
            )
        )

        return {"book_id": book_id, "status": "COMPLETED"}

    except Exception as exc:
        run_async(
            db.books.update_one({"_id": book_id}, {"$set": {"status": "READY"}})
        )
        run_async(
            db.book_builds.update_one(
                {"bookId": book_id, "status": "BUILDING"},
                {"$set": {"status": "FAILED"}},
            )
        )
        raise exc

    finally:
        client.close()
