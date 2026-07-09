from app.tasks.celery_app import celery_app
from app.config import settings
from app.services.book_stats import recompute_book_stats
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import logging

logger = logging.getLogger(__name__)


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _recompute_book_stats(book_id: str):
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]

    try:
        await recompute_book_stats(db, book_id)
        logger.info("recompute_book_stats book_id=%s done", book_id)
    finally:
        client.close()


@celery_app.task(name="app.tasks.recompute_book_stats")
def recompute_book_stats_task(book_id: str):
    return run_async(_recompute_book_stats(book_id))
