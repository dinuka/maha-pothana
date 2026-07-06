from __future__ import annotations

from pydantic import BaseModel
from datetime import datetime


class ExtractRequest(BaseModel):
    pass


class ExtractResponse(BaseModel):
    taskId: str | None = None
    sectionId: str
    status: str
    extractedText: str | None = None
    confidence: float | None = None


class ExtractionResultResponse(BaseModel):
    sectionId: str
    extractedText: str
    confidence: float
    model: str
    processingTimeMs: int
    createdAt: datetime


class BatchExtractResponse(BaseModel):
    taskId: str
    bookId: str
    totalSections: int
    estimatedCost: float
    status: str


class ExtractionStatusResponse(BaseModel):
    bookId: str
    totalSections: int
    extracted: int
    pending: int
    failed: int
    inProgress: bool


class TransliterateResponse(BaseModel):
    sectionId: str
    sourceText: str
    transliteratedText: str
    sourceScript: str
    targetScript: str
    confidence: float
    model: str
    cached: bool


class TransliterationsResponse(BaseModel):
    sectionId: str
    transliterations: list[TransliterationItem]


class TransliterationItem(BaseModel):
    targetScript: str
    transliteratedText: str
    confidence: float
    model: str
    createdAt: datetime


class SourceTextUpdate(BaseModel):
    text: str
    source: str  # "ai" | "ocr"


class ReverseTransliterateRequest(BaseModel):
    transliteratedText: str
    sourceScript: str
    targetScript: str


class ReverseTransliterateResponse(BaseModel):
    sourceText: str
    confidence: float
    model: str
