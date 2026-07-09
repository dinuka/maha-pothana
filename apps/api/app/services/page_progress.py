from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.book import BookStatsSummary


async def get_books_stats_summary(
    db: AsyncIOMotorDatabase, book_ids: list[str]
) -> dict[str, BookStatsSummary]:
    """Return bookId -> BookStatsSummary for a batch of books in a single aggregation.

    Grouped by book (not looped per book) so list endpoints stay to one round trip
    regardless of how many books are being listed.
    """
    if not book_ids:
        return {}

    pipeline = [
        {"$lookup": {"from": "pages", "let": {"pid": "$page.id"}, "pipeline": [{"$match": {"$expr": {"$eq": ["$_id", {"$toObjectId": "$$pid"}]}}}], "as": "page"}},
        {"$unwind": "$page"},
        {"$match": {"page.book.id": {"$in": book_ids}}},
        {
            "$lookup": {
                "from": "translations",
                "let": {"section_id": {"$toString": "$_id"}},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$section.id", "$$section_id"]}}},
                ],
                "as": "translations",
            }
        },
        {
            "$addFields": {
                "hasApproved": {
                    "$anyElementTrue": {
                        "$map": {"input": "$translations", "as": "t", "in": "$$t.isApproved"}
                    }
                },
                "hasAnyTranslation": {"$gt": [{"$size": "$translations"}, 0]},
            }
        },
        {
            "$group": {
                "_id": "$page.book.id",
                "total": {"$sum": 1},
                "approved": {"$sum": {"$cond": ["$hasApproved", 1, 0]}},
                "inProgress": {
                    "$sum": {
                        "$cond": [
                            {"$and": ["$hasAnyTranslation", {"$not": "$hasApproved"}]},
                            1,
                            0,
                        ]
                    }
                },
                "pending": {"$sum": {"$cond": ["$hasAnyTranslation", 0, 1]}},
            }
        },
    ]

    rows = await db.sections.aggregate(pipeline).to_list(length=len(book_ids))
    summaries: dict[str, BookStatsSummary] = {}
    for row in rows:
        total = row["total"]
        approved = row["approved"]
        summaries[row["_id"]] = BookStatsSummary(
            totalSections=total,
            translatedSections=approved,
            inProgressSections=row["inProgress"],
            pendingSections=row["pending"],
            translationPercent=round(approved / total * 100, 1) if total > 0 else 0.0,
        )
    return summaries


async def count_section_translation_progress(
    db: AsyncIOMotorDatabase, page_ids: list[str]
) -> dict[str, tuple[int, int, int]]:
    """Return pageId -> (section_count, translated_count, approved_count).

    translated_count: sections with at least one submitted translation (reflects
    translator effort, used for IN_TRANSLATION/TRANSLATED progress display).
    approved_count: sections with at least one approved translation (used for the
    finalize gate — editor sign-off, independent of raw translation counts).
    """
    if not page_ids:
        return {}

    pipeline = [
        {"$match": {"page.id": {"$in": page_ids}}},
        {
            "$lookup": {
                "from": "translations",
                "let": {"section_id": {"$toString": "$_id"}},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$section.id", "$$section_id"]}}},
                ],
                "as": "translations",
            }
        },
        {
            "$group": {
                "_id": "$page.id",
                "sectionCount": {"$sum": 1},
                "translatedCount": {
                    "$sum": {"$cond": [{"$gt": [{"$size": "$translations"}, 0]}, 1, 0]}
                },
                "approvedCount": {
                    "$sum": {
                        "$cond": [
                            {
                                "$gt": [
                                    {
                                        "$size": {
                                            "$filter": {
                                                "input": "$translations",
                                                "cond": {"$eq": ["$$this.isApproved", True]},
                                            }
                                        }
                                    },
                                    0,
                                ]
                            },
                            1,
                            0,
                        ]
                    }
                },
            }
        },
    ]
    rows = await db.sections.aggregate(pipeline).to_list(length=len(page_ids))
    return {row["_id"]: (row["sectionCount"], row["translatedCount"], row["approvedCount"]) for row in rows}
