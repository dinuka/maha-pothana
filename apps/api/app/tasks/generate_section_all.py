import asyncio
import logging
import time
from datetime import datetime, timezone

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings
from app.tasks.celery_app import celery_app
from app.services.s3 import get_s3
from app.services.ai_text import extract_text, transliterate_text
from app.services.translate import analyze_verse

logger = logging.getLogger(__name__)


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _update_run(db, section_id: str, **fields):
    await db.generation_runs.update_one(
        {"sectionId": section_id},
        {"$set": {"sectionId": section_id, "updatedAt": datetime.now(timezone.utc), **fields}},
        upsert=True,
    )


async def _resolve_book_context(db, sec: dict) -> tuple[str | None, str, str]:
    book_id = None
    source_script = "unknown"
    target_lang = "si"
    page = await db.pages.find_one({"_id": ObjectId(sec["page"]["id"])})
    if page and page.get("book"):
        book_id = page["book"].get("id")
        book = await db.books.find_one({"_id": ObjectId(page["book"]["id"])})
        if book:
            source_script = book.get("sourceLanguage", "unknown")
            langs = book.get("translateLanguages", [])
            if langs:
                target_lang = langs[0]
    return book_id, source_script, target_lang


async def _run_extraction(db, section_id: str, sec: dict, force: bool) -> str | None:
    """Returns the source text, or None if extraction failed/unavailable."""
    existing_text = sec.get("aiExtractedText") or sec.get("originalText")
    if existing_text and not force:
        await _update_run(db, section_id, extractionStatus="completed")
        return existing_text

    cropped_key = sec.get("croppedImageKey")
    if not cropped_key:
        await _update_run(db, section_id, extractionStatus="failed", error="No cropped image")
        return None

    await _update_run(db, section_id, extractionStatus="processing")

    s3 = get_s3()
    try:
        obj = s3.get_object(settings.minio_bucket, cropped_key)
        image_data = obj.read()
    except Exception as e:
        logger.error("[generate_section_all] failed to download %s: %s", cropped_key, e)
        await _update_run(db, section_id, extractionStatus="failed", error=f"Failed to download image: {e}")
        return None

    try:
        result = await extract_text(image_data, db=db, section_id=section_id)
    except Exception as e:
        logger.error("[generate_section_all] extraction failed for %s: %s", section_id, e)
        await db.ai_text_extractions.update_one(
            {"sectionId": section_id},
            {"$set": {
                "sectionId": section_id,
                "extractedText": "",
                "confidence": 0.0,
                "model": "unknown",
                "processingTimeMs": 0,
                "status": "failed",
                "rawResponse": {"error": str(e)},
                "createdAt": datetime.now(timezone.utc),
                "updatedAt": datetime.now(timezone.utc),
            }},
            upsert=True,
        )
        await db.sections.update_one(
            {"_id": ObjectId(section_id)},
            {"$set": {"extractionStatus": "failed"}},
        )
        await _update_run(db, section_id, extractionStatus="failed", error=str(e))
        return None

    await db.ai_text_extractions.update_one(
        {"sectionId": section_id},
        {"$set": {
            "sectionId": section_id,
            "extractedText": result.text,
            "confidence": result.confidence,
            "model": result.model,
            "processingTimeMs": result.processing_time_ms,
            "status": "completed",
            "rawResponse": result.raw_response,
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc),
        }},
        upsert=True,
    )
    await db.sections.update_one(
        {"_id": ObjectId(section_id)},
        {"$set": {"aiExtractedText": result.text, "extractionStatus": "extracted"}},
    )
    await _update_run(db, section_id, extractionStatus="completed", aiExtractedText=result.text)
    return result.text


async def _run_transliteration(
    db, section_id: str, source_text: str, source_script: str, target_script: str, force: bool,
    book_id: str | None = None,
) -> str | None:
    if not force:
        cached = await db.transliterations.find_one({
            "sectionId": section_id,
            "targetScript": target_script,
            "status": "completed",
        })
        if cached:
            await _update_run(db, section_id, transliterationStatus="completed", transliteratedText=cached["transliteratedText"])
            return cached["transliteratedText"]

    await _update_run(db, section_id, transliterationStatus="processing")

    try:
        result = await transliterate_text(
            source_text=source_text,
            source_script=source_script,
            target_script=target_script,
            db=db,
            section_id=section_id,
            book_id=book_id,
        )
    except Exception as e:
        logger.error("[generate_section_all] transliteration failed for %s: %s", section_id, e)
        await db.transliterations.update_one(
            {"sectionId": section_id, "targetScript": target_script},
            {"$set": {"status": "failed", "error": str(e)}},
            upsert=True,
        )
        await _update_run(db, section_id, transliterationStatus="failed", error=str(e))
        return None

    await db.transliterations.update_one(
        {"sectionId": section_id, "targetScript": target_script},
        {"$set": {
            "sectionId": section_id,
            "sourceScript": result.source_script,
            "targetScript": result.target_script,
            "transliteratedText": result.transliterated_text,
            "confidence": result.confidence,
            "model": result.model,
            "status": "completed",
            "rawResponse": result.raw_response,
            "createdAt": datetime.now(timezone.utc),
        }},
        upsert=True,
    )
    await _update_run(db, section_id, transliterationStatus="completed", transliteratedText=result.transliterated_text)
    return result.transliterated_text


