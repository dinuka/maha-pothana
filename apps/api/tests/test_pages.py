import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_list_pages(client, mock_db, sample_page):
    mock_db.pages.find.return_value.to_list = AsyncMock(return_value=[sample_page])
    mock_db.sections.count_documents = AsyncMock(return_value=3)

    response = await client.get(f'/api/books/{sample_page["bookId"]}/pages')

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["pageNumber"] == 1
    assert data[0]["sectionCount"] == 3


@pytest.mark.asyncio
async def test_get_page_with_sections(client, mock_db, sample_page, sample_section):
    mock_db.pages.find_one = AsyncMock(return_value=sample_page)
    mock_db.sections.find.return_value.to_list = AsyncMock(return_value=[sample_section])

    response = await client.get(f'/api/books/{sample_page["bookId"]}/pages/1')

    assert response.status_code == 200
    data = response.json()
    assert data["page"]["pageNumber"] == 1
    assert len(data["sections"]) == 1
    assert data["sections"][0]["originalText"] == "Original Sinhala text"


@pytest.mark.asyncio
async def test_get_page_not_found(client, mock_db, sample_page):
    mock_db.pages.find_one = AsyncMock(return_value=None)

    response = await client.get(
        f'/api/books/{sample_page["bookId"]}/pages/999'
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_trigger_section_detection(client, mock_db, sample_page):
    mock_db.pages.find_one = AsyncMock(return_value=sample_page)

    with patch("app.api.pages.detect_sections") as mock_detect:
        response = await client.post(
            f'/api/pages/{sample_page["_id"]}/sections/detect'
        )

    assert response.status_code == 200
    assert response.json()["status"] == "PROCESSING"
    mock_detect.delay.assert_called_once_with(sample_page["_id"])


@pytest.mark.asyncio
async def test_save_sections(client, mock_db, sample_page):
    mock_db.pages.find_one = AsyncMock(return_value=sample_page)
    mock_db.sections.delete_many = AsyncMock()
    mock_db.sections.insert_one = AsyncMock()
    mock_db.pages.update_one = AsyncMock()

    with patch("app.api.pages.crop_sections") as mock_crop:
        response = await client.put(
            f'/api/pages/{sample_page["_id"]}/sections',
            json=[{
                "sectionOrder": 1,
                "type": "PARAGRAPH",
                "x": 10,
                "y": 10,
                "width": 780,
                "height": 200,
                "originalText": "Text",
            }],
        )

    assert response.status_code == 200
    assert response.json()["status"] == "SECTIONS_CONFIRMED"
    mock_db.sections.delete_many.assert_awaited_once_with({"pageId": sample_page["_id"]})
    mock_crop.delay.assert_called_once_with(sample_page["_id"])
