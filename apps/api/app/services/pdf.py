import io
import fitz
from pypdf import PdfReader


def extract_page_count(data: bytes) -> int:
    reader = PdfReader(io.BytesIO(data))
    return len(reader.pages)


def render_page_as_image(data: bytes, page_number: int, dpi: int = 200) -> bytes | None:
    try:
        with fitz.open(stream=data, filetype="pdf") as doc:
            if page_number < 0 or page_number >= doc.page_count:
                return None
            page = doc[page_number]
            pix = page.get_pixmap(dpi=dpi)
            return pix.tobytes("png")
    except Exception:
        return None


def render_page_as_thumbnail(data: bytes, page_number: int, dpi: int = 30) -> bytes | None:
    try:
        with fitz.open(stream=data, filetype="pdf") as doc:
            if page_number < 0 or page_number >= doc.page_count:
                return None
            page = doc[page_number]
            pix = page.get_pixmap(dpi=dpi)
            return pix.tobytes("png")
    except Exception:
        return None


def get_page_dimensions(data: bytes, page_number: int) -> tuple[int, int]:
    reader = PdfReader(io.BytesIO(data))
    if page_number < 0 or page_number >= len(reader.pages):
        return (0, 0)
    page = reader.pages[page_number]
    mb = page.mediabox
    return (int(mb.width), int(mb.height))
