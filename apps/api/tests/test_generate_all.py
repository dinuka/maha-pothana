from datetime import datetime, timedelta, timezone

import pytest
from pymongo.errors import DuplicateKeyError
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.ai_text import AITextResult, TransliterationResult
from app.services.translate import VerseAnalysis
from app.tasks.generate_section_all import _generate_section_all


def _wire_fake_generation_runs_upsert(mock_db, section_id: str, initial: dict | None):
    """Simulates real Mongo semantics for the claim upsert in trigger_generate_all:
    matches the claim_filter's $or clauses against the current doc; on no match,
    raises DuplicateKeyError (mirroring the unique index on sectionId) instead of
    silently inserting a second doc. This exercises the actual filter logic rather
    than just mocking which branch the endpoint should take."""
    state: dict = dict(initial) if initial is not None else None

    async def fake_find_one_and_update(claim_filter, update, upsert=False):
        nonlocal state
        if state is not None:
            claimable = claim_filter["$or"][0]["status"]["$in"]
            stale_clause = claim_filter["$or"][1]
            stale_cutoff = stale_clause["updatedAt"]["$lt"]
            is_stale = (
                state.get("status") in stale_clause["status"]["$in"]
                and state.get("updatedAt", datetime.now(timezone.utc)) < stale_cutoff
            )
            matches = state.get("status") in claimable or is_stale
            if not matches:
                raise DuplicateKeyError("E11000 duplicate key error")
        state = {**(state or {}), **update["$set"]}
        if "sectionId" not in state:
            state["sectionId"] = section_id
        return state

    async def fake_find_one(_filter):
        return dict(state) if state is not None else None

    mock_db.generation_runs.find_one_and_update = AsyncMock(side_effect=fake_find_one_and_update)
    mock_db.generation_runs.find_one = AsyncMock(side_effect=fake_find_one)


