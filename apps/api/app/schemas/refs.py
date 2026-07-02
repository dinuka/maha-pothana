from pydantic import BaseModel


class BookRef(BaseModel):
    id: str


class PageRef(BaseModel):
    id: str


class SectionRef(BaseModel):
    id: str


class TranslatorRef(BaseModel):
    id: str


class OwnerRef(BaseModel):
    id: str


class UserRef(BaseModel):
    id: str


class ApprovedByRef(BaseModel):
    id: str


class InvitedByRef(BaseModel):
    id: str
