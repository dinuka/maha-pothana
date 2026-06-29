from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import random

from app.db.client import get_db
from app.schemas.section import NextSectionResponse
from app.schemas.translation import TranslationSubmit, TranslationResponse, MyTranslationResponse
from app.services.s3 import get_presigned_url
from app.services.translate import auto_translate
from app.api.deps import get_current_user
from datetime import datetime, timezone

router = APIRouter()


@router.get("/api/sections/next")
async def get_next_section(
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    pipeline = [
        {
            "$lookup": {
                "from": "translations",
                "let": {"section_id": "$_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$sectionId", {"$toString": "$$section_id"}]}}},
                ],
                "as": "translations",
            }
        },
        {
            "$match": {
                "$expr": {
                    "$lt": [
                        {"$size": "$translations"},
                        1,
                    ]
                }
            }
        },
        {"$sample": {"size": 1}},
        {
            "$lookup": {
                "from": "pages",
                "localField": "pageId",
                "foreignField": "_id",
                "as": "page",
            }
        },
        {"$unwind": "$page"},
        {
            "$lookup": {
                "from": "books",
                "localField": "page.bookId",
                "foreignField": "_id",
                "as": "book",
            }
        },
        {"$unwind": "$book"},
    ]

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
        autoTranslatedText=sec.get("autoTranslatedText"),
        pageNumber=page.get("pageNumber", 0),
        bookTitle=book.get("title", ""),
        bookId=str(book["_id"]),
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
        "pageId": sec["pageId"],
        "sectionOrder": sec["sectionOrder"],
        "type": sec.get("type", "PARAGRAPH"),
        "x": sec.get("x", 0),
        "y": sec.get("y", 0),
        "width": sec.get("width", 100),
        "height": sec.get("height", 50),
        "originalText": sec.get("originalText"),
        "croppedImageUrl": cropped_url,
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
        "sectionId": section_id,
        "translatorId": user_id,
    })

    if existing:
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
        await db.translations.insert_one({
            "sectionId": section_id,
            "translatorId": user_id,
            "translatedText": body.translatedText,
            "exactLetterTranslation": body.exactLetterTranslation,
            "isApproved": False,
            "approvedBy": None,
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc),
        })

    return {"status": "saved"}


@router.get("/api/sections/{section_id}/my-translation")
async def get_my_translation(
    section_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    trans = await db.translations.find_one({
        "sectionId": section_id,
        "translatorId": user_id,
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
    cursor = db.translations.find({"sectionId": section_id}).sort("createdAt", 1)
    translations = await cursor.to_list(length=100)

    result = []
    for t in translations:
        user = await db.users.find_one({"_id": ObjectId(t["translatorId"])})
        result.append(
            TranslationResponse(
                id=str(t["_id"]),
                sectionId=t["sectionId"],
                translatorId=t["translatorId"],
                translatorName=user.get("name") if user else None,
                translatedText=t["translatedText"],
                exactLetterTranslation=t.get("exactLetterTranslation"),
                isApproved=t.get("isApproved", False),
                approvedBy=t.get("approvedBy"),
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
    result = await db.translations.update_one(
        {"_id": ObjectId(translation_id)},
        {"$set": {"isApproved": True, "approvedBy": user_id, "updatedAt": datetime.now(timezone.utc)}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Translation not found")
    return {"status": "approved"}


@router.post("/api/translations/{translation_id}/reject")
async def reject_translation(translation_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    result = await db.translations.update_one(
        {"_id": ObjectId(translation_id)},
        {"$set": {"isApproved": False, "updatedAt": datetime.now(timezone.utc)}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Translation not found")
    return {"status": "rejected"}
