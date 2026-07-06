import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta


@pytest.mark.asyncio
async def test_get_book_stats(client, mock_db, sample_book, sample_page, sample_section):
    mock_db.books.find_one = AsyncMock(return_value=sample_book)
    mock_db.sections.aggregate.return_value.to_list = AsyncMock(return_value=[
        {"_id": None, "total": 10, "translated": 3, "inProgress": 2, "pending": 5}
    ])

    with patch("app.api.books_stats._get_stats_from_db") as mock_stats:
        from app.schemas.stats import TranslationStatsResponse, LanguageStats, PageStats
        mock_stats.return_value = TranslationStatsResponse(
            totalSections=10,
            translatedSections=3,
            pendingSections=5,
            inProgressSections=2,
            translationPercent=30.0,
            byLanguage={"si": LanguageStats(total=10, translated=3, percent=30.0)},
            byPage=[PageStats(pageNumber=1, total=5, translated=3, percent=60.0)],
        )

        response = await client.get(
            f"/api/books/{sample_book['_id']}/stats",
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["totalSections"] == 10
    assert data["translatedSections"] == 3
    assert data["translationPercent"] == 30.0


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
    now = datetime.now(timezone.utc)
    section_created = now - timedelta(hours=2)

    mock_db.books.find_one = AsyncMock(return_value=sample_book)
    mock_db.translations.aggregate.return_value.to_list = AsyncMock(return_value=[
        {
            "_id": "507f1f77bcf86cd799439011",
            "translations": [
                {"isApproved": True, "createdAt": now, "sec": {"createdAt": section_created}},
                {"isApproved": False, "createdAt": now, "sec": {"createdAt": section_created}},
            ],
            "totalAssigned": 2,
            "approvedCount": 1,
            "rejectedCount": 0,
            "pendingCount": 1,
            "lastActiveAt": now,
        }
    ])
    mock_db.users.find_one = AsyncMock(return_value={"name": "Test Translator"})

    response = await client.get(
        f"/api/books/{sample_book['_id']}/translators/stats",
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
    mock_db.books.find_one = AsyncMock(return_value=sample_book)
    mock_db.translations.aggregate.return_value.to_list = AsyncMock(return_value=[])

    response = await client.get(
        f"/api/books/{sample_book['_id']}/translators/stats",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert response.json() == []
