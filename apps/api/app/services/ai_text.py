import time
import logging
from dataclasses import dataclass, field

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

EXTRACTION_MODELS = settings.openrouter_extraction_models
EXTRACTION_MODEL = EXTRACTION_MODELS[0]
TRANSLITERATION_MODELS = settings.openrouter_transliteration_models
TRANSLITERATION_MODEL = TRANSLITERATION_MODELS[0]
CONFIDENCE_MODEL = settings.openrouter_confidence_model
EXTRACTION_TIMEOUT = 60
CONFIDENCE_TIMEOUT = 30
TRANSLITERATION_TIMEOUT = 120
SANSKRIT_SCRIPTS = frozenset({"sa", "sa-Latn"})
COST_PER_EXTRACTION = 0.007
COST_PER_CONFIDENCE = 0.001
COST_PER_TRANSLITERATION = 0.001
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def strip_reasoning(text: str) -> str:
    """Some reasoning-tuned models emit their chain-of-thought directly in the
    message content (e.g. wrapped in <think>...</think>) instead of a separate
    reasoning field. Strip that out so only the final answer is used."""
    import re

    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<thinking>.*?</thinking>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    return cleaned.strip()


@dataclass
class AITextResult:
    text: str
    confidence: float
    model: str
    processing_time_ms: int
    raw_response: dict | None = None


@dataclass
class TransliterationResult:
    transliterated_text: str
    source_script: str
    target_script: str
    confidence: float
    model: str
    raw_response: dict | None = None


@dataclass
class ExtractionConfig:
    model: str = EXTRACTION_MODEL
    confidence_threshold: float = 0.7
    max_concurrent: int = 5
    cost_limit_per_book: float = 5.0
    enabled: bool = True


async def _get_model_config(db=None) -> ExtractionConfig:
    if db is None:
        return ExtractionConfig()
    try:
        doc = await db.system_config.find_one({"key": "extraction_config"})
        if doc:
            return ExtractionConfig(
                model=doc.get("model", EXTRACTION_MODEL),
                confidence_threshold=doc.get("confidenceThreshold", 0.7),
                max_concurrent=doc.get("maxConcurrent", 5),
                cost_limit_per_book=doc.get("costLimitPerBook", 5.0),
                enabled=doc.get("enabled", True),
            )
    except Exception:
        logger.warning("Failed to load extraction config from DB, using defaults")
    return ExtractionConfig()


