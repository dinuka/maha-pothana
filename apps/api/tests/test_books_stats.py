import pytest
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_get_book_stats(client, mock_db, sample_book):
    book_id = str(sample_book["_id"])
    mock_db.books.find_one = AsyncMock(return_value=sample_book)
    mock_db.book_stats.find_one = AsyncMock(return_value={
        "bookId": book_id,
        "stats": {
            "totalSections": 10,
            "translatedSections": 3,
            "pendingSections": 5,
            "inProgressSections": 2,
            "translationPercent": 30.0,
            "byLanguage": {"si": {"total": 10, "translated": 3, "percent": 30.0}},
            "byPage": [{"pageNumber": 1, "total": 5, "translated": 3, "percent": 60.0}],
        },
        "translatorStats": [],
    })

    response = await client.get(
        f"/api/books/{book_id}/stats",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["totalSections"] == 10
    assert data["translatedSections"] == 3
    assert data["translationPercent"] == 30.0


@pytest.mark.asyncio
async def test_get_book_stats_no_doc_yet(client, mock_db, sample_book):
    """Before any recompute has run for a book, stats read as an empty summary."""
    book_id = str(sample_book["_id"])
    mock_db.books.find_one = AsyncMock(return_value=sample_book)
    mock_db.book_stats.find_one = AsyncMock(return_value=None)

    response = await client.get(
        f"/api/books/{book_id}/stats",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["totalSections"] == 0
    assert data["translationPercent"] == 0


@pytest.mark.asyncio
async def test_get_book_stats_not_found(client, mock_db):
    mock_db.books.find_one = AsyncMock(return_value=None)

    response = await client.get(
        "/api/books/507f1f77bcf86cd799439999/stats",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_translator_stats(client, mock_db, sample_book):
    book_id = str(sample_book["_id"])
    mock_db.books.find_one = AsyncMock(return_value=sample_book)
    mock_db.book_stats.find_one = AsyncMock(return_value={
        "bookId": book_id,
        "stats": {
            "totalSections": 0, "translatedSections": 0, "pendingSections": 0,
            "inProgressSections": 0, "translationPercent": 0, "byLanguage": {}, "byPage": [],
        },
        "translatorStats": [
            {
                "userId": "507f1f77bcf86cd799439011",
                "userName": "Test Translator",
                "totalAssigned": 2,
                "approvedCount": 1,
                "rejectedCount": 0,
                "pendingCount": 1,
                "approvalRate": 100.0,
                "avgTurnaroundHours": 2.0,
                "lastActiveAt": None,
            }
        ],
    })

    response = await client.get(
        f"/api/books/{book_id}/translators/stats",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["userName"] == "Test Translator"
    assert data[0]["totalAssigned"] == 2
    assert data[0]["approvedCount"] == 1


@pytest.mark.asyncio
async def test_get_translator_stats_empty(client, mock_db, sample_book):
    book_id = str(sample_book["_id"])
    mock_db.books.find_one = AsyncMock(return_value=sample_book)
    mock_db.book_stats.find_one = AsyncMock(return_value=None)

    response = await client.get(
        f"/api/books/{book_id}/translators/stats",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert response.json() == []
