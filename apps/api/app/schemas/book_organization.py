from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

from app.models.build_status import BuildStatus, VersionStatus
from app.models.review_status import ReviewStatus


class PageOrderItem(BaseModel):
    pageId: str
    order: int


class PageReorderRequest(BaseModel):
    orders: list[PageOrderItem]


class ReorderedPageRef(BaseModel):
    id: str
    order: int
    pageNumber: int


class PageReorderResponse(BaseModel):
    success: bool
    reorderedCount: int
    pages: list[ReorderedPageRef]


class AddPageRequest(BaseModel):
    insertAfterOrder: int = Field(..., ge=0)


class DeletePageResponse(BaseModel):
    success: bool
    deleted: dict[str, int]


class PageWithProgress(BaseModel):
    id: str
    pageNumber: int
    originalPageNumber: str
    order: int
    status: str
    thumbnailUrl: str | None = None
    sectionCount: int = 0
    approvedSectionCount: int = 0
    translationPercent: float = 0
    computedStatus: str = "not_started"
    reviewStatus: ReviewStatus = ReviewStatus.NOT_STARTED


class PageListStats(BaseModel):
    totalPages: int
    totalSections: int
    translatedSections: int
    pendingReviewSections: int
    overallPercent: float


class PaginationInfo(BaseModel):
    page: int
    limit: int
    total: int
    totalPages: int


class FilteredPageListResponse(BaseModel):
    pages: list[PageWithProgress]
    pagination: PaginationInfo
    stats: PageListStats


class SectionEditHistorySnapshot(BaseModel):
    sections: list[dict]


class SectionEditHistoryEntry(BaseModel):
    id: str
    editorId: str
    editorName: str
    action: str = "UPDATE"
    snapshot: SectionEditHistorySnapshot
    timestamp: datetime


class PageHistoryResponse(BaseModel):
    pageId: str
    history: list[SectionEditHistoryEntry]


class ApproveTranslationResponse(BaseModel):
    success: bool
    translation: dict


class RejectTranslationRequest(BaseModel):
    reason: str | None = None


class RejectTranslationResponse(BaseModel):
    success: bool
    translation: dict


class EditorOverrideRequest(BaseModel):
    translatedText: str = Field(..., max_length=10000)
    sourceTranslationId: str | None = None


class EditorOverrideResponse(BaseModel):
    id: str
    sectionId: str
    translatorId: str
    translatorName: str | None = None
    isApproved: bool = True
    isEditorOverride: bool = True
    translatedText: str
    createdAt: datetime


class BuildProgressResponse(BaseModel):
    id: str | None = None
    bookId: str | None = None
    status: str
    versionNumber: int | None = None
    currentPage: int | None = None
    totalPages: int | None = None
    estimatedRemainingMs: int | None = None
    startedAt: datetime | None = None
    totalSections: int | None = None
    approvedSections: int | None = None
    buildDurationMs: int | None = None
    fileKey: str | None = None
    completedAt: datetime | None = None
    errorMessage: str | None = None
    failedAt: datetime | None = None
    message: str | None = None


class CancelBuildResponse(BaseModel):
    success: bool
    message: str = "Build cancelled successfully"


class BuildListItem(BaseModel):
    id: str
    versionNumber: int
    status: str
    totalSections: int | None = None
    approvedSections: int | None = None
    buildDurationMs: int | None = None
    createdBy: dict | None = None
    createdAt: datetime | None = None
    completedAt: datetime | None = None


class BuildListPagination(BaseModel):
    page: int
    limit: int
    total: int
    totalPages: int


class BuildListResponse(BaseModel):
    builds: list[BuildListItem]
    pagination: BuildListPagination


class VersionListItem(BaseModel):
    versionNumber: int
    label: str | None = None
    status: VersionStatus
    buildId: str | None = None
    changelog: str | None = None
    createdBy: dict | None = None
    totalSections: int | None = None
    approvedSections: int | None = None
    createdAt: datetime | None = None
    hasMarkdown: bool = False
    hasHtml: bool = False


class VersionListResponse(BaseModel):
    versions: list[VersionListItem]


class CreateVersionRequest(BaseModel):
    label: str | None = Field(None, max_length=100)
    changelog: str | None = Field(None, max_length=500)


class CreateVersionResponse(BaseModel):
    versionNumber: int
    bookId: str
    label: str | None = None
    changelog: str | None = None
    status: VersionStatus = VersionStatus.DRAFT
    fileKey: str | None = None
    createdBy: str | None = None
    createdAt: datetime | None = None


class DownloadResponse(BaseModel):
    downloadUrl: str
    filename: str
    expiresAt: datetime
    versionNumber: int
