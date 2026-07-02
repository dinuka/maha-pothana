import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_get_next_section(client, mock_db, sample_section, sample_page, sample_book):
    section_with_lookups = {
        **sample_section,
        "page": sample_page,
        "book": sample_book,
    }
    mock_db.sections.aggregate.return_value.to_list = AsyncMock(return_value=[section_with_lookups])

    response = await client.get("/api/sections/next", headers={
        "Authorization": "Bearer test-token",
    })

    assert response.status_code == 200
    data = response.json()
    assert data["originalText"] == "Original Sinhala text"
    assert data["pageNumber"] == 1
    assert data["bookTitle"] == "Test Book"


@pytest.mark.asyncio
async def test_get_next_section_none_available(client, mock_db):
    mock_db.sections.aggregate.return_value.to_list = AsyncMock(return_value=[])

    response = await client.get("/api/sections/next", headers={
        "Authorization": "Bearer test-token",
    })

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_section(client, mock_db, sample_section):
    mock_db.sections.find_one = AsyncMock(return_value=sample_section)

    with patch("app.api.sections.get_presigned_url", new=AsyncMock(return_value="https://s3.example.com/cropped.png")):
        response = await client.get(f'/api/sections/{sample_section["_id"]}')

    assert response.status_code == 200
    data = response.json()
    assert data["originalText"] == "Original Sinhala text"
    assert data["type"] == "PARAGRAPH"


@pytest.mark.asyncio
async def test_submit_translation_new(client, mock_db, sample_section, sample_translation):
    mock_db.sections.find_one = AsyncMock(return_value=sample_section)
    mock_db.translations.find_one = AsyncMock(return_value=None)
    mock_db.translations.insert_one = AsyncMock()

    response = await client.post(
        f'/api/sections/{sample_section["_id"]}/translate',
        json={
            "translatedText": "Translated text",
            "exactLetterTranslation": "Exact letter translation",
        },
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "saved"
    mock_db.translations.insert_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_submit_translation_update(client, mock_db, sample_section, sample_translation):
    mock_db.sections.find_one = AsyncMock(return_value=sample_section)
    mock_db.translations.find_one = AsyncMock(return_value=sample_translation)
    mock_db.translations.update_one = AsyncMock()

    response = await client.post(
        f'/api/sections/{sample_section["_id"]}/translate',
        json={
            "translatedText": "Updated translation",
        },
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "saved"
    mock_db.translations.update_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_my_translation(client, mock_db, sample_translation):
    mock_db.translations.find_one = AsyncMock(return_value=sample_translation)

    response = await client.get(
        f'/api/sections/{sample_translation["section"]["id"]}/my-translation',
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["translatedText"] == "Translated text"
    assert data["exactLetterTranslation"] == "Exact letter translation"


@pytest.mark.asyncio
async def test_get_my_translation_not_found(client, mock_db):
    mock_db.translations.find_one = AsyncMock(return_value=None)

    response = await client.get(
        f'/api/sections/507f1f77bcf86cd799439014/my-translation',
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_section_translations(client, mock_db, sample_section, sample_translation, sample_user):
    mock_db.translations.find.return_value.to_list = AsyncMock(return_value=[sample_translation])
    mock_db.users.find_one = AsyncMock(return_value=sample_user)

    response = await client.get(
        f'/api/sections/{sample_section["_id"]}/translations'
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["translatedText"] == "Translated text"
    assert data[0]["translatorName"] == "Test User"


@pytest.mark.asyncio
async def test_approve_translation(client, mock_db, sample_translation):
    mock_db.translations.update_one = AsyncMock()
    mock_db.translations.update_one.return_value.matched_count = 1

    response = await client.post(
        f'/api/translations/{sample_translation["_id"]}/approve',
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"


@pytest.mark.asyncio
async def test_approve_translation_not_found(client, mock_db):
    mock_db.translations.update_one = AsyncMock()
    mock_db.translations.update_one.return_value.matched_count = 0

    response = await client.post(
        f'/api/translations/507f1f77bcf86cd799439999/approve',
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_reject_translation(client, mock_db, sample_translation):
    mock_db.translations.update_one = AsyncMock()
    mock_db.translations.update_one.return_value.matched_count = 1

    response = await client.post(
        f'/api/translations/{sample_translation["_id"]}/reject',
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
