from pydantic import BaseModel
from datetime import datetime


class TranslationHistoryItem(BaseModel):
    translationId: str
    sectionId: str
    pageNumber: int
    sectionOrder: int
    translatorId: str
    translatorName: str
    translatedText: str
    action: str
    performedBy: str | None = None
    performedByName: str | None = None
    createdAt: datetime


class TranslationHistoryResponse(BaseModel):
    items: list[TranslationHistoryItem]
    nextCursor: str | None = None
    hasMore: bool
