from pydantic import BaseModel, EmailStr


class GoogleAuthRequest(BaseModel):
    googleId: str
    email: str
    name: str | None = None
    avatarUrl: str | None = None


class AuthUserResponse(BaseModel):
    id: str
    name: str | None = None
    email: str | None = None
    image: str | None = None
    roles: list[str]


class AuthResponse(BaseModel):
    user: AuthUserResponse
    token: str


class MeResponse(BaseModel):
    id: str
    googleId: str
    email: str
    name: str | None = None
    avatarUrl: str | None = None
    roles: list[str]
