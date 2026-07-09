from datetime import datetime, timezone
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.book import BookStatsSummary
from app.schemas.stats import LanguageStats, PageStats, TranslationStatsResponse, TranslatorStatsResponse


async def _compute_translation_stats(db: AsyncIOMotorDatabase, book_id: str) -> TranslationStatsResponse:
    """Recompute a book's translation stats from sections/translations via join aggregation.

    This is the single source of truth for section-status counting (approved = at least
    one approved translation). Called only on write (see recompute_book_stats), never on
    read, so read paths hit the materialized book_stats collection instead of re-joining.
    """
    total_pipeline = [
        {"$lookup": {"from": "pages", "let": {"pid": "$page.id"}, "pipeline": [{"$match": {"$expr": {"$eq": ["$_id", {"$toObjectId": "$$pid"}]}}}], "as": "page"}},
        {"$unwind": "$page"},
        {"$match": {"page.book.id": book_id}},
        {"$count": "total"},
    ]
    total_result = await db.sections.aggregate(total_pipeline).to_list(1)
    total_sections = total_result[0]["total"] if total_result else 0

    stats_pipeline = [
        {"$lookup": {"from": "pages", "let": {"pid": "$page.id"}, "pipeline": [{"$match": {"$expr": {"$eq": ["$_id", {"$toObjectId": "$$pid"}]}}}], "as": "page"}},
        {"$unwind": "$page"},
        {"$match": {"page.book.id": book_id}},
        {"$lookup": {
            "from": "translations",
            "let": {"sid": {"$toString": "$_id"}},
            "pipeline": [
                {"$match": {"$expr": {"$eq": ["$section.id", "$$sid"]}}},
            ],
            "as": "translations",
        }},
        {"$addFields": {
            "hasApproved": {
                "$anyElementTrue": {
                    "$map": {"input": "$translations", "as": "t", "in": "$$t.isApproved"}
                }
            },
            "hasAnyTranslation": {"$gt": [{"$size": "$translations"}, 0]},
        }},
        {"$addFields": {
            "status": {
                "$cond": [
                    "$hasApproved",
                    "approved",
                    {"$cond": ["$hasAnyTranslation", "in_progress", "pending"]},
                ]
            }
        }},
        {"$group": {
            "_id": None,
            "total": {"$sum": 1},
            "translated": {"$sum": {"$cond": [{"$eq": ["$status", "approved"]}, 1, 0]}},
            "inProgress": {"$sum": {"$cond": [{"$eq": ["$status", "in_progress"]}, 1, 0]}},
            "pending": {"$sum": {"$cond": [{"$eq": ["$status", "pending"]}, 1, 0]}},
        }},
    ]

    stats_result = await db.sections.aggregate(stats_pipeline).to_list(1)

    if stats_result:
        translated = stats_result[0]["translated"]
        in_progress = stats_result[0]["inProgress"]
        pending = stats_result[0]["pending"]
        total = stats_result[0]["total"]
    else:
        translated = 0
        in_progress = 0
        pending = 0
        total = 0

    percent = (translated / total * 100) if total > 0 else 0.0

    book = await db.books.find_one({"_id": ObjectId(book_id)})
    translate_languages = book.get("translateLanguages", []) if book else []

    by_language: dict[str, LanguageStats] = {}
    for lang in translate_languages:
        lang_pipeline = [
            {"$lookup": {"from": "pages", "let": {"pid": "$page.id"}, "pipeline": [{"$match": {"$expr": {"$eq": ["$_id", {"$toObjectId": "$$pid"}]}}}], "as": "page"}},
            {"$unwind": "$page"},
            {"$match": {"page.book.id": book_id}},
            {"$lookup": {
                "from": "translations",
                "let": {"sid": {"$toString": "$_id"}},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$section.id", "$$sid"]}}},
                ],
                "as": "translations",
            }},
            {"$addFields": {
                "langApproved": {
                    "$anyElementTrue": {
                        "$map": {"input": "$translations", "as": "t", "in": "$$t.isApproved"}
                    }
                },
            }},
            {"$group": {
                "_id": None,
                "total": {"$sum": 1},
                "translated": {"$sum": {"$cond": ["$langApproved", 1, 0]}},
            }},
        ]
        lang_result = await db.sections.aggregate(lang_pipeline).to_list(1)
        if lang_result:
            lang_total = lang_result[0]["total"]
            lang_translated = lang_result[0]["translated"]
            by_language[lang] = LanguageStats(
                total=lang_total,
                translated=lang_translated,
                percent=round(lang_translated / lang_total * 100, 1) if lang_total > 0 else 0.0,
            )

    page_pipeline = [
        {"$lookup": {"from": "pages", "let": {"pid": "$page.id"}, "pipeline": [{"$match": {"$expr": {"$eq": ["$_id", {"$toObjectId": "$$pid"}]}}}], "as": "page"}},
        {"$unwind": "$page"},
        {"$match": {"page.book.id": book_id}},
        {"$lookup": {
            "from": "translations",
            "let": {"sid": {"$toString": "$_id"}},
            "pipeline": [
                {"$match": {"$expr": {"$eq": ["$section.id", "$$sid"]}}},
            ],
            "as": "translations",
        }},
        {"$addFields": {
            "hasApproved": {
                "$anyElementTrue": {
                    "$map": {"input": "$translations", "as": "t", "in": "$$t.isApproved"}
                }
            },
        }},
        {"$group": {
            "_id": {"pageNumber": "$page.pageNumber"},
            "total": {"$sum": 1},
            "translated": {"$sum": {"$cond": ["$hasApproved", 1, 0]}},
        }},
        {"$sort": {"_id.pageNumber": 1}},
    ]

    page_results = await db.sections.aggregate(page_pipeline).to_list(1000)
    by_page = []
    for pr in page_results:
        p_num = pr["_id"]["pageNumber"]
        p_total = pr["total"]
        p_translated = pr["translated"]
        by_page.append(PageStats(
            pageNumber=p_num,
            total=p_total,
            translated=p_translated,
            percent=round(p_translated / p_total * 100, 1) if p_total > 0 else 0.0,
        ))

    return TranslationStatsResponse(
        totalSections=total,
        translatedSections=translated,
        pendingSections=pending,
        inProgressSections=in_progress,
        translationPercent=round(percent, 1),
        byLanguage=by_language,
        byPage=by_page,
    )


