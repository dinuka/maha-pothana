import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timezone
from bson import ObjectId


@pytest.mark.asyncio
async def test_get_translation_history(client, mock_db, sample_book, sample_translation, sample_user):
    mock_db.books.find_one = AsyncMock(return_value=sample_book)

    activity_item = {
        "_id": ObjectId(),
        "translationId": str(sample_translation["_id"]),
        "sectionId": sample_translation["section"]["id"],
        "bookId": str(sample_book["_id"]),
        "pageNumber": 1,
        "sectionOrder": 1,
        "translatorId": sample_translation["translator"]["id"],
        "translatorName": sample_user["name"],
        "translatedText": sample_translation["translatedText"],
        "action": "SUBMITTED",
        "performedBy": None,
        "performedByName": None,
        "createdAt": datetime.now(timezone.utc),
    }
    mock_db.translation_activity.find.return_value.to_list = AsyncMock(return_value=[activity_item])

    response = await client.get(
        f"/api/translations/history?bookId={sample_book['_id']}",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "hasMore" in data
    assert len(data["items"]) == 1
    assert data["items"][0]["translatorName"] == "Test User"
    assert data["items"][0]["action"] == "SUBMITTED"


@pytest.mark.asyncio
async def test_get_translation_history_empty(client, mock_db, sample_book):
    mock_db.books.find_one = AsyncMock(return_value=sample_book)
    mock_db.translation_activity.find.return_value.to_list = AsyncMock(return_value=[])

    response = await client.get(
        f"/api/translations/history?bookId={sample_book['_id']}",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["hasMore"] is False


@pytest.mark.asyncio
async def test_get_translation_history_book_not_found(client, mock_db):
    mock_db.books.find_one = AsyncMock(return_value=None)

    response = await client.get(
        "/api/translations/history?bookId=507f1f77bcf86cd799439999",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 404
