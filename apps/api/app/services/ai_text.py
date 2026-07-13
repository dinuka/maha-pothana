import re
import time
import logging
from dataclasses import dataclass, field

from app.config import settings
from app.services.model_usage import log_model_usage
from app.services.openrouter import call_openrouter

logger = logging.getLogger(__name__)

EXTRACTION_MODELS = settings.openrouter_extraction_models
EXTRACTION_MODEL = EXTRACTION_MODELS[0]
TRANSLITERATION_MODELS = settings.openrouter_transliteration_models
TRANSLITERATION_MODEL = TRANSLITERATION_MODELS[0]
CONFIDENCE_MODELS = settings.openrouter_confidence_models
EXTRACTION_TIMEOUT = 60
CONFIDENCE_TIMEOUT = 30
TRANSLITERATION_TIMEOUT = 120
SANSKRIT_SCRIPTS = frozenset({"sa", "sa-Latn"})
COST_PER_EXTRACTION = 0.007
COST_PER_CONFIDENCE = 0.001
COST_PER_TRANSLITERATION = 0.001


def strip_reasoning(text: str) -> str:
    """Some reasoning-tuned models emit their chain-of-thought directly in the
    message content (e.g. wrapped in <think>...</think>) instead of a separate
    reasoning field. Strip that out so only the final answer is used."""
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


