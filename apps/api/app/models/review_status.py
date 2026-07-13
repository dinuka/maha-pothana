from enum import StrEnum


class ReviewStatus(StrEnum):
    REJECTED = "REJECTED"
    NOT_STARTED = "NOT_STARTED"
    NO_TRANSLATIONS = "NO_TRANSLATIONS"
    PARTIALLY_TRANSLATED = "PARTIALLY_TRANSLATED"
    FULLY_TRANSLATED = "FULLY_TRANSLATED"
    PARTIALLY_APPROVED = "PARTIALLY_APPROVED"
    FULLY_APPROVED = "FULLY_APPROVED"


def compute_review_status(
    section_count: int,
    translated_section_count: int,
    approved_count: int,
    has_rejection: bool,
) -> ReviewStatus:
    """Compute the page-level translation/review status from section counts.

    Priority order is significant: states are not mutually exclusive as
    independent predicates (e.g. a page can match both "partially translated"
    and "partially approved" at once), so this must stay an ordered chain
    rather than independent checks, resolving overlaps to the earliest match.

    has_rejection wins over everything else once true. Callers must compute it
    per-section as "every submitted translation is rejected and none is
    approved" (mirrors sections.py's _check_reentry_logic) — not merely "any
    rejected translation exists" — since a rejected document is never deleted
    once the section is later resolved via a resubmission or approval, and
    REJECTED should reflect a section that is currently and entirely blocked,
    not one that had a rejection somewhere in its history.
    """
    if has_rejection:
        return ReviewStatus.REJECTED
    if section_count == 0:
        return ReviewStatus.NOT_STARTED
    if translated_section_count == 0:
        return ReviewStatus.NO_TRANSLATIONS
    if translated_section_count < section_count:
        return ReviewStatus.PARTIALLY_TRANSLATED
    if approved_count == 0:
        return ReviewStatus.FULLY_TRANSLATED
    if approved_count < section_count:
        return ReviewStatus.PARTIALLY_APPROVED
    return ReviewStatus.FULLY_APPROVED
