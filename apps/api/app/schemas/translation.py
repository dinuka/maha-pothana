from pydantic import BaseModel
from datetime import datetime

from app.schemas.refs import SectionRef, TranslatorRef, ApprovedByRef


class TranslationSubmit(BaseModel):
    translatedText: str
    exactLetterTranslation: str | None = None


class TranslationResponse(BaseModel):
    id: str
    section: SectionRef
    translator: TranslatorRef
    translatorName: str | None = None
    translatedText: str
    exactLetterTranslation: str | None = None
    isApproved: bool = False
    isEditorOverride: bool = False
    rejected: bool = False
    approvedBy: ApprovedByRef | None = None
    createdAt: datetime | None = None


class MyTranslationResponse(BaseModel):
    translatedText: str
    exactLetterTranslation: str | None = None
    isApproved: bool = False
