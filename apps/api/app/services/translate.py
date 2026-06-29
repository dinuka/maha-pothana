import httpx
from app.config import settings


async def auto_translate(text: str, source_lang: str = "auto", target_lang: str = "en") -> str | None:
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{settings.libretranslate_url}/translate",
                json={
                    "q": text,
                    "source": source_lang,
                    "target": target_lang,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("translatedText")
    except Exception:
        pass
    return None
