"""One-shot backfill: reconstructs translation_activity records from the
existing mutable `translations` collection.

Run once after deploying the translation_activity feature, so History shows
activity that predates it. Rejections cannot be reconstructed (the old
reject_translation endpoint didn't record who rejected or when), so only
SUBMITTED and APPROVED records are backfilled.

Usage: python -m scripts.backfill_translation_activity
"""

import asyncio

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings


async def backfill() -> None:
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]

    inserted = 0
    skipped = 0

    async for t in db.translations.find({}):
        translation_id = str(t["_id"])

        existing = await db.translation_activity.find_one({"translationId": translation_id})
        if existing:
            skipped += 1
            continue

        section_id = t["section"]["id"]
        translator_id = t["translator"]["id"]

        sec = await db.sections.find_one({"_id": _to_object_id(section_id)})
        if not sec:
            skipped += 1
            continue
        pg = await db.pages.find_one({"_id": _to_object_id(sec["page"]["id"])})
        if not pg:
            skipped += 1
            continue

        translator_user = await db.users.find_one({"_id": _to_object_id(translator_id)})
        translator_name = translator_user.get("name", "Unknown") if translator_user else "Unknown"

        await db.translation_activity.insert_one({
            "translationId": translation_id,
            "sectionId": section_id,
            "bookId": pg["book"]["id"],
            "pageNumber": pg["pageNumber"],
            "sectionOrder": sec.get("sectionOrder", 0),
            "translatorId": translator_id,
            "translatorName": translator_name,
            "translatedText": t["translatedText"],
            "action": "SUBMITTED",
            "performedBy": None,
            "performedByName": None,
            "createdAt": t.get("createdAt"),
        })
        inserted += 1

        if t.get("isApproved") and t.get("approvedBy"):
            approver_id = t["approvedBy"]["id"]
            approver = await db.users.find_one({"_id": _to_object_id(approver_id)})
            approver_name = approver.get("name") if approver else None

            await db.translation_activity.insert_one({
                "translationId": translation_id,
                "sectionId": section_id,
                "bookId": pg["book"]["id"],
                "pageNumber": pg["pageNumber"],
                "sectionOrder": sec.get("sectionOrder", 0),
                "translatorId": translator_id,
                "translatorName": translator_name,
                "translatedText": t["translatedText"],
                "action": "APPROVED",
                "performedBy": approver_id,
                "performedByName": approver_name,
                "createdAt": t.get("updatedAt") or t.get("createdAt"),
            })
            inserted += 1

    print(f"Backfill complete. Inserted {inserted} activity records, skipped {skipped} translations.")
    client.close()


def _to_object_id(value: str):
    from bson import ObjectId
    return ObjectId(value)


if __name__ == "__main__":
    asyncio.run(backfill())
