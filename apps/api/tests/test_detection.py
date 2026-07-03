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
