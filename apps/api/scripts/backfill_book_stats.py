"""One-shot backfill: populates the book_stats collection for existing books.

Run once after deploying the materialized stats feature, so /api/books,
/api/books/available, and the per-book stats endpoints read real numbers
instead of empty defaults for books that predate this collection.

Usage: python -m scripts.backfill_book_stats
"""

import asyncio

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings
from app.services.book_stats import recompute_book_stats


async def backfill() -> None:
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]

    done = 0

    async for book in db.books.find({}):
        book_id = str(book["_id"])
        await recompute_book_stats(db, book_id)
        done += 1

    print(f"backfill_book_stats: recomputed {done} book(s)")
    client.close()


if __name__ == "__main__":
    asyncio.run(backfill())
