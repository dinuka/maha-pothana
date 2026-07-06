import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_get_translation_history(client, mock_db, sample_book, sample_translation, sample_user):
    mock_db.books.find_one = AsyncMock(return_value=sample_book)

    history_item = {
        **sample_translation,
        "sec": {"sectionOrder": 1, "page": {"id": "507f1f77bcf86cd799439013"}},
        "pg": {"pageNumber": 1, "book": {"id": str(sample_book["_id"])}},
        "translatorUser": sample_user,
        "performerUser": None,
    }
    mock_db.translations.aggregate.return_value.to_list = AsyncMock(return_value=[history_item])

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


@pytest.mark.asyncio
async def test_get_translation_history_empty(client, mock_db, sample_book):
    mock_db.books.find_one = AsyncMock(return_value=sample_book)
    mock_db.translations.aggregate.return_value.to_list = AsyncMock(return_value=[])

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
