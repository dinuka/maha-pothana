from app.services.book_pdf import SectionContent, resolve_section_content


def test_resolve_section_content_uses_ai_extracted_text_over_original():
    section = {"_id": "s1", "sectionOrder": 1, "aiExtractedText": "ai text", "originalText": "orig text"}
    content = resolve_section_content(section, None)
    assert content.source_text == "ai text"


def test_resolve_section_content_falls_back_to_original_text():
    section = {"_id": "s1", "sectionOrder": 1, "aiExtractedText": None, "originalText": "orig text"}
    content = resolve_section_content(section, None)
    assert content.source_text == "orig text"


def test_resolve_section_content_no_approved_translation_hides_translation():
    section = {
        "_id": "s1",
        "sectionOrder": 1,
        "originalText": "source",
        "exactLetterTranslation": "section-level translit",
    }
    content = resolve_section_content(section, None)
    assert content.is_approved is False
    assert content.translated_text is None
    assert content.exact_letter_transliteration == "section-level translit"


def test_resolve_section_content_approved_translation_uses_its_own_transliteration():
    section = {
        "_id": "s1",
        "sectionOrder": 1,
        "originalText": "source",
        "exactLetterTranslation": "section-level translit",
    }
    translation = {"translatedText": "translated!", "exactLetterTranslation": "translator translit"}
    content = resolve_section_content(section, translation)
    assert content.is_approved is True
    assert content.translated_text == "translated!"
    assert content.exact_letter_transliteration == "translator translit"


def test_resolve_section_content_approved_translation_without_own_transliteration_falls_back():
    section = {
        "_id": "s1",
        "sectionOrder": 1,
        "originalText": "source",
        "exactLetterTranslation": "section-level translit",
    }
    translation = {"translatedText": "translated!", "exactLetterTranslation": None}
    content = resolve_section_content(section, translation)
    assert content.exact_letter_transliteration == "section-level translit"


def test_build_book_markdown_includes_all_approved_fields():
    from app.services.book_pdf import build_book_markdown

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
    md = build_book_markdown("My Book", [(1, sections)])

    assert "My Book" in md
    assert "Source One" in md
    assert "Translit One" in md
    assert "Translation One" in md


def test_build_book_markdown_hides_unapproved_translation():
    from app.services.book_pdf import build_book_markdown

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
    md = build_book_markdown("My Book", [(1, sections)])

    assert "Source Only" in md
    assert "Translit Only" in md
    assert "Should Not Appear" not in md


def test_build_book_markdown_multiple_pages_in_order():
    from app.services.book_pdf import build_book_markdown

    sections_p1 = [
        SectionContent(section_id="a", section_order=1, source_text="Page One Content", is_approved=False)
    ]
    sections_p2 = [
        SectionContent(section_id="b", section_order=1, source_text="Page Two Content", is_approved=False)
    ]
    md = build_book_markdown("My Book", [(1, sections_p1), (2, sections_p2)])

    assert md.index("Page One Content") < md.index("Page Two Content")


def test_build_book_markdown_skips_pages_with_no_sections():
    from app.services.book_pdf import build_book_markdown

    sections_p2 = [
        SectionContent(section_id="b", section_order=1, source_text="Page Two Content", is_approved=False)
    ]
    md = build_book_markdown("My Book", [(1, []), (2, sections_p2)])

    assert "Page 1" not in md
    assert "Page Two Content" in md
