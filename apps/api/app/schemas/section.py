from __future__ import annotations

from pydantic import BaseModel
from datetime import datetime

from app.schemas.refs import PageRef, BookRef


class SectionResponse(BaseModel):
    id: str
    page: PageRef
    sectionOrder: int
    type: str = "PARAGRAPH"
    x: float = 0
    y: float = 0
    width: float = 100
    height: float = 50
    originalText: str | None = None
    aiExtractedText: str | None = None
    exactLetterTranslation: str | None = None
    croppedImageKey: str | None = None
    extractionStatus: str | None = None
    createdAt: datetime | None = None


class SectionUpdateItem(BaseModel):
    id: str | None = None
    sectionOrder: int
    type: str = "PARAGRAPH"
    x: float
    y: float
    width: float
    height: float


class SectionSave(BaseModel):
    sections: list[SectionUpdateItem]


class NextSectionResponse(BaseModel):
    id: str
    type: str
    originalText: str | None = None
    aiExtractedText: str | None = None
    exactLetterTranslation: str | None = None
    autoTranslatedText: str | None = None
    wordByWordMeaning: str | None = None
    fullMeaning: str | None = None
    simplifiedMeaning: str | None = None
    pageNumber: int
    bookTitle: str
    book: BookRef
    croppedImageUrl: str | None = None
