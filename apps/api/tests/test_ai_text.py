import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from bson import ObjectId


@pytest.mark.asyncio
async def test_extract_section_text_success(client, mock_db, sample_section):
    sample_section["croppedImageKey"] = "books/123/sections/456.png"
    mock_db.sections.find_one = AsyncMock(return_value=sample_section)
    mock_db.ai_text_extractions.find_one = AsyncMock(return_value=None)

    with patch("app.tasks.extract_section_text.extract_section_text") as mock_task:
        mock_task.delay.return_value = MagicMock(id="task-123")
        response = await client.post(
            f"/api/sections/{sample_section['_id']}/extract",
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 202
    data = response.json()
    assert data["taskId"] == "task-123"
    assert data["status"] == "queued"
    assert data["sectionId"] == str(sample_section["_id"])


@pytest.mark.asyncio
async def test_extract_section_text_no_cropped_image(client, mock_db):
    section = {
        "_id": ObjectId("507f1f77bcf86cd799439014"),
        "page": {"id": "507f1f77bcf86cd799439013"},
        "croppedImageKey": None,
    }
    mock_db.sections.find_one = AsyncMock(return_value=section)

    response = await client.post(
        "/api/sections/507f1f77bcf86cd799439014/extract",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 422
    assert "cropped image" in response.json()["detail"]


@pytest.mark.asyncio
async def test_extract_section_text_already_extracted(client, mock_db):
    section = {
        "_id": ObjectId("507f1f77bcf86cd799439014"),
        "page": {"id": "507f1f77bcf86cd799439013"},
        "croppedImageKey": "books/123/sections/456.png",
    }
    mock_db.sections.find_one = AsyncMock(return_value=section)
    mock_db.ai_text_extractions.find_one = AsyncMock(return_value={
        "sectionId": str(section["_id"]),
        "status": "completed",
        "extractedText": "Existing text",
        "confidence": 0.95,
    })

    response = await client.post(
        f"/api/sections/{section['_id']}/extract",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 409
    data = response.json()
    assert data["status"] == "completed"
    assert data["extractedText"] == "Existing text"
    assert data["confidence"] == 0.95


@pytest.mark.asyncio
async def test_extract_section_text_not_found(client, mock_db):
    mock_db.sections.find_one = AsyncMock(return_value=None)

    response = await client.post(
        "/api/sections/507f1f77bcf86cd799439999/extract",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_extraction_success(client, mock_db):
    mock_db.ai_text_extractions.find_one = AsyncMock(return_value={
        "sectionId": "507f1f77bcf86cd799439014",
        "extractedText": "Extracted Sinhala text",
        "confidence": 0.92,
        "model": "gpt-4o",
        "processingTimeMs": 2340,
        "createdAt": datetime.now(timezone.utc),
    })

    response = await client.get(
        "/api/sections/507f1f77bcf86cd799439014/extraction",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["extractedText"] == "Extracted Sinhala text"
    assert data["confidence"] == 0.92
    assert data["model"] == "gpt-4o"
    assert data["processingTimeMs"] == 2340


@pytest.mark.asyncio
async def test_get_extraction_not_found(client, mock_db):
    mock_db.ai_text_extractions.find_one = AsyncMock(return_value=None)

    response = await client.get(
        "/api/sections/507f1f77bcf86cd799439014/extraction",
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_transliterate_section_with_cache(client, mock_db, sample_section):
    mock_db.sections.find_one = AsyncMock(return_value=sample_section)
    mock_db.transliterations.find_one = AsyncMock(return_value={
        "sectionId": str(sample_section["_id"]),
        "targetScript": "sinhala",
        "sourceScript": "devanagari",
        "transliteratedText": "මාතා සර්ව",
        "confidence": 0.91,
        "model": "gpt-4o",
    })

    response = await client.post(
        f"/api/sections/{sample_section['_id']}/transliterate?target_script=sinhala",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["cached"] is True
    assert data["transliteratedText"] == "මාතා සර්ව"


@pytest.mark.asyncio
async def test_transliterate_section_no_source_text(client, mock_db):
    section = {
        "_id": ObjectId("507f1f77bcf86cd799439014"),
        "aiExtractedText": None,
        "originalText": None,
    }
    mock_db.sections.find_one = AsyncMock(return_value=section)

    response = await client.post(
        "/api/sections/507f1f77bcf86cd799439014/transliterate?target_script=sinhala",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 422
    assert "No source text" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_transliterations(client, mock_db):
    mock_db.transliterations.find = MagicMock()
    mock_db.transliterations.find.return_value.to_list = AsyncMock(return_value=[
        {
            "targetScript": "sinhala",
            "transliteratedText": "මාතා සර්ව",
            "confidence": 0.91,
            "model": "gpt-4o",
            "createdAt": datetime.now(timezone.utc),
        }
    ])

    response = await client.get(
        "/api/sections/507f1f77bcf86cd799439014/transliterations",
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["transliterations"]) == 1
    assert data["transliterations"][0]["transliteratedText"] == "මාතා සර්ව"


@pytest.mark.asyncio
async def test_update_source_text_ai(client, mock_db, sample_section):
    mock_db.sections.find_one = AsyncMock(return_value=sample_section)
    mock_db.sections.update_one = AsyncMock()
    mock_db.transliterations.delete_many = AsyncMock()

    response = await client.put(
        f"/api/sections/{sample_section['_id']}/source-text",
        json={"text": "Updated AI text", "source": "ai"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["updatedText"] == "Updated AI text"
    assert data["source"] == "ai"


@pytest.mark.asyncio
async def test_update_source_text_ocr(client, mock_db, sample_section):
    mock_db.sections.find_one = AsyncMock(return_value=sample_section)
    mock_db.sections.update_one = AsyncMock()
    mock_db.transliterations.delete_many = AsyncMock()

    response = await client.put(
        f"/api/sections/{sample_section['_id']}/source-text",
        json={"text": "Updated OCR text", "source": "ocr"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["updatedText"] == "Updated OCR text"
    assert data["source"] == "ocr"


@pytest.mark.asyncio
async def test_update_source_text_invalid_source(client, mock_db, sample_section):
    mock_db.sections.find_one = AsyncMock(return_value=sample_section)

    response = await client.put(
        f"/api/sections/{sample_section['_id']}/source-text",
        json={"text": "Some text", "source": "invalid"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_source_text_not_found(client, mock_db):
    mock_db.sections.find_one = AsyncMock(return_value=None)

    response = await client.put(
        "/api/sections/507f1f77bcf86cd799439999/source-text",
        json={"text": "Some text", "source": "ai"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_extraction_status(client, mock_db):
    mock_db.sections.find = MagicMock()
    mock_db.sections.find.return_value.to_list = AsyncMock(return_value=[
        {"_id": ObjectId("507f1f77bcf86cd799439014")},
        {"_id": ObjectId("507f1f77bcf86cd799439015")},
        {"_id": ObjectId("507f1f77bcf86cd799439016")},
    ])

    call_count = 0

    async def mock_find_one(query):
        nonlocal call_count
        call_count += 1
        section_id = query.get("sectionId")
        if section_id == "507f1f77bcf86cd799439014":
            return {"status": "completed"}
        return None

    mock_db.ai_text_extractions.find_one = AsyncMock(side_effect=mock_find_one)
    mock_db.redis_progress.find_one = AsyncMock(return_value=None)

    response = await client.get(
        "/api/books/507f1f77bcf86cd799439012/extraction/status",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["totalSections"] == 3
    assert data["extracted"] == 1
    assert data["pending"] == 2


@pytest.mark.asyncio
async def test_trigger_book_extraction(client, mock_db, sample_book):
    mock_db.books.find_one = AsyncMock(return_value=sample_book)
    mock_db.redis_progress.find_one = AsyncMock(return_value=None)
    mock_db.sections.find = MagicMock()
    mock_db.sections.find.return_value.to_list = AsyncMock(return_value=[
        {
            "_id": ObjectId("507f1f77bcf86cd799439014"),
            "croppedImageKey": "books/123/sections/456.png",
        },
    ])
    mock_db.ai_text_extractions.find_one = AsyncMock(return_value=None)
    mock_db.redis_progress.insert_one = AsyncMock()

    with patch("app.tasks.extract_section_text.extract_section_text") as mock_task:
        mock_task.delay.return_value = MagicMock(id="task-batch-123")
        response = await client.post(
            f"/api/books/{sample_book['_id']}/extract",
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 202
    data = response.json()
    assert data["totalSections"] == 1
    assert data["estimatedCost"] > 0


@pytest.mark.asyncio
async def test_trigger_book_extraction_all_already_extracted(client, mock_db, sample_book):
    mock_db.books.find_one = AsyncMock(return_value=sample_book)
    mock_db.redis_progress.find_one = AsyncMock(return_value=None)
    mock_db.sections.find = MagicMock()
    mock_db.sections.find.return_value.to_list = AsyncMock(return_value=[
        {
            "_id": ObjectId("507f1f77bcf86cd799439014"),
            "croppedImageKey": "books/123/sections/456.png",
        },
    ])
    mock_db.ai_text_extractions.find_one = AsyncMock(return_value={"status": "completed"})

    response = await client.post(
        f"/api/books/{sample_book['_id']}/extract",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 409
    assert "already extracted" in response.json()["detail"]


@pytest.mark.asyncio
async def test_transliterate_section_queued(client, mock_db, sample_section):
    mock_db.sections.find_one = AsyncMock(return_value=sample_section)
    mock_db.transliterations.find_one = AsyncMock(return_value=None)

    with patch("app.tasks.transliterate_section.transliterate_section") as mock_task:
        mock_task.delay.return_value = MagicMock(id="task-translit-123")
        response = await client.post(
            f"/api/sections/{sample_section['_id']}/transliterate?target_script=sinhala",
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert data["taskId"] == "task-translit-123"


@pytest.mark.asyncio
async def test_transliterate_section_not_found(client, mock_db):
    mock_db.sections.find_one = AsyncMock(return_value=None)

    response = await client.post(
        "/api/sections/507f1f77bcf86cd799439999/transliterate?target_script=sinhala",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 404