async def _compute_translator_stats(db: AsyncIOMotorDatabase, book_id: str) -> list[TranslatorStatsResponse]:
    pipeline = [
        {
            "$lookup": {
                "from": "sections",
                "let": {"sid": "$section.id"},
                "pipeline": [{"$match": {"$expr": {"$eq": ["$_id", {"$toObjectId": "$$sid"}]}}}],
                "as": "sec",
            }
        },
        {"$unwind": "$sec"},
        {
            "$lookup": {
                "from": "pages",
                "let": {"pid": "$sec.page.id"},
                "pipeline": [{"$match": {"$expr": {"$eq": ["$_id", {"$toObjectId": "$$pid"}]}}}],
                "as": "page",
            }
        },
        {"$unwind": "$page"},
        {"$match": {"page.book.id": book_id}},
        {
            "$lookup": {
                "from": "translation_activity",
                "let": {"tid": {"$toString": "$_id"}},
                "pipeline": [
                    {"$match": {"$expr": {"$and": [{"$eq": ["$translationId", "$$tid"]}, {"$eq": ["$action", "REJECTED"]}]}}},
                ],
                "as": "rejectionActivity",
            }
        },
        {"$addFields": {
            "isRejected": {"$gt": [{"$size": "$rejectionActivity"}, 0]},
        }},
        {"$group": {
            "_id": "$translator.id",
            "translations": {"$push": "$$ROOT"},
            "totalAssigned": {"$sum": 1},
            "approvedCount": {"$sum": {"$cond": ["$isApproved", 1, 0]}},
            "rejectedCount": {"$sum": {"$cond": ["$isRejected", 1, 0]}},
            "lastActiveAt": {"$max": "$createdAt"},
        }},
    ]

    results = await db.translations.aggregate(pipeline).to_list(1000)

    translator_stats = []
    for r in results:
        translator_id = r["_id"]
        user = await db.users.find_one({"_id": ObjectId(translator_id)})
        user_name = user.get("name", "Unknown") if user else "Unknown"

        approved = r["approvedCount"]
        rejected = r["rejectedCount"]
        total = r["totalAssigned"]
        pending = total - approved - rejected

        approval_rate = round(approved / total * 100, 1) if total > 0 else None

        translations = r.get("translations", [])
        turnaround_hours = None
        approved_translations = [t for t in translations if t.get("isApproved")]
        if approved_translations:
            total_hours = 0
            for t in approved_translations:
                created = t.get("createdAt")
                if created:
                    section_created = t.get("sec", {}).get("createdAt")
                    if section_created:
                        delta = created - section_created
                        total_hours += delta.total_seconds() / 3600
            turnaround_hours = round(total_hours / len(approved_translations), 1) if approved_translations else None

        last_active = r.get("lastActiveAt")
        last_active_str = last_active.isoformat() if last_active else None

        translator_stats.append(TranslatorStatsResponse(
            userId=translator_id,
            userName=user_name,
            totalAssigned=total,
            approvedCount=approved,
            rejectedCount=rejected,
            pendingCount=pending,
            approvalRate=approval_rate,
            avgTurnaroundHours=turnaround_hours,
            lastActiveAt=last_active_str,
        ))

    translator_stats.sort(key=lambda x: (x.approvalRate is not None, x.approvalRate or 0), reverse=True)
    return translator_stats


