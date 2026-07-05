from motor.motor_asyncio import AsyncIOMotorDatabase


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
