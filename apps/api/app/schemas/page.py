from pydantic import BaseModel
from datetime import datetime

from app.schemas.refs import BookRef


class PageResponse(BaseModel):
    id: str
    book: BookRef
    pageNumber: int
    originalPageNumber: str
    imageKey: str | None = None
    width: int = 0
    height: int = 0
    status: str = "PENDING"
    createdAt: datetime | None = None


class PageListItem(BaseModel):
    id: str
    pageNumber: int
    originalPageNumber: str
    status: str
    sectionCount: int = 0
    translatedPercent: float = 0
    thumbnailUrl: str | None = None


class PageListResponse(BaseModel):
    items: list[PageListItem]
    total: int
    skip: int
    limit: int
