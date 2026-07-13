import json
import logging
import re
import time
from dataclasses import dataclass

from app.config import settings
from app.services.ai_text import strip_reasoning
from app.services.model_usage import log_model_usage
from app.services.openrouter import call_openrouter

logger = logging.getLogger(__name__)

TRANSLATION_MODELS = settings.openrouter_translation_models
TRANSLATION_TIMEOUT = 60
ANALYSIS_TIMEOUT = 90

DEVANAGARI_RE = re.compile(r"[ऀ-ॿ]")
SINHALA_RE = re.compile(r"[඀-෿]")
LATIN_RE = re.compile(r"[A-Za-zÀ-ɏḀ-ỿ]")
PAREN_RE = re.compile(r"\(([^()]*)\)")

VERSE_WORD_HEADER = "සංස්කෘත වචනය"
VERSE_MEANING_HEADER = "අර්ථය"


def _parse_markdown_table(markdown: str) -> tuple[list[str], list[list[str]]] | None:
    lines = [line.strip() for line in markdown.strip().split("\n") if line.strip()]
    if len(lines) < 2:
        return None

    def split_row(line: str) -> list[str]:
        return [cell.strip() for cell in line.strip("|").split("|")]

    headers = split_row(lines[0])
    rows = [split_row(line) for line in lines[2:]]
    return headers, rows


def _is_valid_verse_table(markdown: str) -> bool:
    parsed = _parse_markdown_table(markdown)
    if parsed is None:
        return False
    headers, rows = parsed

    if len(headers) != 2:
        return False
    if headers[0] != VERSE_WORD_HEADER or headers[1] != VERSE_MEANING_HEADER:
        return False
    if not rows:
        return False

    for row in rows:
        if len(row) != 2:
            return False
        word_cell, meaning_cell = row
        if not word_cell or not meaning_cell:
            return False
        if LATIN_RE.search(word_cell) or LATIN_RE.search(meaning_cell):
            return False
        if not SINHALA_RE.search(meaning_cell):
            return False

        paren_match = PAREN_RE.search(word_cell)
        if paren_match is None:
            return False
        devanagari_part = word_cell[: paren_match.start()].strip()
        transliteration_part = paren_match.group(1).strip()
        if not DEVANAGARI_RE.search(devanagari_part):
            return False
        if not transliteration_part or not SINHALA_RE.search(transliteration_part):
            return False
        if DEVANAGARI_RE.search(transliteration_part):
            return False

    return True


async def auto_translate(
    text: str,
    source_lang: str = "auto",
    target_lang: str = "en",
    db=None,
    section_id: str | None = None,
    book_id: str | None = None,
) -> str | None:
    if not settings.openrouter_api_key:
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

    def build_payload(model: str) -> dict:
        return {
            "model": model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 2048,
            "temperature": 0.0,
            "reasoning": {"exclude": True},
        }

    start = time.monotonic()
    attempts: list[dict] = []
    data, model, error = await call_openrouter(
        TRANSLATION_MODELS, build_payload, TRANSLATION_TIMEOUT, attempts=attempts
    )
    elapsed_ms = int((time.monotonic() - start) * 1000)

    if data is None:
        logger.warning("[translate] auto_translate: all models failed, last_error=%s", error)
        await log_model_usage(
            db,
            call_type="auto_translate",
            section_id=section_id,
            book_id=book_id,
            model=model,
            status="failed",
            latency_ms=elapsed_ms,
            attempts=attempts,
            error=error,
            input_summary={"textLength": len(text), "sourceLang": source_lang, "targetLang": target_lang},
        )
        return None

    translated = strip_reasoning(data["choices"][0]["message"]["content"])
    logger.info("[translate] auto_translate: model=%s result_len=%d", model, len(translated))
    await log_model_usage(
        db,
        call_type="auto_translate",
        section_id=section_id,
        book_id=book_id,
        model=model,
        status="success",
        latency_ms=elapsed_ms,
        attempts=attempts,
        usage=data.get("usage"),
        input_summary={"textLength": len(text), "sourceLang": source_lang, "targetLang": target_lang},
        output_summary={"textLength": len(translated), "preview": translated[:200]},
    )
    return translated


