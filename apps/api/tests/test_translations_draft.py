import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_upsert_draft_create(client, mock_db):
    mock_db.translation_drafts.find_one = AsyncMock(return_value=None)
    mock_db.translation_drafts.insert_one = AsyncMock(return_value=MagicMock(inserted_id="507f1f77bcf86cd799439999"))

    response = await client.post(
        "/api/translations/draft",
        json={"sectionId": "507f1f77bcf86cd799439014", "translatedText": "Draft text"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["translatedText"] == "Draft text"
    assert "draftId" in data
    mock_db.translation_drafts.insert_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_upsert_draft_update(client, mock_db):
    existing = {
        "_id": "507f1f77bcf86cd799439998",
        "sectionId": "507f1f77bcf86cd799439014",
        "translatorId": "507f1f77bcf86cd799439011",
        "translatedText": "Old text",
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc),
    }
    mock_db.translation_drafts.find_one = AsyncMock(return_value=existing)
    mock_db.translation_drafts.update_one = AsyncMock()

    response = await client.post(
        "/api/translations/draft",
        json={"sectionId": "507f1f77bcf86cd799439014", "translatedText": "Updated text"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["translatedText"] == "Updated text"
    assert data["draftId"] == "507f1f77bcf86cd799439998"
    mock_db.translation_drafts.update_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_draft_found(client, mock_db):
    draft = {
        "_id": "507f1f77bcf86cd799439999",
        "sectionId": "507f1f77bcf86cd799439014",
        "translatorId": "507f1f77bcf86cd799439011",
        "translatedText": "Draft text",
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc),
    }
    mock_db.translation_drafts.find_one = AsyncMock(return_value=draft)

    response = await client.get(
        "/api/translations/draft?sectionId=507f1f77bcf86cd799439014",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["translatedText"] == "Draft text"
    assert data["draftId"] == "507f1f77bcf86cd799439999"


@pytest.mark.asyncio
async def test_get_draft_not_found(client, mock_db):
    mock_db.translation_drafts.find_one = AsyncMock(return_value=None)

    response = await client.get(
        "/api/translations/draft?sectionId=507f1f77bcf86cd799439014",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_draft_success(client, mock_db):
    mock_db.translation_drafts.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))

    response = await client.delete(
        "/api/translations/draft/507f1f77bcf86cd799439999",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "deleted"


@pytest.mark.asyncio
async def test_delete_draft_not_found(client, mock_db):
    mock_db.translation_drafts.delete_one = AsyncMock(return_value=MagicMock(deleted_count=0))

    response = await client.delete(
        "/api/translations/draft/507f1f77bcf86cd799439999",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 404
