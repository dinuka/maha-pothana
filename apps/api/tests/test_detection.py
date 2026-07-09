import io
import pytest
from PIL import Image
from app.services.detection import (
    detect_page_sections,
    classify_section_type,
    create_default_sections,
)


def _make_test_image(dark_rects: list[tuple[int, int, int, int]], width: int = 800, height: int = 1200) -> bytes:
    img = Image.new("L", (width, height), 255)
    pixels = img.load()
    for x0, y0, x1, y1 in dark_rects:
        for y in range(y0, min(y1, height)):
            for x in range(x0, min(x1, width)):
                pixels[x, y] = 0
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_classify_section_type_header():
    result = classify_section_type(50, 20, 200, 60, 150, 40, 800, 1200)
    assert result == "HEADER"


def test_classify_section_type_paragraph():
    result = classify_section_type(50, 200, 750, 400, 700, 200, 800, 1200)
    assert result == "PARAGRAPH"


def test_classify_section_type_page_number():
    result = classify_section_type(650, 1100, 750, 1140, 100, 40, 800, 1200)
    assert result == "PAGE_NUMBER"


def test_classify_section_type_footnote():
    result = classify_section_type(50, 1050, 400, 1100, 350, 50, 800, 1200)
    assert result == "FOOTNOTE"


def test_classify_section_type_other():
    result = classify_section_type(50, 500, 100, 530, 50, 30, 800, 1200)
    assert result == "OTHER"


def test_create_default_sections():
    sections = create_default_sections(800, 1200)
    assert len(sections) == 5
    assert sections[0]["type"] == "HEADER"
    assert sections[1]["type"] == "PARAGRAPH"
    assert sections[2]["type"] == "PARAGRAPH"
    assert sections[3]["type"] == "FOOTNOTE"
    assert sections[4]["type"] == "PAGE_NUMBER"
    for sec in sections:
        assert 0 <= sec["x"] <= 800
        assert 0 <= sec["y"] <= 1200
        assert sec["width"] > 0
        assert sec["height"] > 0
        assert "confidence" in sec


def test_detect_page_sections_empty_image_falls_back():
    sections = detect_page_sections(b"", 800, 1200)
    assert len(sections) == 5
    assert sections[0]["type"] == "HEADER"


def test_detect_page_sections_single_paragraph():
    image_data = _make_test_image([
        (100, 200, 700, 500),
    ])
    sections = detect_page_sections(image_data, 800, 1200)
    assert len(sections) == 1
    assert sections[0]["type"] == "PARAGRAPH"
    assert 50 <= sections[0]["x"] <= 120
    assert 180 <= sections[0]["y"] <= 220
    assert sections[0]["width"] > 400


def test_detect_page_sections_header_and_body():
    image_data = _make_test_image([
        (100, 30, 700, 70),
        (100, 200, 700, 500),
        (100, 520, 700, 800),
    ])
    sections = detect_page_sections(image_data, 800, 1200)
    assert len(sections) >= 2
    types = [s["type"] for s in sections]
    assert "HEADER" in types
    assert "PARAGRAPH" in types


def test_detect_page_sections_different_positions():
    image_data = _make_test_image([
        (600, 1050, 750, 1080),
    ])
    sections = detect_page_sections(image_data, 800, 1200)
    assert len(sections) == 1
    assert sections[0]["type"] == "PAGE_NUMBER"


def test_detect_page_sections_with_image_size():
    image_data = _make_test_image([
        (50, 50, 750, 150),
    ])
    sections = detect_page_sections(image_data, 0, 0)
    assert len(sections) >= 1


def test_detect_page_sections_ignores_mismatched_dpi_dimensions():
    # Simulates the real production bug: page_width/page_height are stale
    # 72-DPI PDF mediabox points, but the real rendered image is 800x1200.
    # Content sits in the bottom-right, outside the stale 290x430 bounds --
    # the buggy code would never scan that far and would miss it entirely.
    image_data = _make_test_image([
        (600, 900, 780, 1150),
    ])
    sections = detect_page_sections(image_data, page_width=290, page_height=430)
    assert len(sections) == 1
    assert sections[0]["x"] >= 590
    assert sections[0]["y"] >= 890


def test_detect_page_sections_full_width_not_clipped_by_stale_dims():
    # A wide paragraph spanning most of the real 800px-wide image, with
    # stale (72-DPI-style) page_width passed in artificially small -- any
    # bound derived from that stale value would clip well below 800.
    image_data = _make_test_image([
        (20, 200, 780, 500),
    ])
    sections = detect_page_sections(image_data, page_width=290, page_height=430)
    assert len(sections) == 1
    assert sections[0]["width"] > 700


def test_detect_page_sections_seeds_missing_recurring_element_with_content():
    # No band detector match near the profiled footnote position -- the actual
    # content there (300x30) is picked up by the band scan and replaced via
    # the snap path, exercising "detected, then replaced with profile geometry".
    image_data = _make_test_image([
        (100, 200, 700, 500),  # body paragraph, detected normally
        (100, 1075, 400, 1105),  # footnote-position content the band scan misses due to size
    ])
    profile = {"FOOTNOTE": {"x": 0.1, "y": 0.89, "width": 0.4, "height": 0.03}}
    sections = detect_page_sections(image_data, 800, 1200, profile=profile)
    types = [s["type"] for s in sections]
    assert "FOOTNOTE" in types


