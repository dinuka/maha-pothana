import json
import logging
import time
from dataclasses import dataclass

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
TRANSLATION_MODELS = settings.openrouter_translation_models
TRANSLATION_TIMEOUT = 60
ANALYSIS_TIMEOUT = 90


async def auto_translate(text: str, source_lang: str = "auto", target_lang: str = "en") -> str | None:
    api_key = settings.openrouter_api_key
    if not api_key:
        logger.warning("[translate] auto_translate: OpenRouter API key not configured")
        return None

    system_message = "You are a translation engine. Output only the translated text, nothing else."
    source_desc = "the source language" if source_lang == "auto" else source_lang
    prompt = (
        f"Translate the following text from {source_desc} into {target_lang}.\n"
        "Rules:\n"
        "1. Preserve meaning and tone.\n"
        "2. Do NOT explain your work.\n"
        "3. Return ONLY the translated text.\n\n"
        f"Input:\n{text}\n\n"
        "Output:"
    )

    last_error = None
    for model in TRANSLATION_MODELS:
        logger.info("[translate] auto_translate: trying model=%s", model)

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 2048,
            "temperature": 0.0,
        }

        try:
            start = time.monotonic()
            async with httpx.AsyncClient(timeout=TRANSLATION_TIMEOUT) as client:
                resp = await client.post(
                    f"{OPENROUTER_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                elapsed_ms = int((time.monotonic() - start) * 1000)
                logger.info("[translate] auto_translate: model=%s status=%d in %dms", model, resp.status_code, elapsed_ms)

                if resp.status_code == 429:
                    logger.warning("[translate] auto_translate: rate limited on model=%s, trying next", model)
                    last_error = "Too many requests. Try again later."
                    continue

                if resp.status_code != 200:
                    error_text = resp.text[:500]
                    logger.warning("[translate] auto_translate: model=%s failed with status=%d: %s", model, resp.status_code, error_text)
                    last_error = f"Translation failed with status {resp.status_code}"
                    continue

                data = resp.json()

                if "error" in data:
                    error_msg = data["error"].get("message", "Unknown error")
                    logger.warning("[translate] auto_translate: model=%s API error: %s, trying next", model, error_msg)
                    last_error = error_msg
                    continue

                if "choices" not in data or not data["choices"]:
                    logger.warning("[translate] auto_translate: model=%s returned empty choices, trying next", model)
                    last_error = "Empty response from AI"
                    continue

            translated = data["choices"][0]["message"]["content"].strip()
            logger.info("[translate] auto_translate: model=%s result_len=%d", model, len(translated))
            return translated

        except httpx.TimeoutException:
            logger.warning("[translate] auto_translate: model=%s timed out, trying next", model)
            last_error = "AI service timed out"
            continue
        except Exception as e:
            logger.warning("[translate] auto_translate: model=%s failed: %s, trying next", model, e)
            last_error = str(e)
            continue

    logger.warning("[translate] auto_translate: all models failed, last_error=%s", last_error)
    return None


@dataclass
class VerseAnalysis:
    wordByWordMeaning: str
    fullMeaning: str
    simplifiedMeaning: str


async def analyze_verse(text: str, target_lang: str = "si") -> VerseAnalysis | None:
    api_key = settings.openrouter_api_key
    if not api_key:
        logger.warning("[translate] analyze_verse: OpenRouter API key not configured")
        return None

    system_message = (
        "You are a Sanskrit verse analysis engine for translators. "
        "Output strict JSON only, no markdown fences, no commentary."
    )
    prompt = (
        f"Analyze the following Sanskrit verse (given in Devanagari and/or IAST) and respond in {target_lang}. "
        "Return a single JSON object with exactly these three string keys:\n"
        '- "wordByWordMeaning": a markdown table breaking the verse into individual words/phrases, '
        f"each with its meaning in {target_lang} (columns: Sanskrit word, meaning)\n"
        f'- "fullMeaning": the complete, faithful meaning of the verse in {target_lang}\n'
        f'- "simplifiedMeaning": the same meaning restated in simpler, more accessible {target_lang}\n\n'
        f"Verse:\n{text}\n\n"
        "Respond with only the JSON object."
    )

    last_error = None
    for model in TRANSLATION_MODELS:
        logger.info("[translate] analyze_verse: trying model=%s", model)

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 8192,
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
        }

        try:
            start = time.monotonic()
            async with httpx.AsyncClient(timeout=ANALYSIS_TIMEOUT) as client:
                resp = await client.post(
                    f"{OPENROUTER_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                elapsed_ms = int((time.monotonic() - start) * 1000)
                logger.info("[translate] analyze_verse: model=%s status=%d in %dms", model, resp.status_code, elapsed_ms)

                if resp.status_code == 429:
                    logger.warning("[translate] analyze_verse: rate limited on model=%s, trying next", model)
                    last_error = "Too many requests. Try again later."
                    continue

                if resp.status_code != 200:
                    error_text = resp.text[:500]
                    logger.warning("[translate] analyze_verse: model=%s failed with status=%d: %s", model, resp.status_code, error_text)
                    last_error = f"Analysis failed with status {resp.status_code}"
                    continue

                data = resp.json()

                if "error" in data:
                    error_msg = data["error"].get("message", "Unknown error")
                    logger.warning("[translate] analyze_verse: model=%s API error: %s, trying next", model, error_msg)
                    last_error = error_msg
                    continue

                if "choices" not in data or not data["choices"]:
                    logger.warning("[translate] analyze_verse: model=%s returned empty choices, trying next", model)
                    last_error = "Empty response from AI"
                    continue

            content = data["choices"][0]["message"]["content"].strip()

            try:
                parsed = json.loads(content)
                result = VerseAnalysis(
                    wordByWordMeaning=parsed["wordByWordMeaning"],
                    fullMeaning=parsed["fullMeaning"],
                    simplifiedMeaning=parsed["simplifiedMeaning"],
                )
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning("[translate] analyze_verse: model=%s returned unparseable JSON: %s, trying next", model, e)
                last_error = "AI returned an unexpected response format"
                continue

            logger.info("[translate] analyze_verse: model=%s succeeded", model)
            return result

        except httpx.TimeoutException:
            logger.warning("[translate] analyze_verse: model=%s timed out, trying next", model)
            last_error = "AI service timed out"
            continue
        except Exception as e:
            logger.warning("[translate] analyze_verse: model=%s failed: %s, trying next", model, e)
            last_error = str(e)
            continue

    logger.warning("[translate] analyze_verse: all models failed, last_error=%s", last_error)
    return None
