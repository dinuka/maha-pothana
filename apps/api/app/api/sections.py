from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import random
from pydantic import BaseModel

from app.db.client import get_db
from app.schemas.section import NextSectionResponse
from app.schemas.translation import TranslationSubmit, TranslationResponse, MyTranslationResponse
from app.schemas.refs import BookRef, SectionRef, TranslatorRef, ApprovedByRef
from app.services.s3 import get_presigned_url
from app.services.translate import auto_translate, analyze_verse
from app.services.translation_activity import record_translation_activity
from app.api.deps import get_current_user
from app.tasks.recompute_book_stats import recompute_book_stats_task
from datetime import datetime, timezone


router = APIRouter()


async def _queue_stats_recompute_for_section(db: AsyncIOMotorDatabase, section_id: str) -> None:
    sec = await db.sections.find_one({"_id": ObjectId(section_id)})
    if not sec:
        return
    page = await db.pages.find_one({"_id": ObjectId(sec["page"]["id"])})
    if not page or not page.get("book"):
        return
    recompute_book_stats_task.delay(page["book"]["id"])


class ExactLetterUpdate(BaseModel):
    exactLetter: str


@router.get("/api/sections/next")
async def get_next_section(
    bookId: str | None = Query(None),
    language: str | None = Query(None),
    page_num: int | None = Query(None, alias="page"),
    status: str | None = Query(None),
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    pipeline = [
        {
            "$lookup": {
                "from": "translations",
                "let": {"section_id": "$_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$section.id", {"$toString": "$$section_id"}]}}},
                ],
                "as": "translations",
            }
        },
    ]

    # Apply status filter
    if status == "pending":
        pipeline.append({
            "$match": {
                "$expr": {
                    "$lt": [{"$size": "$translations"}, 1]
                }
            }
        })
    elif status == "translated":
        pipeline.append({
            "$match": {
                "$expr": {
                    "$and": [
                        {"$gt": [{"$size": "$translations"}, 0]},
                        {"$not": {"$anyElementTrue": {
                            "$map": {"input": "$translations", "as": "t", "in": "$$t.isApproved"}
                        }}}
                    ]
                }
            }
        })
    elif status == "approved":
        pipeline.append({
            "$match": {
                "$expr": {
                    "$anyElementTrue": {
                        "$map": {"input": "$translations", "as": "t", "in": "$$t.isApproved"}
                    }
                }
            }
        })
    else:
        # Default: sections with no translations
        pipeline.append({
            "$match": {
                "$expr": {
                    "$lt": [{"$size": "$translations"}, 1]
                }
            }
        })

    pipeline.append({"$sample": {"size": 1}})

    pipeline.extend([
        {
            "$lookup": {
                "from": "pages",
                "let": {"page_id": "$page.id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$_id", {"$toObjectId": "$$page_id"}]}}},
                ],
                "as": "page",
            }
        },
        {"$unwind": "$page"},
    ])

    # Apply book filter
    if bookId:
        pipeline.append({"$match": {"page.book.id": bookId}})

    # Apply page number filter
    if page_num is not None:
        pipeline.append({"$match": {"page.pageNumber": page_num}})

    pipeline.extend([
        {
            "$lookup": {
                "from": "books",
                "let": {"book_id": "$page.book.id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$_id", {"$toObjectId": "$$book_id"}]}}},
                ],
                "as": "book",
            }
        },
        {"$unwind": "$book"},
    ])

    # Apply language filter
    if language:
        pipeline.append({"$match": {"book.translateLanguages": language}})

    cursor = db.sections.aggregate(pipeline)
    sections = await cursor.to_list(length=1)

    if not sections:
        raise HTTPException(404, "No sections available")

    sec = sections[0]
    section_id = str(sec["_id"])
    page = sec["page"]
    book = sec["book"]

    cropped_url = None
    if sec.get("croppedImageKey"):
        cropped_url = await get_presigned_url(sec["croppedImageKey"])

    return NextSectionResponse(
        id=section_id,
        type=sec.get("type", "PARAGRAPH"),
        originalText=sec.get("originalText"),
        aiExtractedText=sec.get("aiExtractedText"),
        exactLetterTranslation=sec.get("exactLetterTranslation"),
        autoTranslatedText=sec.get("autoTranslatedText"),
        wordByWordMeaning=sec.get("wordByWordMeaning"),
        fullMeaning=sec.get("fullMeaning"),
        simplifiedMeaning=sec.get("simplifiedMeaning"),
        pageNumber=page.get("pageNumber", 0),
        bookTitle=book.get("title", ""),
        book=BookRef(id=str(book["_id"]), sourceLanguage=book.get("sourceLanguage")),
        croppedImageUrl=cropped_url,
    )


