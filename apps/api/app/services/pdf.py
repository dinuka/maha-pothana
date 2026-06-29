import io
from PIL import Image
from pypdf import PdfReader


def extract_page_count(data: bytes) -> int:
    reader = PdfReader(io.BytesIO(data))
    return len(reader.pages)


def render_page_as_image(data: bytes, page_number: int, dpi: int = 200) -> bytes | None:
    try:
        reader = PdfReader(io.BytesIO(data))
        if page_number < 0 or page_number >= len(reader.pages):
            return None
        page = reader.pages[page_number]
        images = page.images
        if images:
            img_data = images[0].data
            return img_data
        return None
    except Exception:
        return None


def get_page_dimensions(data: bytes, page_number: int) -> tuple[int, int]:
    reader = PdfReader(io.BytesIO(data))
    if page_number < 0 or page_number >= len(reader.pages):
        return (0, 0)
    page = reader.pages[page_number]
    mb = page.mediabox
    return (int(mb.width), int(mb.height))
