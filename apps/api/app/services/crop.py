import io
from PIL import Image


def crop_section(page_image_data: bytes, x: float, y: float, width: float, height: float) -> bytes | None:
    try:
        img = Image.open(io.BytesIO(page_image_data))
        cropped = img.crop((x, y, x + width, y + height))
        buf = io.BytesIO()
        cropped.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return None
