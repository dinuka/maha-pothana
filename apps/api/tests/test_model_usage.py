import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.model_usage import log_model_usage


@pytest.mark.asyncio
async def test_log_model_usage_inserts_expected_shape():
    db = MagicMock()
    db.model_usage.insert_one = AsyncMock()

    await log_model_usage(
        db,
        call_type="extraction",
        section_id="sec-1",
        book_id="book-1",
        model="model-a",
        status="success",
        latency_ms=123,
        attempts=[{"model": "model-a", "outcome": "success", "error": None, "elapsedMs": 100}],
        usage={"total_tokens": 42},
        input_summary={"imageBytes": 1024},
        output_summary={"confidence": 0.9},
    )

    db.model_usage.insert_one.assert_awaited_once()
    doc = db.model_usage.insert_one.call_args.args[0]
    assert doc["callType"] == "extraction"
    assert doc["sectionId"] == "sec-1"
    assert doc["bookId"] == "book-1"
    assert doc["model"] == "model-a"
    assert doc["status"] == "success"
    assert doc["latencyMs"] == 123
    assert doc["usage"] == {"total_tokens": 42}
    assert doc["inputSummary"] == {"imageBytes": 1024}
    assert doc["outputSummary"] == {"confidence": 0.9}
    assert "createdAt" in doc


@pytest.mark.asyncio
async def test_log_model_usage_noop_when_db_is_none():
    # Should not raise even though there's nothing to write to.
    await log_model_usage(
        None,
        call_type="extraction",
        section_id="sec-1",
        model="model-a",
        status="success",
        latency_ms=1,
    )


@pytest.mark.asyncio
async def test_log_model_usage_swallows_insert_failure():
    db = MagicMock()
    db.model_usage.insert_one = AsyncMock(side_effect=Exception("mongo down"))

    # Must not raise: logging must never break the underlying AI call.
    await log_model_usage(
        db,
        call_type="extraction",
        section_id="sec-1",
        model="model-a",
        status="success",
        latency_ms=1,
    )


@pytest.mark.asyncio
async def test_extract_text_logs_failed_row_before_raising():
    """The most important row for the AI engineer is the failure row — it
    must be written even though extract_text raises immediately after."""
    from app.services.ai_text import extract_text

    db = MagicMock()
    db.model_usage.insert_one = AsyncMock()

    with patch("app.services.ai_text.settings.openrouter_api_key", "test-key"):
        with patch(
            "app.services.ai_text.call_openrouter",
            new=AsyncMock(return_value=(None, None, "All extraction models failed")),
        ):
            with pytest.raises(ValueError):
                await extract_text(b"fake-image-bytes", db=db, section_id="sec-1")

    db.model_usage.insert_one.assert_awaited_once()
    doc = db.model_usage.insert_one.call_args.args[0]
    assert doc["callType"] == "extraction"
    assert doc["sectionId"] == "sec-1"
    assert doc["status"] == "failed"
    assert doc["error"] == "All extraction models failed"