def test_detect_page_sections_seeds_true_gap_below_detection_thresholds():
    # A tiny page-number-sized mark (12x10px, under MIN_SECTION_WIDTH/HEIGHT)
    # never forms its own band, so this exercises a genuine seed: no detected
    # section of this type exists at all, but there is real content there.
    image_data = _make_test_image([
        (100, 200, 700, 500),  # body paragraph, detected normally
        (710, 1080, 722, 1090),  # small mark, filtered out as its own band
    ])
    profile = {"PAGE_NUMBER": {"x": 0.88, "y": 0.89, "width": 0.05, "height": 0.02}}
    sections = detect_page_sections(image_data, 800, 1200, profile=profile)
    page_number_sections = [s for s in sections if s["type"] == "PAGE_NUMBER"]
    assert len(page_number_sections) == 1
    assert page_number_sections[0]["confidence"] == 0.4


def test_detect_page_sections_does_not_seed_blank_recurring_region():
    # Profile expects a page number near the bottom-right, but this page has
    # nothing there -- must not inject a phantom box.
    image_data = _make_test_image([
        (100, 200, 700, 500),
    ])
    profile = {"PAGE_NUMBER": {"x": 0.85, "y": 0.9, "width": 0.1, "height": 0.04}}
    sections = detect_page_sections(image_data, 800, 1200, profile=profile)
    types = [s["type"] for s in sections]
    assert "PAGE_NUMBER" not in types


def test_detect_page_sections_does_not_duplicate_already_detected_recurring_element():
    # Header is already found by the normal band detector at roughly the
    # profiled position -- snapping replaces it, must not end up with two.
    image_data = _make_test_image([
        (100, 30, 700, 70),
    ])
    profile = {"HEADER": {"x": 0.1, "y": 0.02, "width": 0.7, "height": 0.05}}
    sections = detect_page_sections(image_data, 800, 1200, profile=profile)
    header_sections = [s for s in sections if s["type"] == "HEADER"]
    assert len(header_sections) == 1


def test_detect_page_sections_snaps_detected_recurring_element_to_profile_geometry():
    # Band detector finds a HEADER, but drawn too short/narrow compared to
    # this book's usual header box -- the detected geometry should be
    # replaced by the profiled (book-consistent) geometry, not kept as-is.
    image_data = _make_test_image([
        (300, 30, 500, 50),  # detector's guess: narrow, off-center
    ])
    profile = {"HEADER": {"x": 0.1, "y": 0.02, "width": 0.7, "height": 0.05}}
    sections = detect_page_sections(image_data, 800, 1200, profile=profile)
    header_sections = [s for s in sections if s["type"] == "HEADER"]
    assert len(header_sections) == 1
    header = header_sections[0]
    assert header["x"] == int(0.1 * 800)
    assert header["width"] == int(0.7 * 800)


def test_detect_page_sections_does_not_touch_other_types_near_recurring_zone():
    # A PARAGRAPH detected near the header zone must never be reclassified,
    # resized, or have a phantom HEADER seeded alongside it just because a
    # HEADER profile exists and dark content happens to reach that zone --
    # the content there belongs to the paragraph, not an undetected header.
    image_data = _make_test_image([
        (50, 20, 750, 300),  # large block starting near the top, classified PARAGRAPH
    ])
    profile = {"HEADER": {"x": 0.1, "y": 0.02, "width": 0.7, "height": 0.05}}
    sections = detect_page_sections(image_data, 800, 1200, profile=profile)
    assert len(sections) == 1
    paragraph = sections[0]
    assert paragraph["type"] == "PARAGRAPH"
    assert paragraph["y"] == 20
    assert 270 <= paragraph["height"] <= 280


def test_detect_page_sections_does_not_collapse_multiple_same_type_sections():
    # Two vertically separated footnote blocks (each its own band) on this
    # page -- must not be collapsed into a single profiled footnote box
    # (that would be data loss).
    image_data = _make_test_image([
        (100, 990, 400, 1015),
        (100, 1075, 400, 1100),
    ])
    profile = {"FOOTNOTE": {"x": 0.1, "y": 0.83, "width": 0.4, "height": 0.03}}
    sections = detect_page_sections(image_data, 800, 1200, profile=profile)
    footnote_sections = [s for s in sections if s["type"] == "FOOTNOTE"]
    assert len(footnote_sections) == 2


def test_detect_page_sections_no_profile_behaves_as_before():
    image_data = _make_test_image([
        (100, 200, 700, 500),
    ])
    sections = detect_page_sections(image_data, 800, 1200, profile=None)
    assert len(sections) == 1


def test_detect_page_sections_merges_multiline_paragraph_at_real_dpi():
    # Two paragraph clusters at realistic 200-DPI proportions (1700x2200,
    # matching the real bug page). Each cluster has 2 closely-spaced line
    # rects (simulating a Devanagari line + its transliteration line);
    # clusters are separated by a large blank gap. Detection should merge
    # each cluster into a single PARAGRAPH section, not one box per line.
    image_data = _make_test_image(
        [
            (150, 300, 1550, 340),
            (150, 355, 1550, 395),
            (150, 700, 1550, 740),
            (150, 755, 1550, 795),
        ],
        width=1700,
        height=2200,
    )
    sections = detect_page_sections(image_data, page_width=612, page_height=792)
    assert len(sections) == 2
    for sec in sections:
        assert sec["type"] == "PARAGRAPH"
        assert sec["width"] > 1300
