import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


async def log_model_usage(
    db,
    *,
    call_type: str,
    section_id: str | None,
    model: str | None,
    status: str,
    latency_ms: int,
    book_id: str | None = None,
    attempts: list[dict] | None = None,
    usage: dict | None = None,
    error: str | None = None,
    input_summary: dict | None = None,
    output_summary: dict | None = None,
    direction: str | None = None,
) -> None:
    """Best-effort append-only audit log of one AI model call.

    Never raises: logging must not break the underlying AI call. This is a
    separate, additive log for cross-feature model observability — it does
    not replace ai_text_extractions/transliterations, which remain the
    upsert-per-section source of truth for the app UI.
    """
    if db is None:
        return
    try:
        await db.model_usage.insert_one({
            "callType": call_type,
            "direction": direction,
            "sectionId": section_id,
            "bookId": book_id,
            "model": model,
            "status": status,
            "latencyMs": latency_ms,
            "attempts": attempts or [],
            "usage": usage,
            "error": error,
            "inputSummary": input_summary or {},
            "outputSummary": output_summary or {},
            "createdAt": datetime.now(timezone.utc),
        })
    except Exception as e:
        logger.warning(
            "[model_usage] log_model_usage failed for callType=%s sectionId=%s: %s",
            call_type, section_id, e,
        )
