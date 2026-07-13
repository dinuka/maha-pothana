from pydantic import BaseModel
from datetime import datetime

from app.models.page_status import PageStatus
from app.models.review_status import ReviewStatus
from app.schemas.refs import BookRef


class PageResponse(BaseModel):
    id: str
    book: BookRef
    pageNumber: int
    originalPageNumber: str
    imageKey: str | None = None
    imageUrl: str | None = None
    width: int = 0
    height: int = 0
    status: PageStatus = PageStatus.PENDING
    createdAt: datetime | None = None


class PageListItem(BaseModel):
    id: str
    pageNumber: int
    originalPageNumber: str
    status: PageStatus
    sectionCount: int = 0
    translatedPercent: float = 0
    thumbnailUrl: str | None = None
    reviewStatus: ReviewStatus = ReviewStatus.NOT_STARTED


class PageListResponse(BaseModel):
    items: list[PageListItem]
    total: int
    skip: int
    limit: int


class PageImageResponse(BaseModel):
    pageNumber: int
    imageUrl: str | None = None
    totalPages: int
