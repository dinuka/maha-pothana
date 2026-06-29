from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone

from app.db.client import get_db
from app.schemas.auth import GoogleAuthRequest, AuthResponse, AuthUserResponse, MeResponse
from app.config import settings
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/api/auth/google")
async def google_auth(body: GoogleAuthRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    existing = await db.users.find_one({"googleId": body.googleId})
    if existing:
        await db.users.update_one(
            {"_id": existing["_id"]},
            {"$set": {"updatedAt": datetime.now(timezone.utc)}},
        )
        user = existing
    else:
        new_user = {
            "googleId": body.googleId,
            "email": body.email,
            "name": body.name,
            "avatarUrl": body.avatarUrl,
            "roles": ["EDITOR", "TRANSLATOR"],
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc),
        }
        result = await db.users.insert_one(new_user)
        new_user["_id"] = result.inserted_id
        user = new_user

    return AuthResponse(
        user=AuthUserResponse(
            id=str(user["_id"]),
            name=user.get("name"),
            email=user.get("email"),
            image=user.get("avatarUrl"),
            roles=user.get("roles", []),
        ),
        token=settings.internal_api_key,
    )


@router.get("/api/auth/me")
async def get_me(
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    if not user_id:
        raise HTTPException(401, "Not authenticated")
    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(404, "User not found")
    return MeResponse(
        id=str(user["_id"]),
        googleId=user["googleId"],
        email=user["email"],
        name=user.get("name"),
        avatarUrl=user.get("avatarUrl"),
        roles=user.get("roles", []),
    )