async def extract_text(image_data: bytes, db=None, section_id: str | None = None) -> AITextResult:
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

    def build_payload(model: str) -> dict:
        return {
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

    start = time.monotonic()
    attempts: list[dict] = []
    data, model, error = await call_openrouter(
        EXTRACTION_MODELS, build_payload, EXTRACTION_TIMEOUT, attempts=attempts
    )
    elapsed_ms = int((time.monotonic() - start) * 1000)

    await log_model_usage(
        db,
        call_type="extraction",
        section_id=section_id,
        model=model,
        status="success" if data else "failed",
        latency_ms=elapsed_ms,
        attempts=attempts,
        usage=(data or {}).get("usage"),
        error=error,
        input_summary={"imageBytes": len(image_data)},
    )

    if data is None:
        raise ValueError(error or "All extraction models failed")

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

    confidence = await _score_confidence(extracted_text, model, api_key, db=db, section_id=section_id)

    return AITextResult(
        text=extracted_text,
        confidence=confidence,
        model=model,
        processing_time_ms=elapsed_ms,
        raw_response=data,
    )


_SCORE_PATTERN = re.compile(r"(?<![\d.])(?:0(?:\.\d+)?|1(?:\.0+)?)(?![\d.])")


def _parse_score(text: str) -> float | None:
    """Pull the first standalone 0.0-1.0 number out of a model response.

    Reasoning models sometimes ignore `reasoning: {exclude: True}` and emit
    their chain-of-thought as plain prose in the message content (no
    <think> tags for strip_reasoning to remove), e.g. "The user wants me to
    rate the quality of an...". A bare float() on that raises ValueError, so
    instead we search for the score itself anywhere in the text.
    """
    match = _SCORE_PATTERN.search(text)
    if match is None:
        return None
    return max(0.0, min(1.0, float(match.group())))


def _validate_confidence_response(data: dict) -> bool:
    content = data["choices"][0].get("message", {}).get("content", "")
    return _parse_score(strip_reasoning(content)) is not None


async def _score_confidence(
    extracted_text: str, model: str, api_key: str, db=None, section_id: str | None = None
) -> float:
    prompt = (
        "Rate the quality of this OCR extraction on a scale of 0.0 to 1.0. "
        "Consider: character accuracy, completeness, script correctness. "
        "Return ONLY a number between 0.0 and 1.0.\n\n"
        f"Image text: {extracted_text}"
    )

    def build_payload(confidence_model: str) -> dict:
        return {
            "model": confidence_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 10,
            "temperature": 0.2,
            "reasoning": {"exclude": True},
        }

    logger.info("[ai_text] _score_confidence: calling OpenRouter for confidence scoring")
    start = time.monotonic()
    attempts: list[dict] = []
    data, used_model, error = await call_openrouter(
        CONFIDENCE_MODELS, build_payload, CONFIDENCE_TIMEOUT, validate=_validate_confidence_response, attempts=attempts
    )
    elapsed_ms = int((time.monotonic() - start) * 1000)

    if data is None:
        logger.warning("[ai_text] _score_confidence failed: %s, defaulting to 0.5", error)
        await log_model_usage(
            db,
            call_type="confidence",
            section_id=section_id,
            model=used_model,
            status="failed",
            latency_ms=elapsed_ms,
            attempts=attempts,
            error=error,
            input_summary={"textLength": len(extracted_text)},
        )
        return 0.5

    score_text = strip_reasoning(data["choices"][0]["message"]["content"])
    score = _parse_score(score_text)
    if score is None:
        logger.warning("[ai_text] _score_confidence: unparseable score from model=%s, defaulting to 0.5", used_model)
        await log_model_usage(
            db,
            call_type="confidence",
            section_id=section_id,
            model=used_model,
            status="failed",
            latency_ms=elapsed_ms,
            attempts=attempts,
            usage=data.get("usage"),
            error="unparseable score",
            input_summary={"textLength": len(extracted_text)},
        )
        return 0.5

    logger.info("[ai_text] _score_confidence: model=%s score=%s", used_model, score)
    await log_model_usage(
        db,
        call_type="confidence",
        section_id=section_id,
        model=used_model,
        status="success",
        latency_ms=elapsed_ms,
        attempts=attempts,
        usage=data.get("usage"),
        input_summary={"textLength": len(extracted_text)},
        output_summary={"confidence": score},
    )
    return score


async def transliterate_text(
    source_text: str,
    source_script: str,
    target_script: str,
    db=None,
    section_id: str | None = None,
    book_id: str | None = None,
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

    def build_payload(model: str) -> dict:
        return {
            "model": model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 1024,
            "temperature": 0.2,
            "reasoning": {"exclude": True},
        }

    start = time.monotonic()
    attempts: list[dict] = []
    data, model, error = await call_openrouter(
        TRANSLITERATION_MODELS, build_payload, TRANSLITERATION_TIMEOUT, attempts=attempts
    )
    elapsed_ms = int((time.monotonic() - start) * 1000)

    await log_model_usage(
        db,
        call_type="transliteration",
        direction="forward",
        section_id=section_id,
        book_id=book_id,
        model=model,
        status="success" if data else "failed",
        latency_ms=elapsed_ms,
        attempts=attempts,
        usage=(data or {}).get("usage"),
        error=error,
        input_summary={"textLength": len(source_text), "sourceScript": source_script, "targetScript": target_script},
    )

    if data is None:
        raise ValueError(error or "All transliteration models failed")

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


def estimate_extraction_cost(section_count: int) -> float:
    return section_count * COST_PER_EXTRACTION


async def reverse_transliterate_text(
    transliterated_text: str,
    source_script: str,
    target_script: str,
    db=None,
    section_id: str | None = None,
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

    def build_payload(model: str) -> dict:
        return {
            "model": model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 1024,
            "temperature": 0.2,
            "reasoning": {"exclude": True},
        }

    start = time.monotonic()
    attempts: list[dict] = []
    data, model, error = await call_openrouter(
        TRANSLITERATION_MODELS, build_payload, TRANSLITERATION_TIMEOUT, attempts=attempts
    )
    elapsed_ms = int((time.monotonic() - start) * 1000)

    await log_model_usage(
        db,
        call_type="transliteration",
        direction="reverse",
        section_id=section_id,
        model=model,
        status="success" if data else "failed",
        latency_ms=elapsed_ms,
        attempts=attempts,
        usage=(data or {}).get("usage"),
        error=error,
        input_summary={"textLength": len(transliterated_text), "sourceScript": source_script, "targetScript": target_script},
    )

    if data is None:
        raise ValueError(error or "All reverse transliteration models failed")

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