async def _run_analysis(
    db, section_id: str, sec: dict, source_text: str, target_lang: str, force: bool,
    book_id: str | None = None,
) -> None:
    if not force and sec.get("wordByWordMeaning"):
        await _update_run(
            db, section_id,
            analysisStatus="completed",
            wordByWordMeaning=sec.get("wordByWordMeaning"),
            fullMeaning=sec.get("fullMeaning"),
            simplifiedMeaning=sec.get("simplifiedMeaning"),
        )
        return

    await _update_run(db, section_id, analysisStatus="processing")

    analysis = await analyze_verse(
        source_text, target_lang=target_lang, db=db, section_id=section_id, book_id=book_id,
    )
    if analysis is None:
        await _update_run(db, section_id, analysisStatus="failed", error="Verse analysis service unavailable")
        return

    await db.sections.update_one(
        {"_id": ObjectId(section_id)},
        {"$set": {
            "wordByWordMeaning": analysis.wordByWordMeaning,
            "fullMeaning": analysis.fullMeaning,
            "simplifiedMeaning": analysis.simplifiedMeaning,
        }},
    )
    await _update_run(
        db, section_id,
        analysisStatus="completed",
        wordByWordMeaning=analysis.wordByWordMeaning,
        fullMeaning=analysis.fullMeaning,
        simplifiedMeaning=analysis.simplifiedMeaning,
    )


async def _generate_section_all(section_id: str, target_script: str, force: bool):
    logger.info("[generate_section_all] START section_id=%s target_script=%s force=%s", section_id, target_script, force)

    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]

    try:
        sec = await db.sections.find_one({"_id": ObjectId(section_id)})
        if not sec:
            await _update_run(db, section_id, status="failed", error="Section not found")
            return {"error": "Section not found"}

        await _update_run(db, section_id, status="processing")
        start_time = time.monotonic()

        source_text = await _run_extraction(db, section_id, sec, force)
        if not source_text:
            await _update_run(db, section_id, status="failed")
            return {"error": "Extraction failed; cannot continue"}

        book_id, source_script, target_lang = await _resolve_book_context(db, sec)

        transliterated_text = await _run_transliteration(
            db, section_id, source_text, source_script, target_script, force, book_id=book_id
        )

        sec_after_extraction = await db.sections.find_one({"_id": ObjectId(section_id)})
        await _run_analysis(
            db, section_id, sec_after_extraction or sec, source_text, target_lang, force, book_id=book_id
        )

        run = await db.generation_runs.find_one({"sectionId": section_id})
        statuses = [
            (run or {}).get("extractionStatus"),
            (run or {}).get("transliterationStatus"),
            (run or {}).get("analysisStatus"),
        ]
        if all(s == "completed" for s in statuses):
            overall = "completed"
        elif any(s == "completed" for s in statuses):
            overall = "partial"
        else:
            overall = "failed"

        await _update_run(db, section_id, status=overall)

        elapsed = int((time.monotonic() - start_time) * 1000)
        logger.info("[generate_section_all] DONE section_id=%s status=%s time=%dms", section_id, overall, elapsed)

        return {
            "section_id": section_id,
            "status": overall,
            "extractedText": source_text,
            "transliteratedText": transliterated_text,
        }

    finally:
        client.close()


@celery_app.task(bind=True, max_retries=3)
def generate_section_all(self, section_id: str, target_script: str, force: bool = False):
    logger.info("[generate_section_all] TASK STARTED section_id=%s task_id=%s", section_id, self.request.id)
    try:
        result = run_async(_generate_section_all(section_id, target_script, force))
        logger.info("[generate_section_all] TASK COMPLETED section_id=%s result=%s", section_id, result)
        return result
    except Exception as e:
        logger.error("[generate_section_all] TASK FAILED section_id=%s: %s", section_id, e, exc_info=True)
        raise
