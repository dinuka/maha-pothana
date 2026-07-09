from pydantic import BaseModel


class LanguageStats(BaseModel):
    total: int
    translated: int
    percent: float


class PageStats(BaseModel):
    pageNumber: int
    total: int
    translated: int
    percent: float


class TranslationStatsResponse(BaseModel):
    totalSections: int
    translatedSections: int
    pendingSections: int
    inProgressSections: int
    translationPercent: float
    byLanguage: dict[str, LanguageStats]
    byPage: list[PageStats]


class TranslatorStatsResponse(BaseModel):
    userId: str
    userName: str
    totalAssigned: int
    approvedCount: int
    rejectedCount: int
    pendingCount: int
    approvalRate: float | None = None
    avgTurnaroundHours: float | None = None
    lastActiveAt: str | None = None
