from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime, timezone


async def record_translation_activity(
    db: AsyncIOMotorDatabase,
    *,
    translation_id: str,
    section_id: str,
    translator_id: str,
    translated_text: str,
    action: str,
    performed_by: str | None = None,
) -> None:
    sec = await db.sections.find_one({"_id": ObjectId(section_id)})
    if not sec:
        return
    pg = await db.pages.find_one({"_id": ObjectId(sec["page"]["id"])})
    if not pg:
        return

    translator_user = await db.users.find_one({"_id": ObjectId(translator_id)})
    performer_user = (
        await db.users.find_one({"_id": ObjectId(performed_by)}) if performed_by else None
    )

    await db.translation_activity.insert_one({
        "translationId": translation_id,
        "sectionId": section_id,
        "bookId": pg["book"]["id"],
        "pageNumber": pg["pageNumber"],
        "sectionOrder": sec.get("sectionOrder", 0),
        "translatorId": translator_id,
        "translatorName": translator_user.get("name", "Unknown") if translator_user else "Unknown",
        "translatedText": translated_text,
        "action": action,
        "performedBy": performed_by,
        "performedByName": performer_user.get("name") if performer_user else None,
        "createdAt": datetime.now(timezone.utc),
    })
