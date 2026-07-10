from enum import StrEnum


class BuildStatus(StrEnum):
    BUILDING = "BUILDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class VersionStatus(StrEnum):
    DRAFT = "DRAFT"
    FINALIZED = "FINALIZED"
    ARCHIVED = "ARCHIVED"