async def extract_text(image_data: bytes, db=None) -> AITextResult:
    api_key = settings.openrouter_api_key
    if not api_key:
        raise ValueError("OpenRouter API key not configured")

    import base64
    b64_image = base64.b64encode(image_data).decode("utf-8")

    prompt = (
        "You are an expert OCR system for Indic scripts. "
        "Extract ALL text from this image. "
        "Return ONLY the extracted text, preserving line breaks. "
        "Do not add any explanation. "
        "If the image contains no text, return exactly: [NO_TEXT]"
    )

    last_error = None
    models_to_try = EXTRACTION_MODELS[:]

    for model in models_to_try:
        logger.info("[ai_text] extract_text: trying model=%s, image_size=%d bytes", model, len(image_data))

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{b64_image}",
                                "detail": "high",
                            },
                        },
                    ],
                }
            ],
            "max_tokens": 1024,
            "reasoning": {"exclude": True},
        }

        try:
            logger.info("[ai_text] extract_text: calling OpenRouter API at %s/chat/completions", OPENROUTER_BASE_URL)
            start = time.monotonic()
            async with httpx.AsyncClient(timeout=EXTRACTION_TIMEOUT) as client:
                resp = await client.post(
                    f"{OPENROUTER_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                logger.info("[ai_text] extract_text: response status=%d for model=%s", resp.status_code, model)

                if resp.status_code == 429:
                    logger.warning("[ai_text] extract_text: rate limited on model=%s, trying next", model)
                    last_error = "Too many requests. Try again later."
                    continue

                if resp.status_code != 200:
                    error_text = resp.text[:500]
                    logger.warning("[ai_text] extract_text: model=%s failed with status=%d: %s", model, resp.status_code, error_text)
                    last_error = f"Extraction failed with status {resp.status_code}"
                    continue

                data = resp.json()
                if "choices" not in data or not data["choices"]:
                    logger.warning("[ai_text] extract_text: model=%s returned empty choices, trying next", model)
                    last_error = "Empty response from AI"
                    continue

            elapsed_ms = int((time.monotonic() - start) * 1000)
            extracted_text = strip_reasoning(data["choices"][0]["message"]["content"])
            logger.info("[ai_text] extract_text: model=%s extracted %d chars in %dms", model, len(extracted_text), elapsed_ms)

            if extracted_text == "[NO_TEXT]":
                return AITextResult(
                    text="",
                    confidence=0.0,
                    model=model,
                    processing_time_ms=elapsed_ms,
                    raw_response=data,
                )

            confidence = await _score_confidence(extracted_text, model, api_key)

            return AITextResult(
                text=extracted_text,
                confidence=confidence,
                model=model,
                processing_time_ms=elapsed_ms,
                raw_response=data,
            )

        except httpx.TimeoutException:
            logger.warning("[ai_text] extract_text: model=%s timed out, trying next", model)
            last_error = "AI service timed out"
            continue
        except Exception as e:
            logger.warning("[ai_text] extract_text: model=%s failed: %s, trying next", model, e)
            last_error = str(e)
            continue

    raise ValueError(last_error or "All extraction models failed")


async def _score_confidence(extracted_text: str, model: str, api_key: str) -> float:
    prompt = (
        "Rate the quality of this OCR extraction on a scale of 0.0 to 1.0. "
        "Consider: character accuracy, completeness, script correctness. "
        "Return ONLY a number between 0.0 and 1.0.\n\n"
        f"Image text: {extracted_text}"
    )

    payload = {
        "model": CONFIDENCE_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 10,
        "temperature": 0.0,
        "reasoning": {"exclude": True},
    }

    try:
        logger.info("[ai_text] _score_confidence: calling OpenRouter for confidence scoring")
        async with httpx.AsyncClient(timeout=CONFIDENCE_TIMEOUT) as client:
            resp = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            logger.info("[ai_text] _score_confidence: response status=%d", resp.status_code)
            resp.raise_for_status()

        data = resp.json()
        if "choices" not in data or not data["choices"]:
            logger.warning("[ai_text] _score_confidence: no choices in response")
            return 0.5

        score_text = strip_reasoning(data["choices"][0]["message"]["content"])
        score = max(0.0, min(1.0, float(score_text)))
        logger.info("[ai_text] _score_confidence: score=%s", score)
        return score
    except Exception as e:
        logger.warning("[ai_text] _score_confidence failed: %s, defaulting to 0.5", e)
        return 0.5


async def transliterate_text(
    source_text: str,
    source_script: str,
    target_script: str,
    db=None,
) -> TransliterationResult:
    api_key = settings.openrouter_api_key
    if not api_key:
        raise ValueError("OpenRouter API key not configured")

    logger.info("[ai_text] transliterate_text: source_script=%s, target_script=%s, text_len=%d",
                source_script, target_script, len(source_text))

    is_sanskrit = source_script in SANSKRIT_SCRIPTS

    if is_sanskrit:
        system_message = "You are a Sanskrit transliteration engine. Output only Sinhala script, nothing else."
        prompt = (
            "Convert Sanskrit text written in either:\n\n"
            "- Devanagari\n"
            "- IAST\n\n"
            f"into {target_script} script.\n\n"
            "Rules:\n"
            "- Preserve pronunciation exactly.\n"
            "- Do NOT translate the meaning.\n"
            f"- Output only {target_script} script.\n"
            "- Preserve punctuation.\n"
            "- Preserve spaces.\n"
            "- Preserve visarga, anusvara, chandrabindu, and conjunct consonants.\n"
            f"- Use standard {target_script} transliteration conventions.\n\n"
            "Examples:\n\n"
            "धर्मः\n"
            "→ ධර්මඃ\n\n"
            "कृष्णः\n"
            "→ කෘෂ්ණඃ\n\n"
            "śrī\n"
            "→ ශ්‍රී\n\n"
            "jñāna\n"
            "→ ඥාන\n\n"
            f"Input:\n{source_text}\n\n"
            "Only output the Sinhala transliteration."
        )
    else:
        system_message = "You are a script transliteration engine. Output only the transliterated text, nothing else."
        prompt = (
            f"Transliterate the following {source_script} text into {target_script} script.\n"
            "Rules:\n"
            "1. Perform letter-for-letter script conversion only\n"
            "2. Do NOT translate\n"
            "3. Do NOT explain your work\n"
            "4. Return ONLY the final transliterated text\n\n"
            f"Input: {source_text}\n\n"
            "Output:"
        )

    last_error = None
    models_to_try = TRANSLITERATION_MODELS[:]

    for model in models_to_try:
        logger.info("[ai_text] transliterate_text: trying model=%s", model)

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 1024,
            "temperature": 0.0,
            "reasoning": {"exclude": True},
        }

        try:
            logger.info("[ai_text] transliterate_text: calling OpenRouter API with model=%s", model)
            start = time.monotonic()
            async with httpx.AsyncClient(timeout=TRANSLITERATION_TIMEOUT) as client:
                resp = await client.post(
                    f"{OPENROUTER_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                elapsed_ms = int((time.monotonic() - start) * 1000)
                logger.info("[ai_text] transliterate_text: model=%s status=%d in %dms", model, resp.status_code, elapsed_ms)

                if resp.status_code == 429:
                    logger.warning("[ai_text] transliterate_text: rate limited on model=%s, trying next", model)
                    last_error = "Too many requests. Try again later."
                    continue

                if resp.status_code != 200:
                    error_text = resp.text[:500]
                    logger.warning("[ai_text] transliterate_text: model=%s failed with status=%d: %s", model, resp.status_code, error_text)
                    error_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                    last_error = error_data.get("error", {}).get("message", f"API error {resp.status_code}")
                    continue

                data = resp.json()

                if "error" in data:
                    error_msg = data["error"].get("message", "Unknown error")
                    logger.warning("[ai_text] transliterate_text: model=%s API error: %s, trying next", model, error_msg)
                    last_error = error_msg
                    continue

                if "choices" not in data or not data["choices"]:
                    logger.warning("[ai_text] transliterate_text: model=%s returned empty choices, trying next", model)
                    last_error = "Empty response from AI"
                    continue

            transliterated = strip_reasoning(data["choices"][0]["message"]["content"])
            logger.info("[ai_text] transliterate_text: model=%s result_len=%d", model, len(transliterated))

            return TransliterationResult(
                transliterated_text=transliterated,
                source_script=source_script,
                target_script=target_script,
                confidence=0.9,
                model=model,
                raw_response=data,
            )

        except httpx.TimeoutException:
            logger.warning("[ai_text] transliterate_text: model=%s timed out, trying next", model)
            last_error = "AI service timed out"
            continue
        except Exception as e:
            logger.warning("[ai_text] transliterate_text: model=%s failed: %s, trying next", model, e)
            last_error = str(e)
            continue

    raise ValueError(last_error or "All transliteration models failed")


def estimate_extraction_cost(section_count: int) -> float:
    return section_count * COST_PER_EXTRACTION


async def reverse_transliterate_text(
    transliterated_text: str,
    source_script: str,
    target_script: str,
    db=None,
) -> TransliterationResult:
    api_key = settings.openrouter_api_key
    if not api_key:
        raise ValueError("OpenRouter API key not configured")

    logger.info("[ai_text] reverse_transliterate_text: source_script=%s, target_script=%s, text_len=%d",
                source_script, target_script, len(transliterated_text))

    is_sanskrit = target_script in SANSKRIT_SCRIPTS

    if is_sanskrit:
        system_message = f"You are a Sanskrit transliteration engine. Convert Sinhala back to Sanskrit ({target_script}). Output only the result."
        prompt = (
            f"Reverse the following Sinhala transliteration back to original Sanskrit text.\n\n"
            "Rules:\n"
            "- Preserve pronunciation exactly.\n"
            "- Do NOT translate the meaning.\n"
            "- Output only the original script (Devanagari or IAST).\n"
            "- Preserve punctuation.\n"
            "- Preserve spaces.\n"
            "- Preserve visarga, anusvara, chandrabindu, and conjunct consonants.\n"
            "- Sinhala anusvara (ං, binduva) MUST map to Devanagari anusvara (ं), never to म् (virama-ma). "
            "Do NOT normalize anusvara into its nasal consonant equivalent (e.g. කලං -> कलं, NOT कलम्).\n"
            "- Do NOT apply grammatical correction or standardization; reproduce the exact orthography implied by the input.\n\n"
            "Examples:\n\n"
            "ධර්මඃ\n"
            "→ धर्मः\n\n"
            "කෘෂ්ණඃ\n"
            "→ कृष्णः\n\n"
            "කලං\n"
            "→ कलं\n\n"
            f"Input:\n{transliterated_text}\n\n"
            "Output:"
        )
    else:
        system_message = f"You are a script transliteration engine. Convert {source_script} back to {target_script}. Output only the result."
        prompt = (
            f"Reverse the following {source_script} transliteration back to {target_script} script.\n"
            "Rules:\n"
            "1. Perform letter-for-letter script conversion only\n"
            "2. Do NOT translate\n"
            "3. Do NOT explain your work\n"
            f"4. Return ONLY the original {target_script} text\n\n"
            f"Input: {transliterated_text}\n\n"
            "Output:"
        )

    last_error = None
    models_to_try = TRANSLITERATION_MODELS[:]

    for model in models_to_try:
        logger.info("[ai_text] reverse_transliterate_text: trying model=%s", model)

        payload = {
            "model": model,
            "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
            ],
            "max_tokens": 1024,
            "temperature": 0.0,
            "reasoning": {"exclude": True},
        }

        try:
            logger.info("[ai_text] reverse_transliterate_text: calling OpenRouter API with model=%s", model)
            start = time.monotonic()
            async with httpx.AsyncClient(timeout=TRANSLITERATION_TIMEOUT) as client:
                resp = await client.post(
                    f"{OPENROUTER_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                elapsed_ms = int((time.monotonic() - start) * 1000)
                logger.info("[ai_text] reverse_transliterate_text: model=%s status=%d in %dms", model, resp.status_code, elapsed_ms)

                if resp.status_code == 429:
                    logger.warning("[ai_text] reverse_transliterate_text: rate limited on model=%s, trying next", model)
                    last_error = "Too many requests. Try again later."
                    continue

                if resp.status_code != 200:
                    error_text = resp.text[:500]
                    logger.warning("[ai_text] reverse_transliterate_text: model=%s failed with status=%d: %s", model, resp.status_code, error_text)
                    error_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                    last_error = error_data.get("error", {}).get("message", f"API error {resp.status_code}")
                    continue

                data = resp.json()

                if "error" in data:
                    error_msg = data["error"].get("message", "Unknown error")
                    logger.warning("[ai_text] reverse_transliterate_text: model=%s API error: %s, trying next", model, error_msg)
                    last_error = error_msg
                    continue

                if "choices" not in data or not data["choices"]:
                    logger.warning("[ai_text] reverse_transliterate_text: model=%s returned empty choices, trying next", model)
                    last_error = "Empty response from AI"
                    continue

            original_text = strip_reasoning(data["choices"][0]["message"]["content"])
            logger.info("[ai_text] reverse_transliterate_text: model=%s result_len=%d", model, len(original_text))

            return TransliterationResult(
                transliterated_text=original_text,
                source_script=source_script,
                target_script=target_script,
                confidence=0.9,
                model=model,
                raw_response=data,
            )

        except httpx.TimeoutException:
            logger.warning("[ai_text] reverse_transliterate_text: model=%s timed out, trying next", model)
            last_error = "AI service timed out"
            continue
        except Exception as e:
            logger.warning("[ai_text] reverse_transliterate_text: model=%s failed: %s, trying next", model, e)
            last_error = str(e)
            continue

    raise ValueError(last_error or "All reverse transliteration models failed")
