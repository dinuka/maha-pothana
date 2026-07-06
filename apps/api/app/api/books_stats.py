from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import json
import logging

from app.db.client import get_db
from app.schemas.stats import TranslationStatsResponse, LanguageStats, PageStats, TranslatorStatsResponse
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

STATS_CACHE_TTL = 30


async def _get_stats_from_db(db: AsyncIOMotorDatabase, book_id: str) -> TranslationStatsResponse:
    # Count total sections for this book
    total_pipeline = [
        {"$lookup": {"from": "pages", "localField": "page.id", "foreignField": "_id", "as": "page"}},
        {"$unwind": "$page"},
        {"$match": {"page.book.id": book_id}},
        {"$count": "total"},
    ]
    total_result = await db.sections.aggregate(total_pipeline).to_list(1)
    total_sections = total_result[0]["total"] if total_result else 0

    # Aggregate sections with translation status
    stats_pipeline = [
        {"$lookup": {"from": "pages", "localField": "page.id", "foreignField": "_id", "as": "page"}},
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

    # Per-language breakdown
    book = await db.books.find_one({"_id": ObjectId(book_id)})
    translate_languages = book.get("translateLanguages", []) if book else []

    by_language: dict[str, LanguageStats] = {}
    if translate_languages:
        for lang in translate_languages:
            lang_pipeline = [
                {"$lookup": {"from": "pages", "localField": "page.id", "foreignField": "_id", "as": "page"}},
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

    # Per-page breakdown
    page_pipeline = [
        {"$lookup": {"from": "pages", "localField": "page.id", "foreignField": "_id", "as": "page"}},
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


@router.get("/api/books/{book_id}/stats")
async def get_book_stats(
    book_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    # Verify book exists
    book = await db.books.find_one({"_id": ObjectId(book_id)})
    if not book:
        raise HTTPException(404, "Book not found")

    # Check Redis cache
    cache_key = f"stats:book:{book_id}"
    try:
        from app.db.client import client as mongo_client
        # We'll try to use redis if available
        import redis.asyncio as aioredis
        r = aioredis.from_url("redis://localhost:6379/0")
        cached = await r.get(cache_key)
        if cached:
            return TranslationStatsResponse.model_validate_json(cached)
    except Exception:
        pass

    stats = await _get_stats_from_db(db, book_id)

    # Try to cache
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url("redis://localhost:6379/0")
        await r.setex(cache_key, STATS_CACHE_TTL, stats.model_dump_json())
    except Exception:
        pass

    return stats


@router.get("/api/books/{book_id}/translators/stats")
async def get_translator_stats(
    book_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    book = await db.books.find_one({"_id": ObjectId(book_id)})
    if not book:
        raise HTTPException(404, "Book not found")

    cache_key = f"translators:stats:book:{book_id}"
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url("redis://localhost:6379/0")
        cached = await r.get(cache_key)
        if cached:
            import json
            return [TranslatorStatsResponse.model_validate(item) for item in json.loads(cached)]
    except Exception:
        pass

    # Find all translations for sections in this book
    pipeline = [
        {"$lookup": {"from": "sections", "localField": "section.id", "foreignField": "_id", "as": "sec"}},
        {"$unwind": "$sec"},
        {"$lookup": {"from": "pages", "localField": "sec.page.id", "foreignField": "_id", "as": "page"}},
        {"$unwind": "$page"},
        {"$match": {"page.book.id": book_id}},
        {"$group": {
            "_id": "$translator.id",
            "translations": {"$push": "$$ROOT"},
            "totalAssigned": {"$sum": 1},
            "approvedCount": {"$sum": {"$cond": ["$isApproved", 1, 0]}},
            "rejectedCount": {"$sum": {"$cond": [{"$and": [{"$not": "$isApproved"}, {"$gt": [{"$size": "$translations"}, 0]}]}, 1, 0]}},
            "pendingCount": {"$sum": {"$cond": [{"$and": [{"$not": "$isApproved"}, {"$eq": [{"$size": "$translations"}, 0]}]}, 1, 0]}},
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

        if approved + rejected > 0:
            approval_rate = round(approved / (approved + rejected) * 100, 1)
        else:
            approval_rate = None

        # Calculate avg turnaround
        translations = r.get("translations", [])
        turnaround_hours = None
        approved_translations = [t for t in translations if t.get("isApproved")]
        if approved_translations:
            total_hours = 0
            for t in approved_translations:
                created = t.get("createdAt")
                if created:
                    # Use section created_at as proxy for turnaround
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
            pendingCount=total - approved - rejected,
            approvalRate=approval_rate,
            avgTurnaroundHours=turnaround_hours,
            lastActiveAt=last_active_str,
        ))

    # Sort by approval rate descending (None at end)
    translator_stats.sort(key=lambda x: (x.approvalRate is not None, x.approvalRate or 0), reverse=True)

    # Cache
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url("redis://localhost:6379/0")
        await r.setex(cache_key, STATS_CACHE_TTL, json.dumps([s.model_dump() for s in translator_stats]))
    except Exception:
        pass

    return translator_stats
