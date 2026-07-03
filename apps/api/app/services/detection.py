import io
import logging
from PIL import Image

logger = logging.getLogger(__name__)

ROW_CONTENT_RATIO = 0.02
MERGE_GAP = 12
MIN_BAND_HEIGHT = 10
MIN_SECTION_WIDTH = 20
MIN_SECTION_HEIGHT = 15
HEADER_ZONE = 0.12
FOOTNOTE_ZONE = 0.82
PAGE_NUM_ZONE_X = 0.7
PAGE_NUM_ZONE_Y_START = 0.85


def detect_page_sections(
    image_data: bytes,
    page_width: int,
    page_height: int,
) -> list[dict]:
    try:
        img = Image.open(io.BytesIO(image_data))
    except Exception:
        logger.warning("Failed to open page image, using default sections")
        return create_default_sections(page_width, page_height)

    gray = img.convert("L")

    if page_width <= 0 or page_height <= 0:
        page_width, page_height = img.size

    bands = _find_content_bands(gray, page_width, page_height)

    if not bands:
        logger.info("No content detected in image, using default sections")
        return create_default_sections(page_width, page_height)

    sections = []
    for band_y0, band_y1 in bands:
        x0, x1 = _find_horizontal_bounds(gray, band_y0, band_y1, page_width)
        bw = x1 - x0
        bh = band_y1 - band_y0

        if bw < MIN_SECTION_WIDTH or bh < MIN_SECTION_HEIGHT:
            continue

        section_type = classify_section_type(x0, band_y0, x1, band_y1, bw, bh, page_width, page_height)
        confidence = round(min(1.0, max(0.1, (bw * bh) / (page_width * page_height * 0.3))), 2)

        sections.append({
            "sectionOrder": 0,
            "type": section_type,
            "x": x0,
            "y": band_y0,
            "width": bw,
            "height": bh,
            "confidence": confidence,
            "originalText": None,
            "croppedImageKey": None,
        })

    for i, sec in enumerate(sections):
        sec["sectionOrder"] = i

    return sections


def _find_content_bands(gray: Image.Image, page_width: int, page_height: int) -> list[tuple[int, int]]:
    pixels = gray.load()
    min_dark = int(page_width * ROW_CONTENT_RATIO)

    content_rows = []
    for y in range(page_height):
        dark_count = 0
        for x in range(page_width):
            if pixels[x, y] < 200:
                dark_count += 1
                if dark_count > min_dark:
                    content_rows.append(y)
                    break

    if not content_rows:
        return []

    bands = []
    band_start = content_rows[0]

    for i in range(1, len(content_rows)):
        if content_rows[i] - content_rows[i - 1] > MERGE_GAP:
            if content_rows[i - 1] - band_start >= MIN_BAND_HEIGHT:
                bands.append((band_start, content_rows[i - 1]))
            band_start = content_rows[i]

    if content_rows[-1] - band_start >= MIN_BAND_HEIGHT:
        bands.append((band_start, content_rows[-1]))

    return bands


def _find_horizontal_bounds(gray: Image.Image, y0: int, y1: int, page_width: int) -> tuple[int, int]:
    pixels = gray.load()
    min_dark = int((y1 - y0) * 0.05)

    left = 0
    for x in range(page_width):
        dark_count = 0
        for y in range(y0, y1 + 1):
            if pixels[x, y] < 200:
                dark_count += 1
        if dark_count > min_dark:
            left = x
            break

    right = page_width
    for x in range(page_width - 1, -1, -1):
        dark_count = 0
        for y in range(y0, y1 + 1):
            if pixels[x, y] < 200:
                dark_count += 1
        if dark_count > min_dark:
            right = x
            break

    return max(0, left - 4), min(page_width, right + 4)


def classify_section_type(
    x0: int, y0: int, x1: int, y1: int,
    bw: int, bh: int,
    page_width: int, page_height: int,
) -> str:
    rel_y = y0 / page_height if page_height else 0
    rel_x_center = (x0 + bw / 2) / page_width if page_width else 0

    if rel_y < HEADER_ZONE and bh < page_height * 0.08:
        return "HEADER"

    if rel_y > PAGE_NUM_ZONE_Y_START and rel_x_center > PAGE_NUM_ZONE_X and bh < page_height * 0.05:
        return "PAGE_NUMBER"

    if rel_y > FOOTNOTE_ZONE and bh < page_height * 0.06:
        return "FOOTNOTE"

    if bw > page_width * 0.4 and bh > page_height * 0.03:
        return "PARAGRAPH"

    return "OTHER"


def create_default_sections(page_width: int, page_height: int) -> list[dict]:
    return [
        {
            "sectionOrder": 0,
            "type": "HEADER",
            "x": max(20, int(page_width * 0.05)),
            "y": max(10, int(page_height * 0.02)),
            "width": max(100, int(page_width * 0.9)),
            "height": max(30, int(page_height * 0.08)),
            "confidence": 0.5,
            "originalText": None,
            "croppedImageKey": None,
        },
        {
            "sectionOrder": 1,
            "type": "PARAGRAPH",
            "x": max(20, int(page_width * 0.05)),
            "y": max(50, int(page_height * 0.12)),
            "width": max(100, int(page_width * 0.9)),
            "height": max(50, int(page_height * 0.3)),
            "confidence": 0.5,
            "originalText": None,
            "croppedImageKey": None,
        },
        {
            "sectionOrder": 2,
            "type": "PARAGRAPH",
            "x": max(20, int(page_width * 0.05)),
            "y": max(50, int(page_height * 0.45)),
            "width": max(100, int(page_width * 0.9)),
            "height": max(50, int(page_height * 0.3)),
            "confidence": 0.5,
            "originalText": None,
            "croppedImageKey": None,
        },
        {
            "sectionOrder": 3,
            "type": "FOOTNOTE",
            "x": max(20, int(page_width * 0.05)),
            "y": max(50, int(page_height * 0.78)),
            "width": max(100, int(page_width * 0.6)),
            "height": max(20, int(page_height * 0.06)),
            "confidence": 0.5,
            "originalText": None,
            "croppedImageKey": None,
        },
        {
            "sectionOrder": 4,
            "type": "PAGE_NUMBER",
            "x": max(50, int(page_width * 0.8)),
            "y": max(50, int(page_height * 0.88)),
            "width": max(30, int(page_width * 0.1)),
            "height": max(15, int(page_height * 0.04)),
            "confidence": 0.5,
            "originalText": None,
            "croppedImageKey": None,
        },
    ]
