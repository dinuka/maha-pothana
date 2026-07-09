import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.db.client import get_db
from app.api.deps import get_current_user
from app.schemas.extraction import (
    ExtractResponse,
    ExtractionResultResponse,
    BatchExtractResponse,
    ExtractionStatusResponse,
    TransliterateResponse,
    TransliterationsResponse,
    TransliterationItem,
    SourceTextUpdate,
    ReverseTransliterateRequest,
    ReverseTransliterateResponse,
)
from app.services.ai_text import estimate_extraction_cost

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["extraction"])


@router.post("/sections/{section_id}/extract", status_code=202)
async def trigger_extraction(
    section_id: str,
    force: bool = Query(False),
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    logger.info("POST /sections/%s/extract - triggered by user %s (force=%s)", section_id, user_id, force)

    sec = await db.sections.find_one({"_id": ObjectId(section_id)})
    if not sec:
        logger.warning("POST /sections/%s/extract - section not found", section_id)
        raise HTTPException(404, "Section not found")

    if not sec.get("croppedImageKey"):
        logger.warning("POST /sections/%s/extract - no croppedImageKey", section_id)
        raise HTTPException(422, "Section has no cropped image. Crop sections first.")

    existing = await db.ai_text_extractions.find_one({"sectionId": section_id})
    logger.info("POST /sections/%s/extract - existing extraction: %s", section_id, existing)

    if not force and existing and existing.get("status") == "completed":
        logger.info("POST /sections/%s/extract - already completed, returning 409", section_id)
        return JSONResponse(
            status_code=409,
            content={
                "sectionId": section_id,
                "status": "completed",
                "extractedText": existing.get("extractedText"),
                "confidence": existing.get("confidence"),
            },
        )

    if force and existing:
        await db.ai_text_extractions.delete_many({"sectionId": section_id})

    from app.tasks.extract_section_text import extract_section_text

    logger.info("POST /sections/%s/extract - dispatching Celery task", section_id)
    task = extract_section_text.delay(section_id)
    logger.info("POST /sections/%s/extract - task dispatched, task_id=%s", section_id, task.id)

    return ExtractResponse(
        taskId=task.id,
        sectionId=section_id,
        status="queued",
    )


@router.post("/books/{book_id}/pages/{page_num}/extract", status_code=202)
async def trigger_page_extraction(
    book_id: str,
    page_num: int,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    page = await db.pages.find_one({
        "book.id": book_id,
        "pageNumber": page_num,
    })
    if not page:
        raise HTTPException(404, "Page not found")

    page_id = str(page["_id"])
    cursor = db.sections.find({"page.id": page_id})
    sections = await cursor.to_list(length=1000)

    if not sections:
        raise HTTPException(404, "No sections found on this page")

    sections_to_extract = [
        s for s in sections
        if s.get("croppedImageKey")
        and not (
            await db.ai_text_extractions.find_one({"sectionId": str(s["_id"]), "status": "completed"})
        )
    ]

    if not sections_to_extract:
        raise HTTPException(409, "All sections on this page already extracted")

    from app.tasks.extract_section_text import extract_section_text

    for sec in sections_to_extract:
        extract_section_text.delay(str(sec["_id"]))

    total = len(sections_to_extract)
    estimated_cost = estimate_extraction_cost(total)

    return BatchExtractResponse(
        taskId=f"page-{page_id}",
        bookId=book_id,
        totalSections=total,
        estimatedCost=estimated_cost,
        status="queued",
    )


@router.post("/books/{book_id}/extract", status_code=202)
async def trigger_book_extraction(
    book_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    book = await db.books.find_one({"_id": ObjectId(book_id)})
    if not book:
        raise HTTPException(404, "Book not found")

    existing_progress = await db.redis_progress.find_one({"bookId": book_id})
    if existing_progress and existing_progress.get("inProgress"):
        return {
            "bookId": book_id,
            "status": "in_progress",
            "completed": existing_progress.get("completed", 0),
            "total": existing_progress.get("total", 0),
            "failed": existing_progress.get("failed", 0),
        }

    cursor = db.sections.find({"page.book.id": book_id})
    all_sections = await cursor.to_list(length=10000)

    sections_to_extract = []
    for sec in all_sections:
        if not sec.get("croppedImageKey"):
            continue
        existing = await db.ai_text_extractions.find_one({
            "sectionId": str(sec["_id"]),
            "status": "completed",
        })
        if not existing:
            sections_to_extract.append(sec)

    if not sections_to_extract:
        raise HTTPException(409, "All sections already extracted")

    estimated_cost = estimate_extraction_cost(len(sections_to_extract))

    from app.tasks.extract_section_text import extract_section_text

    for sec in sections_to_extract:
        extract_section_text.delay(str(sec["_id"]))

    await db.redis_progress.insert_one({
        "bookId": book_id,
        "total": len(sections_to_extract),
        "completed": 0,
        "failed": 0,
        "inProgress": True,
        "createdAt": datetime.now(timezone.utc),
    })

    return BatchExtractResponse(
        taskId=f"book-{book_id}",
        bookId=book_id,
        totalSections=len(sections_to_extract),
        estimatedCost=estimated_cost,
        status="queued",
    )


@router.get("/sections/{section_id}/extraction")
async def get_extraction(
    section_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    logger.info("GET /sections/%s/extraction - looking up extraction", section_id)

    extraction = await db.ai_text_extractions.find_one({"sectionId": section_id})
    logger.info("GET /sections/%s/extraction - found: %s", section_id, extraction)

    if not extraction:
        logger.warning("GET /sections/%s/extraction - no extraction found (404)", section_id)
        raise HTTPException(404, "No extraction found for this section")

    if extraction.get("status") == "failed":
        logger.warning("GET /sections/%s/extraction - extraction failed, returning 404 for retry", section_id)
        raise HTTPException(404, "Extraction not yet available")

    return ExtractionResultResponse(
        sectionId=extraction["sectionId"],
        extractedText=extraction.get("extractedText", ""),
        confidence=extraction.get("confidence", 0.0),
        model=extraction.get("model", "gpt-4o"),
        processingTimeMs=extraction.get("processingTimeMs", 0),
        createdAt=extraction.get("createdAt", datetime.now(timezone.utc)),
    )


@router.post("/sections/{section_id}/transliterate")
async def transliterate_section(
    section_id: str,
    target_script: str = Query(..., min_length=1),
    force: bool = Query(False),
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    sec = await db.sections.find_one({"_id": ObjectId(section_id)})
    if not sec:
        raise HTTPException(404, "Section not found")

    source_text = sec.get("aiExtractedText") or sec.get("originalText")
    if not source_text:
        raise HTTPException(422, "No source text available. Run AI extraction first.")

    if not force:
        existing = await db.transliterations.find_one({
            "sectionId": section_id,
            "targetScript": target_script,
        })
        if existing:
            status = existing.get("status", "completed")
            if status == "pending":
                return {
                    "sectionId": section_id,
                    "status": "queued",
                    "taskId": None,
                    "message": "Transliteration already in progress",
                }
            return TransliterateResponse(
                sectionId=section_id,
                sourceText=source_text,
                transliteratedText=existing["transliteratedText"],
                sourceScript=existing.get("sourceScript", "unknown"),
                targetScript=existing["targetScript"],
                confidence=existing.get("confidence", 0.9),
                model=existing.get("model", "gpt-4o"),
                cached=True,
            )

    if force:
        await db.transliterations.delete_many({
            "sectionId": section_id,
            "targetScript": target_script,
        })

    await db.transliterations.update_one(
        {"sectionId": section_id, "targetScript": target_script},
        {"$set": {
            "sectionId": section_id,
            "targetScript": target_script,
            "status": "pending",
            "createdAt": datetime.now(timezone.utc),
        }},
        upsert=True,
    )

    from app.tasks.transliterate_section import transliterate_section as transliterate_task

    task = transliterate_task.delay(section_id, target_script)

    return {
        "sectionId": section_id,
        "status": "queued",
        "taskId": task.id,
    }


@router.get("/sections/{section_id}/transliterations")
async def get_transliterations(
    section_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    cursor = db.transliterations.find({"sectionId": section_id, "status": "completed"})
    items = await cursor.to_list(length=100)

    transliterations = [
        TransliterationItem(
            targetScript=t["targetScript"],
            transliteratedText=t["transliteratedText"],
            confidence=t.get("confidence", 0.9),
            model=t.get("model", "gpt-4o"),
            createdAt=t.get("createdAt", datetime.now(timezone.utc)),
        )
        for t in items
        if "transliteratedText" in t
    ]

    return TransliterationsResponse(
        sectionId=section_id,
        transliterations=transliterations,
    )


@router.put("/sections/{section_id}/source-text")
async def update_source_text(
    section_id: str,
    body: SourceTextUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    sec = await db.sections.find_one({"_id": ObjectId(section_id)})
    if not sec:
        raise HTTPException(404, "Section not found")

    if body.source == "ai":
        await db.sections.update_one(
            {"_id": ObjectId(section_id)},
            {"$set": {"aiExtractedText": body.text}},
        )
    elif body.source == "ocr":
        await db.sections.update_one(
            {"_id": ObjectId(section_id)},
            {"$set": {"originalText": body.text}},
        )
    else:
        raise HTTPException(422, "source must be 'ai' or 'ocr'")

    await db.transliterations.delete_many({"sectionId": section_id})

    return {
        "sectionId": section_id,
        "updatedText": body.text,
        "source": body.source,
    }


@router.get("/books/{book_id}/extraction/status")
async def get_extraction_status(
    book_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    cursor = db.sections.find({"page.book.id": book_id})
    all_sections = await cursor.to_list(length=10000)

    total = len(all_sections)
    extracted = 0
    pending = 0
    failed = 0

    for sec in all_sections:
        section_id = str(sec["_id"])
        ext = await db.ai_text_extractions.find_one({"sectionId": section_id})
        if ext:
            status = ext.get("status", "pending")
            if status == "completed":
                extracted += 1
            elif status == "failed":
                failed += 1
            else:
                pending += 1
        else:
            pending += 1

    progress = await db.redis_progress.find_one({"bookId": book_id})
    in_progress = progress.get("inProgress", False) if progress else False

    return ExtractionStatusResponse(
        bookId=book_id,
        totalSections=total,
        extracted=extracted,
        pending=pending,
        failed=failed,
        inProgress=in_progress,
    )


@router.post("/sections/{section_id}/reverse-transliterate")
async def reverse_transliterate(
    section_id: str,
    body: ReverseTransliterateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    from app.services.ai_text import reverse_transliterate_text

    logger.info("POST /sections/%s/reverse-transliterate - triggered by user %s", section_id, user_id)

    sec = await db.sections.find_one({"_id": ObjectId(section_id)})
    if not sec:
        raise HTTPException(404, "Section not found")

    try:
        result = await reverse_transliterate_text(
            transliterated_text=body.transliteratedText,
            source_script=body.sourceScript,
            target_script=body.targetScript,
            db=db,
        )

        source_text = result.transliterated_text

        await db.sections.update_one(
            {"_id": ObjectId(section_id)},
            {"$set": {"aiExtractedText": source_text}},
        )

        await db.transliterations.delete_many({"sectionId": section_id})

        return ReverseTransliterateResponse(
            sourceText=source_text,
            confidence=result.confidence,
            model=result.model,
        )
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        logger.error("reverse_transliterate failed for %s: %s", section_id, e)
        raise HTTPException(500, f"Reverse transliteration failed: {e}")
