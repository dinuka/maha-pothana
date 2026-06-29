from pydantic import BaseModel
from datetime import datetime


class UserResponse(BaseModel):
    id: str
    googleId: str
    email: str
    name: str | None = None
    avatarUrl: str | None = None
    roles: list[str]
    createdAt: datetime | None = None


class RoleUpdate(BaseModel):
    roles: list[str]


class InviteRequest(BaseModel):
    email: str
