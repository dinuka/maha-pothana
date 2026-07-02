from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime, timezone

from app.db.client import get_db
from app.schemas.user import UserResponse, RoleUpdate, InviteRequest
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/api/users")
async def list_users(db: AsyncIOMotorDatabase = Depends(get_db)):
    cursor = db.users.find({}).sort("createdAt", -1)
    users = await cursor.to_list(length=1000)
    return [
        UserResponse(
            id=str(u["_id"]),
            googleId=u["googleId"],
            email=u["email"],
            name=u.get("name"),
            avatarUrl=u.get("avatarUrl"),
            roles=u.get("roles", []),
            createdAt=u.get("createdAt"),
        )
        for u in users
    ]


@router.put("/api/users/{user_id}/roles")
async def update_roles(user_id: str, body: RoleUpdate, db: AsyncIOMotorDatabase = Depends(get_db)):
    result = await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"roles": body.roles, "updatedAt": datetime.now(timezone.utc)}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "User not found")
    return {"ok": True}


@router.post("/api/books/{book_id}/invite")
async def invite_translator(
    book_id: str,
    body: InviteRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    book = await db.books.find_one({"_id": ObjectId(book_id)})
    if not book:
        raise HTTPException(404, "Book not found")

    target = await db.users.find_one({"email": body.email})
    if not target:
        raise HTTPException(404, "User not found")

    existing = await db.invitations.find_one({"book.id": book_id, "user.id": str(target["_id"])})
    if existing:
        raise HTTPException(409, "User already invited")

    await db.invitations.insert_one({
        "book": {"id": book_id},
        "user": {"id": str(target["_id"])},
        "invitedBy": {"id": user_id},
        "status": "PENDING",
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc),
    })

    return {"status": "PENDING"}


@router.post("/api/books/{book_id}/translators/{translator_id}/block")
async def block_translator(book_id: str, translator_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    result = await db.invitations.update_one(
        {"book.id": book_id, "user.id": translator_id},
        {"$set": {"status": "BLOCKED", "updatedAt": datetime.now(timezone.utc)}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Invitation not found")
    return {"status": "BLOCKED"}
