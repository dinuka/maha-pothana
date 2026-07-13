from app.services.book_html import FONT_DEVANAGARI, FONT_LATIN, FONT_SINHALA, build_book_html, pick_font
from app.services.book_pdf import SectionContent


def test_pick_font_devanagari_line():
    assert pick_font("श्री गणेशाय नमः") == FONT_DEVANAGARI


def test_pick_font_sinhala_line():
    assert pick_font("ශ්‍රී ගණේශාය නමඃ") == FONT_SINHALA


def test_pick_font_latin_line():
    assert pick_font("Devi Mahatmyam") == FONT_LATIN


def test_pick_font_danda_alone_is_neutral_not_devanagari():
    # U+0965 (॥) lives in the Devanagari Unicode block but is reused as
    # punctuation in Sinhala transliteration text; it must not force FONT_DEVANAGARI.
    assert pick_font("॥") == FONT_LATIN


def test_pick_font_sinhala_line_with_devanagari_danda_stays_sinhala():
    assert pick_font("॥ ශ්‍රීදුර්ගායෛ නමඃ ॥") == FONT_SINHALA


def test_pick_font_devanagari_line_with_danda_stays_devanagari():
    assert pick_font("॥ देवी माहात्म्यम् ॥") == FONT_DEVANAGARI


def test_build_book_html_includes_all_approved_fields():
    sections = [
        SectionContent(
            section_id="s1",
            section_order=1,
            source_text="Source One",
            exact_letter_transliteration="Translit One",
            translated_text="Translation One",
            is_approved=True,
        )
    ]
    html = build_book_html("My Book", [(1, sections)])

    assert "My Book" in html
    assert "Source One" in html
    assert "Translit One" in html
    assert "Translation One" in html


def test_build_book_html_hides_unapproved_translation():
    sections = [
        SectionContent(
            section_id="s1",
            section_order=1,
            source_text="Source Only",
            exact_letter_transliteration="Translit Only",
            translated_text="Should Not Appear",
            is_approved=False,
        )
    ]
    html = build_book_html("My Book", [(1, sections)])

    assert "Source Only" in html
    assert "Translit Only" in html
    assert "Should Not Appear" not in html


def test_build_book_html_escapes_content():
    sections = [
        SectionContent(
            section_id="s1",
            section_order=1,
            source_text="<script>alert(1)</script>",
            is_approved=False,
        )
    ]
    html = build_book_html("My Book", [(1, sections)])

    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_build_book_html_mixed_script_lines_use_correct_font_class():
    sections = [
        SectionContent(
            section_id="s1",
            section_order=1,
            source_text="॥ देवी माहात्म्यम् ॥\nDevī Māhātmyam",
            is_approved=False,
        )
    ]
    html = build_book_html("My Book", [(1, sections)])

    assert 'font-deva">॥ देवी माहात्म्यम् ॥' in html
    assert 'font-latin">Devī Māhātmyam' in html


def test_build_book_html_flattens_sections_across_pages():
    sections_p2 = [
        SectionContent(section_id="b", section_order=1, source_text="Page Two Content", is_approved=False)
    ]
    html = build_book_html("My Book", [(1, []), (2, sections_p2)])

    assert "Page 1" not in html
    assert "Page 2" not in html
    assert "Page Two Content" in html


def test_build_book_html_groups_all_source_before_all_translit_before_all_translation():
    sections = [
        SectionContent(
            section_id="s1",
            section_order=1,
            source_text="Source One",
            exact_letter_transliteration="Translit One",
            translated_text="Translation One",
            is_approved=True,
        ),
        SectionContent(
            section_id="s2",
            section_order=2,
            source_text="Source Two",
            exact_letter_transliteration="Translit Two",
            translated_text="Translation Two",
            is_approved=True,
        ),
    ]
    html = build_book_html("My Book", [(1, sections)])

    assert html.index("Source One") < html.index("Source Two") < html.index("Translit One")
    assert html.index("Translit One") < html.index("Translit Two") < html.index("Translation One")
    assert html.index("Translation One") < html.index("Translation Two")


def test_build_book_pdf_via_weasyprint_produces_valid_pdf():
    from app.services.book_html import build_book_pdf_via_weasyprint

    sections = [
        SectionContent(
            section_id="s1",
            section_order=1,
            source_text="Hello world",
            exact_letter_transliteration="ශ්‍රී ගණේශාය",
            is_approved=False,
        )
    ]
    html = build_book_html("My Book", [(1, sections)])
    pdf_bytes = build_book_pdf_via_weasyprint(html)

    assert pdf_bytes.startswith(b"%PDF")
