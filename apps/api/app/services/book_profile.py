import statistics

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.page_status import PageStatus

# Only these types recur at a consistent position across a book's pages (running
# header, footnote block, page number). Body paragraphs vary page to page with
# how much text flows onto them, so a position prior would misplace them -- they
# are intentionally left out and stay on the plain band detector.
RECURRING_TYPES = {"HEADER", "FOOTNOTE", "PAGE_NUMBER"}

# A type must appear on at least this fraction of the book's confirmed pages
# before we trust its position enough to seed it on an undetected page.
MIN_APPEARANCE_RATIO = 0.5


async def build_recurring_element_profile(
    db: AsyncIOMotorDatabase, book_id: str
) -> dict[str, dict[str, float]]:
    """Return normalized median bbox per recurring section type for this book.

    Normalized to (x/width, y/height, w/width, h/height) so the profile is
    independent of any one page's pixel dimensions. Built fresh from currently
    confirmed sections on every call rather than cached, so it can't drift out
    of sync with corrections the user has since made.

    Only pages with status SECTIONS_CONFIRMED/FINALIZED contribute, which
    naturally excludes the page currently being detected -- detect_sections
    moves it to PROCESSING before this runs, so it never has confirmed
    sections of its own yet.
    """
    pages = await db.pages.find(
        {
            "book.id": book_id,
            "status": {"$in": [PageStatus.SECTIONS_CONFIRMED, PageStatus.FINALIZED]},
        },
        {"_id": 1, "width": 1, "height": 1},
    ).to_list(length=None)

    if not pages:
        return {}

    page_dims = {str(p["_id"]): (p.get("width", 0), p.get("height", 0)) for p in pages}
    page_ids = list(page_dims.keys())

    sections = await db.sections.find(
        {"page.id": {"$in": page_ids}, "type": {"$in": list(RECURRING_TYPES)}}
    ).to_list(length=None)

    normalized_by_type: dict[str, list[tuple[float, float, float, float]]] = {}
    for sec in sections:
        page_width, page_height = page_dims.get(sec["page"]["id"], (0, 0))
        if not page_width or not page_height:
            continue
        sec_type = sec["type"]
        normalized_by_type.setdefault(sec_type, []).append((
            sec.get("x", 0) / page_width,
            sec.get("y", 0) / page_height,
            sec.get("width", 0) / page_width,
            sec.get("height", 0) / page_height,
        ))

    profile = {}
    min_appearances = max(1, int(len(page_ids) * MIN_APPEARANCE_RATIO))
    for sec_type, boxes in normalized_by_type.items():
        if len(boxes) < min_appearances:
            continue
        xs, ys, ws, hs = zip(*boxes)
        profile[sec_type] = {
            "x": statistics.median(xs),
            "y": statistics.median(ys),
            "width": statistics.median(ws),
            "height": statistics.median(hs),
        }

    return profile