@router.get("/api/sections/{section_id}")
async def get_section(section_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    sec = await db.sections.find_one({"_id": ObjectId(section_id)})
    if not sec:
        raise HTTPException(404, "Section not found")

    cropped_url = None
    if sec.get("croppedImageKey"):
        cropped_url = await get_presigned_url(sec["croppedImageKey"])

    return {
        "id": str(sec["_id"]),
        "page": {"id": sec["page"]["id"]},
        "sectionOrder": sec["sectionOrder"],
        "type": sec.get("type", "PARAGRAPH"),
        "x": sec.get("x", 0),
        "y": sec.get("y", 0),
        "width": sec.get("width", 100),
        "height": sec.get("height", 50),
        "originalText": sec.get("originalText"),
        "exactLetterTranslation": sec.get("exactLetterTranslation"),
        "croppedImageUrl": cropped_url,
    }


@router.put("/api/sections/{section_id}/exact-letter")
async def update_exact_letter(
    section_id: str,
    body: ExactLetterUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    result = await db.sections.update_one(
        {"_id": ObjectId(section_id)},
        {"$set": {"exactLetterTranslation": body.exactLetter}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Section not found")
    return {"status": "saved"}


@router.post("/api/sections/{section_id}/auto-translate")
async def auto_translate_section(
    section_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    sec = await db.sections.find_one({"_id": ObjectId(section_id)})
    if not sec:
        raise HTTPException(404, "Section not found")

    source_text = sec.get("aiExtractedText") or sec.get("originalText")
    if not source_text:
        raise HTTPException(422, "No source text available. Run AI extraction or add text first.")

    book_id = None
    page = await db.pages.find_one({"_id": ObjectId(sec["page"]["id"])})
    if page and page.get("book"):
        book_id = page["book"].get("id")
    target_lang = "si"
    if book_id:
        book = await db.books.find_one({"_id": ObjectId(book_id)})
        if book:
            langs = book.get("translateLanguages", [])
            if langs:
                target_lang = langs[0]

    translated = await auto_translate(source_text, source_lang="auto", target_lang=target_lang)
    if translated is None:
        raise HTTPException(502, "Auto-translation service unavailable")

    await db.sections.update_one(
        {"_id": ObjectId(section_id)},
        {"$set": {"autoTranslatedText": translated}},
    )

    return {"translatedText": translated}


@router.post("/api/sections/{section_id}/analyze")
async def analyze_section(
    section_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    sec = await db.sections.find_one({"_id": ObjectId(section_id)})
    if not sec:
        raise HTTPException(404, "Section not found")

    source_text = sec.get("aiExtractedText") or sec.get("originalText")
    if not source_text:
        raise HTTPException(422, "No source text available. Run AI extraction or add text first.")

    book_id = None
    page = await db.pages.find_one({"_id": ObjectId(sec["page"]["id"])})
    if page and page.get("book"):
        book_id = page["book"].get("id")
    target_lang = "si"
    if book_id:
        book = await db.books.find_one({"_id": ObjectId(book_id)})
        if book:
            langs = book.get("translateLanguages", [])
            if langs:
                target_lang = langs[0]

    analysis = await analyze_verse(source_text, target_lang=target_lang)
    if analysis is None:
        raise HTTPException(502, "Verse analysis service unavailable")

    await db.sections.update_one(
        {"_id": ObjectId(section_id)},
        {
            "$set": {
                "wordByWordMeaning": analysis.wordByWordMeaning,
                "fullMeaning": analysis.fullMeaning,
                "simplifiedMeaning": analysis.simplifiedMeaning,
            }
        },
    )

    return {
        "wordByWordMeaning": analysis.wordByWordMeaning,
        "fullMeaning": analysis.fullMeaning,
        "simplifiedMeaning": analysis.simplifiedMeaning,
    }


@router.post("/api/sections/{section_id}/translate")
async def submit_translation(
    section_id: str,
    body: TranslationSubmit,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    sec = await db.sections.find_one({"_id": ObjectId(section_id)})
    if not sec:
        raise HTTPException(404, "Section not found")

    existing = await db.translations.find_one({
        "section.id": section_id,
        "translator.id": user_id,
    })

    if existing:
        translation_id = str(existing["_id"])
        await db.translations.update_one(
            {"_id": existing["_id"]},
            {
                "$set": {
                    "translatedText": body.translatedText,
                    "exactLetterTranslation": body.exactLetterTranslation,
                    "updatedAt": datetime.now(timezone.utc),
                }
            },
        )
    else:
        result = await db.translations.insert_one({
            "section": {"id": section_id},
            "translator": {"id": user_id},
            "translatedText": body.translatedText,
            "exactLetterTranslation": body.exactLetterTranslation,
            "isApproved": False,
            "approvedBy": None,
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc),
        })
        translation_id = str(result.inserted_id)

    await record_translation_activity(
        db,
        translation_id=translation_id,
        section_id=section_id,
        translator_id=user_id,
        translated_text=body.translatedText,
        action="SUBMITTED",
    )

    await _queue_stats_recompute_for_section(db, section_id)

    return {"status": "saved"}


@router.get("/api/sections/{section_id}/my-translation")
async def get_my_translation(
    section_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    trans = await db.translations.find_one({
        "section.id": section_id,
        "translator.id": user_id,
    })
    if not trans:
        raise HTTPException(404, "No translation found")

    return MyTranslationResponse(
        translatedText=trans["translatedText"],
        exactLetterTranslation=trans.get("exactLetterTranslation"),
        isApproved=trans.get("isApproved", False),
    )


@router.get("/api/sections/{section_id}/translations")
async def get_section_translations(section_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    cursor = db.translations.find({"section.id": section_id}).sort("createdAt", 1)
    translations = await cursor.to_list(length=100)

    result = []
    for t in translations:
        user = await db.users.find_one({"_id": ObjectId(t["translator"]["id"])})
        result.append(
            TranslationResponse(
                id=str(t["_id"]),
                section=SectionRef(id=t["section"]["id"]),
                translator=TranslatorRef(id=t["translator"]["id"]),
                translatorName=user.get("name") if user else None,
                translatedText=t["translatedText"],
                exactLetterTranslation=t.get("exactLetterTranslation"),
                isApproved=t.get("isApproved", False),
                approvedBy=ApprovedByRef(id=t["approvedBy"]["id"]) if t.get("approvedBy") else None,
                createdAt=t.get("createdAt"),
            )
        )
    return result


@router.post("/api/translations/{translation_id}/approve")
async def approve_translation(
    translation_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    translation = await db.translations.find_one({"_id": ObjectId(translation_id)})
    if not translation:
        raise HTTPException(404, "Translation not found")

    await db.translations.update_one(
        {"_id": ObjectId(translation_id)},
        {"$set": {"isApproved": True, "approvedBy": {"id": user_id}, "updatedAt": datetime.now(timezone.utc)}},
    )

    await record_translation_activity(
        db,
        translation_id=translation_id,
        section_id=translation["section"]["id"],
        translator_id=translation["translator"]["id"],
        translated_text=translation["translatedText"],
        action="APPROVED",
        performed_by=user_id,
    )

    await _queue_stats_recompute_for_section(db, translation["section"]["id"])

    return {"status": "approved"}


@router.post("/api/translations/{translation_id}/reject")
async def reject_translation(
    translation_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    translation = await db.translations.find_one({"_id": ObjectId(translation_id)})
    if not translation:
        raise HTTPException(404, "Translation not found")

    await db.translations.update_one(
        {"_id": ObjectId(translation_id)},
        {"$set": {"isApproved": False, "updatedAt": datetime.now(timezone.utc)}},
    )

    await record_translation_activity(
        db,
        translation_id=translation_id,
        section_id=translation["section"]["id"],
        translator_id=translation["translator"]["id"],
        translated_text=translation["translatedText"],
        action="REJECTED",
        performed_by=user_id,
    )

    await _queue_stats_recompute_for_section(db, translation["section"]["id"])

    return {"status": "rejected"}
