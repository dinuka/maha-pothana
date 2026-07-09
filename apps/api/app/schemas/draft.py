from pydantic import BaseModel
from datetime import datetime


class DraftCreate(BaseModel):
    sectionId: str
    translatedText: str


class DraftResponse(BaseModel):
    draftId: str
    translatedText: str
    updatedAt: datetime