@pytest.mark.asyncio
async def test_trigger_generate_all_dispatches_task(client, mock_db, sample_section):
    section = {**sample_section, "croppedImageKey": "books/x/sections/1.png"}
    mock_db.sections.find_one = AsyncMock(return_value=section)
    _wire_fake_generation_runs_upsert(mock_db, section["_id"], initial=None)

    mock_task = MagicMock()
    mock_task.id = "task-123"

    with patch("app.tasks.generate_section_all.generate_section_all.delay", return_value=mock_task):
        response = await client.post(
            f'/api/sections/{section["_id"]}/generate-all',
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "queued"
    assert data["taskId"] == "task-123"


@pytest.mark.asyncio
async def test_trigger_generate_all_section_not_found(client, mock_db):
    mock_db.sections.find_one = AsyncMock(return_value=None)

    response = await client.post(
        "/api/sections/507f1f77bcf86cd799439014/generate-all",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_trigger_generate_all_no_cropped_image(client, mock_db, sample_section):
    section = {**sample_section, "croppedImageKey": None, "aiExtractedText": None, "originalText": None}
    mock_db.sections.find_one = AsyncMock(return_value=section)

    response = await client.post(
        f'/api/sections/{section["_id"]}/generate-all',
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_trigger_generate_all_already_completed_skips_unless_forced(
    client, mock_db, sample_section
):
    section = {**sample_section, "croppedImageKey": "books/x/sections/1.png"}
    mock_db.sections.find_one = AsyncMock(return_value=section)
    _wire_fake_generation_runs_upsert(
        mock_db, section["_id"], initial={"sectionId": section["_id"], "status": "completed"}
    )

    response = await client.post(
        f'/api/sections/{section["_id"]}/generate-all',
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_trigger_generate_all_force_reruns_completed(client, mock_db, sample_section):
    section = {**sample_section, "croppedImageKey": "books/x/sections/1.png"}
    mock_db.sections.find_one = AsyncMock(return_value=section)
    _wire_fake_generation_runs_upsert(
        mock_db, section["_id"], initial={"sectionId": section["_id"], "status": "completed"}
    )

    mock_task = MagicMock()
    mock_task.id = "task-456"

    with patch("app.tasks.generate_section_all.generate_section_all.delay", return_value=mock_task):
        response = await client.post(
            f'/api/sections/{section["_id"]}/generate-all?force=true',
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 202
    assert response.json()["taskId"] == "task-456"


@pytest.mark.asyncio
async def test_trigger_generate_all_processing_run_returns_202_no_dispatch(
    client, mock_db, sample_section
):
    section = {**sample_section, "croppedImageKey": "books/x/sections/1.png"}
    mock_db.sections.find_one = AsyncMock(return_value=section)
    _wire_fake_generation_runs_upsert(
        mock_db,
        section["_id"],
        initial={
            "sectionId": section["_id"],
            "status": "processing",
            "updatedAt": datetime.now(timezone.utc),
        },
    )

    with patch("app.tasks.generate_section_all.generate_section_all.delay") as mock_delay:
        response = await client.post(
            f'/api/sections/{section["_id"]}/generate-all',
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 202
    assert response.json()["status"] == "processing"
    mock_delay.assert_not_called()


@pytest.mark.asyncio
async def test_trigger_generate_all_stale_processing_run_dispatches(
    client, mock_db, sample_section
):
    section = {**sample_section, "croppedImageKey": "books/x/sections/1.png"}
    mock_db.sections.find_one = AsyncMock(return_value=section)
    _wire_fake_generation_runs_upsert(
        mock_db,
        section["_id"],
        initial={
            "sectionId": section["_id"],
            "status": "processing",
            "updatedAt": datetime.now(timezone.utc) - timedelta(seconds=601),
        },
    )

    mock_task = MagicMock()
    mock_task.id = "task-789"

    with patch("app.tasks.generate_section_all.generate_section_all.delay", return_value=mock_task):
        response = await client.post(
            f'/api/sections/{section["_id"]}/generate-all',
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 202
    assert response.json()["taskId"] == "task-789"


@pytest.mark.asyncio
async def test_trigger_generate_all_force_does_not_reclaim_live_run(
    client, mock_db, sample_section
):
    section = {**sample_section, "croppedImageKey": "books/x/sections/1.png"}
    mock_db.sections.find_one = AsyncMock(return_value=section)
    _wire_fake_generation_runs_upsert(
        mock_db,
        section["_id"],
        initial={
            "sectionId": section["_id"],
            "status": "processing",
            "updatedAt": datetime.now(timezone.utc),
        },
    )

    with patch("app.tasks.generate_section_all.generate_section_all.delay") as mock_delay:
        response = await client.post(
            f'/api/sections/{section["_id"]}/generate-all?force=true',
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 202
    assert response.json()["status"] == "processing"
    mock_delay.assert_not_called()


@pytest.mark.asyncio
async def test_trigger_generate_all_fresh_processing_run_not_dispatched_even_though_marginally_old(
    client, mock_db, sample_section
):
    """Guards against a regression flipping $lt to $gt in the staleness clause:
    a processing run just under the staleness cutoff must still block dispatch."""
    section = {**sample_section, "croppedImageKey": "books/x/sections/1.png"}
    mock_db.sections.find_one = AsyncMock(return_value=section)
    _wire_fake_generation_runs_upsert(
        mock_db,
        section["_id"],
        initial={
            "sectionId": section["_id"],
            "status": "processing",
            "updatedAt": datetime.now(timezone.utc) - timedelta(seconds=599),
        },
    )

    with patch("app.tasks.generate_section_all.generate_section_all.delay") as mock_delay:
        response = await client.post(
            f'/api/sections/{section["_id"]}/generate-all',
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 202
    assert response.json()["status"] == "processing"
    mock_delay.assert_not_called()


@pytest.mark.asyncio
async def test_get_generate_all_returns_merged_status(client, mock_db, sample_section):
    run = {
        "sectionId": sample_section["_id"],
        "status": "partial",
        "extractionStatus": "completed",
        "transliterationStatus": "completed",
        "analysisStatus": "failed",
        "aiExtractedText": "extracted text",
        "transliteratedText": "translit text",
        "wordByWordMeaning": None,
        "fullMeaning": None,
        "simplifiedMeaning": None,
        "error": "Verse analysis service unavailable",
    }
    mock_db.generation_runs.find_one = AsyncMock(return_value=run)

    response = await client.get(f'/api/sections/{sample_section["_id"]}/generate-all')

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "partial"
    assert data["extractionStatus"] == "completed"
    assert data["transliterationStatus"] == "completed"
    assert data["analysisStatus"] == "failed"
    assert data["aiExtractedText"] == "extracted text"
    assert data["transliteratedText"] == "translit text"
    assert data["error"] == "Verse analysis service unavailable"


@pytest.mark.asyncio
async def test_get_generate_all_not_found(client, mock_db):
    mock_db.generation_runs.find_one = AsyncMock(return_value=None)

    response = await client.get("/api/sections/507f1f77bcf86cd799439014/generate-all")

    assert response.status_code == 404


def _patch_motor_client(mock_db):
    mock_client = MagicMock()
    mock_client.__getitem__ = MagicMock(return_value=mock_db)
    mock_client.close = MagicMock()
    return patch(
        "app.tasks.generate_section_all.AsyncIOMotorClient",
        return_value=mock_client,
    )


def _wire_stateful_generation_runs(mock_db):
    """Makes generation_runs.update_one/find_one share an in-memory dict, so the
    orchestrator's read-after-write status computation sees prior writes."""
    state: dict = {}

    async def fake_update_one(_filter, update, **kwargs):
        state.update(update.get("$set", {}))
        return MagicMock()

    async def fake_find_one(_filter, **kwargs):
        return dict(state) if state else None

    mock_db.generation_runs.update_one = AsyncMock(side_effect=fake_update_one)
    mock_db.generation_runs.find_one = AsyncMock(side_effect=fake_find_one)
    return state


@pytest.mark.asyncio
async def test_generate_section_all_happy_path(mock_db, sample_section, sample_page, sample_book):
    section = {**sample_section, "croppedImageKey": "books/x/sections/1.png", "originalText": None}
    mock_db.sections.find_one = AsyncMock(return_value=section)
    mock_db.pages.find_one = AsyncMock(return_value=sample_page)
    mock_db.books.find_one = AsyncMock(return_value=sample_book)
    mock_db.ai_text_extractions.update_one = AsyncMock()
    mock_db.transliterations.find_one = AsyncMock(return_value=None)
    mock_db.transliterations.update_one = AsyncMock()
    mock_db.sections.update_one = AsyncMock()
    state = _wire_stateful_generation_runs(mock_db)

    extraction_result = AITextResult(
        text="extracted source text", confidence=0.9, model="test-model", processing_time_ms=100,
    )
    translit_result = TransliterationResult(
        transliterated_text="translit text", source_script="si", target_script="sinhala",
        confidence=0.9, model="test-model",
    )
    analysis_result = VerseAnalysis(
        wordByWordMeaning="word by word", fullMeaning="full meaning", simplifiedMeaning="simple meaning",
    )

    with _patch_motor_client(mock_db), \
         patch("app.tasks.generate_section_all.get_s3") as mock_get_s3, \
         patch("app.tasks.generate_section_all.extract_text", new=AsyncMock(return_value=extraction_result)), \
         patch("app.tasks.generate_section_all.transliterate_text", new=AsyncMock(return_value=translit_result)), \
         patch("app.tasks.generate_section_all.analyze_verse", new=AsyncMock(return_value=analysis_result)):
        mock_s3 = MagicMock()
        mock_s3.get_object.return_value.read.return_value = b"fake-image-bytes"
        mock_get_s3.return_value = mock_s3

        result = await _generate_section_all(str(section["_id"]), "sinhala", False)

    assert result["status"] == "completed"
    assert state["extractionStatus"] == "completed"
    assert state["transliterationStatus"] == "completed"
    assert state["analysisStatus"] == "completed"
    assert state["status"] == "completed"
    assert state["aiExtractedText"] == "extracted source text"
    assert state["transliteratedText"] == "translit text"
    assert state["wordByWordMeaning"] == "word by word"


@pytest.mark.asyncio
async def test_generate_section_all_extraction_failure_stops_chain(mock_db, sample_section):
    section = {**sample_section, "croppedImageKey": "books/x/sections/1.png", "originalText": None}
    mock_db.sections.find_one = AsyncMock(return_value=section)
    mock_db.ai_text_extractions.update_one = AsyncMock()
    mock_db.sections.update_one = AsyncMock()
    state = _wire_stateful_generation_runs(mock_db)

    with _patch_motor_client(mock_db), \
         patch("app.tasks.generate_section_all.get_s3") as mock_get_s3, \
         patch("app.tasks.generate_section_all.extract_text", new=AsyncMock(side_effect=RuntimeError("boom"))), \
         patch("app.tasks.generate_section_all.transliterate_text", new=AsyncMock()) as mock_translit, \
         patch("app.tasks.generate_section_all.analyze_verse", new=AsyncMock()) as mock_analyze:
        mock_s3 = MagicMock()
        mock_s3.get_object.return_value.read.return_value = b"fake-image-bytes"
        mock_get_s3.return_value = mock_s3

        result = await _generate_section_all(str(section["_id"]), "sinhala", False)

    assert "error" in result
    mock_translit.assert_not_called()
    mock_analyze.assert_not_called()
    assert state["extractionStatus"] == "failed"
    assert state["status"] == "failed"


@pytest.mark.asyncio
async def test_generate_section_all_partial_when_analysis_fails(
    mock_db, sample_section, sample_page, sample_book
):
    section = {**sample_section, "croppedImageKey": "books/x/sections/1.png", "originalText": None}
    mock_db.sections.find_one = AsyncMock(return_value=section)
    mock_db.pages.find_one = AsyncMock(return_value=sample_page)
    mock_db.books.find_one = AsyncMock(return_value=sample_book)
    mock_db.ai_text_extractions.update_one = AsyncMock()
    mock_db.transliterations.find_one = AsyncMock(return_value=None)
    mock_db.transliterations.update_one = AsyncMock()
    mock_db.sections.update_one = AsyncMock()
    state = _wire_stateful_generation_runs(mock_db)

    extraction_result = AITextResult(
        text="extracted source text", confidence=0.9, model="test-model", processing_time_ms=100,
    )
    translit_result = TransliterationResult(
        transliterated_text="translit text", source_script="si", target_script="sinhala",
        confidence=0.9, model="test-model",
    )

    with _patch_motor_client(mock_db), \
         patch("app.tasks.generate_section_all.get_s3") as mock_get_s3, \
         patch("app.tasks.generate_section_all.extract_text", new=AsyncMock(return_value=extraction_result)), \
         patch("app.tasks.generate_section_all.transliterate_text", new=AsyncMock(return_value=translit_result)), \
         patch("app.tasks.generate_section_all.analyze_verse", new=AsyncMock(return_value=None)):
        mock_s3 = MagicMock()
        mock_s3.get_object.return_value.read.return_value = b"fake-image-bytes"
        mock_get_s3.return_value = mock_s3

        result = await _generate_section_all(str(section["_id"]), "sinhala", False)

    assert result["status"] == "partial"
    assert state["extractionStatus"] == "completed"
    assert state["transliterationStatus"] == "completed"
    assert state["analysisStatus"] == "failed"
    assert state["status"] == "partial"
    assert state["aiExtractedText"] == "extracted source text"
    assert state["transliteratedText"] == "translit text"