@dataclass
class VerseAnalysis:
    wordByWordMeaning: str
    fullMeaning: str
    simplifiedMeaning: str


async def analyze_verse(
    text: str,
    target_lang: str = "si",
    db=None,
    section_id: str | None = None,
    book_id: str | None = None,
) -> VerseAnalysis | None:
    if not settings.openrouter_api_key:
        logger.warning("[translate] analyze_verse: OpenRouter API key not configured")
        return None

    system_message = (
        "You are a Sanskrit verse analysis engine for translators. "
        "Output strict JSON only, no markdown fences, no commentary."
    )
    prompt = (
        "Analyze the following Sanskrit verse (given in Devanagari and/or IAST). "
        "Return a single JSON object with exactly these three string keys:\n"
        '- "wordByWordMeaning": a markdown table breaking the verse into individual words, '
        f'with exactly these two column headers in this order: "{VERSE_WORD_HEADER}" and "{VERSE_MEANING_HEADER}".\n'
        f'  - "{VERSE_WORD_HEADER}" column: the word in Devanagari script, followed by its exact letter-by-letter '
        "transliteration into Sinhala script (not IAST, not romanized Latin) in parentheses. "
        "Examples: च (ච), राजः (රාජඃ)\n"
        f'  - "{VERSE_MEANING_HEADER}" column: the meaning of that word, written only in Sinhala script '
        "(no Devanagari, no Latin/English/IAST). Example: සහ\n"
        "  - Every cell must contain only Devanagari and/or Sinhala letters — never Latin, English, or "
        "romanized/IAST characters (e.g. never write rājaḥ, ča, or similar romanized forms).\n"
        f'- "fullMeaning": the complete, faithful meaning of the verse in {target_lang}\n'
        f'- "simplifiedMeaning": the same meaning restated in simpler, more accessible {target_lang}\n\n'
        f"Verse:\n{text}\n\n"
        "Respond with only the JSON object."
    )

    def build_payload(model: str) -> dict:
        return {
            "model": model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 8192,
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
            "reasoning": {"exclude": True},
        }

    def validate(data: dict) -> bool:
        try:
            content = strip_reasoning(data["choices"][0]["message"]["content"])
            parsed = json.loads(content)
            if not all(key in parsed for key in ("wordByWordMeaning", "fullMeaning", "simplifiedMeaning")):
                return False
            return _is_valid_verse_table(parsed["wordByWordMeaning"])
        except (json.JSONDecodeError, KeyError, TypeError, IndexError):
            return False

    start = time.monotonic()
    attempts: list[dict] = []
    data, model, error = await call_openrouter(
        TRANSLATION_MODELS, build_payload, ANALYSIS_TIMEOUT, validate=validate, attempts=attempts
    )
    elapsed_ms = int((time.monotonic() - start) * 1000)

    if data is None:
        logger.warning("[translate] analyze_verse: all models failed, last_error=%s", error)
        await log_model_usage(
            db,
            call_type="verse_analysis",
            section_id=section_id,
            book_id=book_id,
            model=model,
            status="failed",
            latency_ms=elapsed_ms,
            attempts=attempts,
            error=error,
            input_summary={"textLength": len(text), "targetLang": target_lang},
        )
        return None

    content = strip_reasoning(data["choices"][0]["message"]["content"])
    parsed = json.loads(content)
    result = VerseAnalysis(
        wordByWordMeaning=parsed["wordByWordMeaning"],
        fullMeaning=parsed["fullMeaning"],
        simplifiedMeaning=parsed["simplifiedMeaning"],
    )

    logger.info("[translate] analyze_verse: model=%s succeeded", model)
    await log_model_usage(
        db,
        call_type="verse_analysis",
        section_id=section_id,
        book_id=book_id,
        model=model,
        status="success",
        latency_ms=elapsed_ms,
        attempts=attempts,
        usage=data.get("usage"),
        input_summary={"textLength": len(text), "targetLang": target_lang},
        output_summary={"textLength": len(content)},
    )
    return result
