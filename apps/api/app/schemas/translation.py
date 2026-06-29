from pydantic import BaseModel
from datetime import datetime


class TranslationSubmit(BaseModel):
    translatedText: str
    exactLetterTranslation: str | None = None


class TranslationResponse(BaseModel):
    id: str
    sectionId: str
    translatorId: str
    translatorName: str | None = None
    translatedText: str
    exactLetterTranslation: str | None = None
    isApproved: bool = False
    approvedBy: str | None = None
    createdAt: datetime | None = None


class MyTranslationResponse(BaseModel):
    translatedText: str
    exactLetterTranslation: str | None = None
    isApproved: bool = False
