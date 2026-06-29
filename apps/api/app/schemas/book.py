from pydantic import BaseModel
from datetime import datetime


class BookCreate(BaseModel):
    title: str
    author: str
    sourceLanguage: str
    translateLanguages: list[str]
    description: str | None = None


class BookResponse(BaseModel):
    id: str
    title: str
    author: str
    sourceLanguage: str
    translateLanguages: list[str]
    description: str | None = None
    fileKey: str | None = None
    thumbnailKey: str | None = None
    translatorCount: int = 1
    ownerId: str
    status: str = "UPLOADING"
    createdAt: datetime | None = None
    updatedAt: datetime | None = None


class BookUpdate(BaseModel):
    title: str | None = None
    author: str | None = None
    description: str | None = None
    translatorCount: int | None = None


class BookListItem(BaseModel):
    id: str
    title: str
    author: str
    sourceLanguage: str
    translateLanguages: list[str]
    status: str
    thumbnailKey: str | None = None
    pageCount: int = 0
    translatedPercent: float = 0