async def recompute_book_stats(db: AsyncIOMotorDatabase, book_id: str) -> None:
    """Recompute and upsert the book_stats document for one book.

    Recompute-on-write, not incremental counters: translatedSections counts sections
    with >=1 approved translation, so a second approval on an already-approved section
    must not increment. Detecting that 0->1 crossing requires reading the section's
    translation state regardless, so recomputing the whole book from source is simpler
    and correct by construction rather than tracking per-section deltas.
    """
    stats = await _compute_translation_stats(db, book_id)
    translator_stats = await _compute_translator_stats(db, book_id)

    await db.book_stats.update_one(
        {"bookId": book_id},
        {
            "$set": {
                "bookId": book_id,
                "stats": stats.model_dump(),
                "translatorStats": [t.model_dump() for t in translator_stats],
                "updatedAt": datetime.now(timezone.utc),
            }
        },
        upsert=True,
    )


async def get_book_stats_doc(db: AsyncIOMotorDatabase, book_id: str) -> TranslationStatsResponse:
    doc = await db.book_stats.find_one({"bookId": book_id})
    if not doc:
        return TranslationStatsResponse(
            totalSections=0,
            translatedSections=0,
            pendingSections=0,
            inProgressSections=0,
            translationPercent=0,
            byLanguage={},
            byPage=[],
        )
    return TranslationStatsResponse.model_validate(doc["stats"])


async def get_translator_stats_doc(db: AsyncIOMotorDatabase, book_id: str) -> list[TranslatorStatsResponse]:
    doc = await db.book_stats.find_one({"bookId": book_id})
    if not doc:
        return []
    return [TranslatorStatsResponse.model_validate(t) for t in doc.get("translatorStats", [])]


async def get_books_stats_summary_doc(
    db: AsyncIOMotorDatabase, book_ids: list[str]
) -> dict[str, BookStatsSummary]:
    """Batched read of BookStatsSummary from book_stats for list endpoints."""
    if not book_ids:
        return {}

    cursor = db.book_stats.find({"bookId": {"$in": book_ids}})
    docs = await cursor.to_list(length=len(book_ids))

    summaries: dict[str, BookStatsSummary] = {}
    for doc in docs:
        s = doc["stats"]
        summaries[doc["bookId"]] = BookStatsSummary(
            totalSections=s["totalSections"],
            translatedSections=s["translatedSections"],
            inProgressSections=s["inProgressSections"],
            pendingSections=s["pendingSections"],
            translationPercent=s["translationPercent"],
        )
    return summaries
