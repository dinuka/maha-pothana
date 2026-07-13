from dataclasses import dataclass


@dataclass
class SectionContent:
    section_id: str
    section_order: int
    source_text: str | None = None
    exact_letter_transliteration: str | None = None
    translated_text: str | None = None
    is_approved: bool = False


def resolve_section_content(section: dict, latest_approved_translation: dict | None) -> SectionContent:
    source_text = section.get("aiExtractedText") or section.get("originalText")
    exact_letter = section.get("exactLetterTranslation")

    translated_text = None
    is_approved = latest_approved_translation is not None
    if is_approved:
        translated_text = latest_approved_translation.get("translatedText")
        exact_letter = latest_approved_translation.get("exactLetterTranslation") or exact_letter

    return SectionContent(
        section_id=str(section["_id"]),
        section_order=section.get("sectionOrder", 0),
        source_text=source_text,
        exact_letter_transliteration=exact_letter,
        translated_text=translated_text,
        is_approved=is_approved,
    )


def build_book_markdown(book_title: str, sections_by_page: list[tuple[int, list[SectionContent]]]) -> str:
    """Plain-text Markdown rendering of the same content as build_book_html."""
    lines = [f"# {book_title}", ""]

    sections: list[SectionContent] = [content for _, page_sections in sections_by_page for content in page_sections]

    lines.append("## Source Text")
    lines.append("")
    for content in sections:
        if content.source_text:
            lines.append(content.source_text)
            lines.append("")

    lines.append("## Exact Letter Transliteration")
    lines.append("")
    for content in sections:
        if content.exact_letter_transliteration:
            lines.append(content.exact_letter_transliteration)
            lines.append("")

    lines.append("## Translation")
    lines.append("")
    for content in sections:
        if content.is_approved and content.translated_text:
            lines.append(content.translated_text)
            lines.append("")

    return "\n".join(lines)
