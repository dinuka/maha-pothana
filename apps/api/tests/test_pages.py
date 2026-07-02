import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_list_pages(client, mock_db, sample_page):
    mock_db.pages.find.return_value.to_list = AsyncMock(return_value=[sample_page])
    mock_db.pages.count_documents = AsyncMock(return_value=1)
    mock_db.sections.count_documents = AsyncMock(return_value=3)

    response = await client.get(f'/api/books/{sample_page["book"]["id"]}/pages')

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["skip"] == 0
    assert data["limit"] == 35
    assert len(data["items"]) == 1
    assert data["items"][0]["pageNumber"] == 1
    assert data["items"][0]["sectionCount"] == 3


@pytest.mark.asyncio
async def test_list_pages_pagination(client, mock_db, sample_page):
    mock_db.pages.find.return_value.to_list = AsyncMock(return_value=[sample_page])
    mock_db.pages.count_documents = AsyncMock(return_value=50)

    response = await client.get(
        f'/api/books/{sample_page["book"]["id"]}/pages?skip=35&limit=7'
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 50
    assert data["skip"] == 35
    assert data["limit"] == 7
    mock_db.pages.find.return_value.skip.assert_called_with(35)
    mock_db.pages.find.return_value.skip.return_value.limit.assert_called_with(7)


@pytest.mark.asyncio
async def test_list_pages_status_filter(client, mock_db, sample_page):
    mock_db.pages.find.return_value.to_list = AsyncMock(return_value=[sample_page])
    mock_db.pages.count_documents = AsyncMock(return_value=1)

    response = await client.get(
        f'/api/books/{sample_page["book"]["id"]}/pages?status=SECTIONS_CONFIRMED'
    )

    assert response.status_code == 200
    mock_db.pages.count_documents.assert_awaited_once_with(
        {"book.id": sample_page["book"]["id"], "status": "SECTIONS_CONFIRMED"}
    )
    mock_db.pages.find.assert_called_once_with(
        {"book.id": sample_page["book"]["id"], "status": "SECTIONS_CONFIRMED"}
    )


@pytest.mark.asyncio
async def test_list_pages_status_all_is_no_filter(client, mock_db, sample_page):
    mock_db.pages.find.return_value.to_list = AsyncMock(return_value=[sample_page])
    mock_db.pages.count_documents = AsyncMock(return_value=1)

    response = await client.get(
        f'/api/books/{sample_page["book"]["id"]}/pages?status=ALL'
    )

    assert response.status_code == 200
    mock_db.pages.count_documents.assert_awaited_once_with(
        {"book.id": sample_page["book"]["id"]}
    )
    mock_db.pages.find.assert_called_once_with({"book.id": sample_page["book"]["id"]})


@pytest.mark.asyncio
async def test_list_pages_sort_progress_maps_to_page_number(client, mock_db, sample_page):
    mock_db.pages.find.return_value.to_list = AsyncMock(return_value=[sample_page])
    mock_db.pages.count_documents = AsyncMock(return_value=1)

    response = await client.get(
        f'/api/books/{sample_page["book"]["id"]}/pages?sort=PROGRESS'
    )

    assert response.status_code == 200
    mock_db.pages.find.return_value.sort.assert_called_once_with("pageNumber", 1)


@pytest.mark.asyncio
async def test_list_pages_default_limit(client, mock_db, sample_page):
    mock_db.pages.find.return_value.to_list = AsyncMock(return_value=[sample_page])
    mock_db.pages.count_documents = AsyncMock(return_value=1)

    response = await client.get(f'/api/books/{sample_page["book"]["id"]}/pages')

    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 35
    mock_db.pages.find.return_value.skip.return_value.limit.assert_called_with(35)


@pytest.mark.asyncio
async def test_get_page_with_sections(client, mock_db, sample_page, sample_section):
    mock_db.pages.find_one = AsyncMock(return_value=sample_page)
    mock_db.sections.find.return_value.to_list = AsyncMock(return_value=[sample_section])

    response = await client.get(f'/api/books/{sample_page["book"]["id"]}/pages/1')

    assert response.status_code == 200
    data = response.json()
    assert data["page"]["pageNumber"] == 1
    assert len(data["sections"]) == 1
    assert data["sections"][0]["originalText"] == "Original Sinhala text"


@pytest.mark.asyncio
async def test_get_page_not_found(client, mock_db, sample_page):
    mock_db.pages.find_one = AsyncMock(return_value=None)

    response = await client.get(
        f'/api/books/{sample_page["book"]["id"]}/pages/999'
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
    mock_db.sections.delete_many.assert_awaited_once_with({"page.id": sample_page["_id"]})
    mock_crop.delay.assert_called_once_with(sample_page["_id"])
