import html as html_module
import re
from pathlib import Path

from app.services.book_pdf import SectionContent, resolve_section_content

__all__ = [
    "SectionContent",
    "resolve_section_content",
    "build_book_html",
    "build_book_pdf_via_weasyprint",
    "pick_font",
]

FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"

FONT_LATIN = ("latin", FONT_DIR / "NotoSans.ttf")
FONT_DEVANAGARI = ("deva", FONT_DIR / "NotoSansDevanagari.ttf")
FONT_SINHALA = ("sinh", FONT_DIR / "NotoSansSinhala.ttf")

DEVANAGARI_RE = re.compile(r"[ऀ-ॿ]")
SINHALA_RE = re.compile(r"[඀-෿]")
# Neutral: punctuation/digits shared across scripts (incl. Devanagari danda ॥ used in
# Sinhala transliteration too) that must not sway script detection either way.
NEUTRAL_RE = re.compile(r"[\s।॥|.,;:!?()\[\]\-–—0-9‌‍]")


def pick_font(text: str) -> tuple[str, Path]:
    significant = NEUTRAL_RE.sub("", text)
    if not significant:
        return FONT_LATIN
    devanagari_count = len(DEVANAGARI_RE.findall(significant))
    sinhala_count = len(SINHALA_RE.findall(significant))
    if devanagari_count == 0 and sinhala_count == 0:
        return FONT_LATIN
    return FONT_DEVANAGARI if devanagari_count >= sinhala_count else FONT_SINHALA


def _escape(text: str) -> str:
    return html_module.escape(text)


def _text_to_html(text: str) -> str:
    """Render each raw newline-separated line in its own span, tagged with the
    script-appropriate font class. A block can legitimately mix scripts line by
    line (e.g. a Devanagari line followed by its IAST romanization), so font
    selection is per-line, not per-block.
    """
    parts = []
    for raw_line in text.split("\n"):
        fontname, _ = pick_font(raw_line)
        parts.append(f'<div class="line font-{fontname}">{_escape(raw_line)}</div>')
    return "".join(parts)


def build_book_html(book_title: str, sections_by_page: list[tuple[int, "list[SectionContent]"]]) -> str:
    font_faces = "\n".join(
        f"""@font-face {{
  font-family: "{name}";
  src: url("file://{path}");
}}"""
        for name, path in [FONT_LATIN, FONT_DEVANAGARI, FONT_SINHALA]
    )

    body_parts = [f'<h1 class="font-latin">{_escape(book_title)}</h1>']

    sections: list[SectionContent] = [content for _, page_sections in sections_by_page for content in page_sections]

    body_parts.append('<h2 class="font-latin">Source Text</h2>')
    for content in sections:
        if content.source_text:
            body_parts.append(f'<div class="text-block">{_text_to_html(content.source_text)}</div>')

    body_parts.append('<h2 class="font-latin">Exact Letter Transliteration</h2>')
    for content in sections:
        if content.exact_letter_transliteration:
            body_parts.append(f'<div class="text-block">{_text_to_html(content.exact_letter_transliteration)}</div>')

    body_parts.append('<h2 class="font-latin">Translation</h2>')
    for content in sections:
        if content.is_approved and content.translated_text:
            body_parts.append(f'<div class="text-block">{_text_to_html(content.translated_text)}</div>')

    body = "\n".join(body_parts)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{_escape(book_title)}</title>
<style>
{font_faces}

@page {{
  size: A4;
  margin: 50px;
}}

body {{
  font-size: 12pt;
  color: #000;
}}

.font-latin {{ font-family: "latin", sans-serif; }}
.font-deva {{ font-family: "deva", sans-serif; }}
.font-sinh {{ font-family: "sinh", sans-serif; }}

h1 {{
  font-size: 20pt;
  margin: 0 0 24px 0;
}}

h2 {{
  font-size: 13pt;
  margin: 22px 0 12px 0;
}}

.text-block {{
  margin-bottom: 12px;
}}

.text-block .line {{
  margin: 2px 0;
}}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def build_book_pdf_via_weasyprint(html_text: str) -> bytes:
    from weasyprint import HTML

    return HTML(string=html_text).write_pdf()
