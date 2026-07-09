from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime, timezone

from app.db.client import get_db
from app.schemas.draft import DraftCreate, DraftResponse
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/api/translations/draft")
async def upsert_draft(
    body: DraftCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)

    existing = await db.translation_drafts.find_one({
        "sectionId": body.sectionId,
        "translatorId": user_id,
    })

    if existing:
        await db.translation_drafts.update_one(
            {"_id": existing["_id"]},
            {"$set": {"translatedText": body.translatedText, "updatedAt": now}},
        )
        draft_id = str(existing["_id"])
    else:
        result = await db.translation_drafts.insert_one({
            "sectionId": body.sectionId,
            "translatorId": user_id,
            "translatedText": body.translatedText,
            "createdAt": now,
            "updatedAt": now,
        })
        draft_id = str(result.inserted_id)

    return DraftResponse(
        draftId=draft_id,
        translatedText=body.translatedText,
        updatedAt=now,
    )


@router.get("/api/translations/draft")
async def get_draft(
    sectionId: str = Query(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    draft = await db.translation_drafts.find_one({
        "sectionId": sectionId,
        "translatorId": user_id,
    })

    if not draft:
        raise HTTPException(404, "No draft found")

    return DraftResponse(
        draftId=str(draft["_id"]),
        translatedText=draft["translatedText"],
        updatedAt=draft.get("updatedAt", draft.get("createdAt")),
    )


@router.delete("/api/translations/draft/{draft_id}")
async def delete_draft(
    draft_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    result = await db.translation_drafts.delete_one({
        "_id": ObjectId(draft_id),
        "translatorId": user_id,
    })

    if result.deleted_count == 0:
        raise HTTPException(404, "Draft not found")

    return {"status": "deleted"}
