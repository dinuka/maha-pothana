from enum import StrEnum


class PageStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    DETECTION_FAILED = "DETECTION_FAILED"
    SECTIONS_CONFIRMED = "SECTIONS_CONFIRMED"
    IN_TRANSLATION = "IN_TRANSLATION"
    TRANSLATED = "TRANSLATED"
    FINALIZED = "FINALIZED"


# Derived-only statuses: never written to the `pages` collection. They are computed
# at read time from section/translation counts and layered on top of SECTIONS_CONFIRMED
# so translator progress can't drift out of sync the way a stored flag would.
DERIVED_PAGE_STATUSES = {PageStatus.IN_TRANSLATION, PageStatus.TRANSLATED}


def parse_page_status(value: str | None) -> PageStatus:
    """Parse a stored status value, falling back to PENDING for unrecognized ones.

    Stored status is a plain string at the Mongo boundary, so a value predating
    this enum (or written by a future service revision) must not 500 the request.
    """
    try:
        return PageStatus(value)
    except ValueError:
        return PageStatus.PENDING


def with_translation_progress(
    stored_status: PageStatus, section_count: int, translated_count: int
) -> PageStatus:
    """Overlay translator-progress on top of a stored SECTIONS_CONFIRMED status.

    translated_count counts sections with at least one submitted translation
    (approval status is irrelevant here — this reflects translator effort, not
    editor sign-off, which is checked separately by the finalize gate).
    """
    if stored_status != PageStatus.SECTIONS_CONFIRMED or section_count == 0:
        return stored_status
    if translated_count == 0:
        return stored_status
    if translated_count < section_count:
        return PageStatus.IN_TRANSLATION
    return PageStatus.TRANSLATED
