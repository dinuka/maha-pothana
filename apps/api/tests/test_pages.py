import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_list_pages(client, mock_db, sample_page):
    mock_db.pages.find.return_value.to_list = AsyncMock(return_value=[sample_page])
    mock_db.pages.count_documents = AsyncMock(return_value=1)
    mock_db.sections.aggregate.return_value.to_list = AsyncMock(
        return_value=[
            {"_id": sample_page["_id"], "sectionCount": 3, "translatedCount": 0, "approvedCount": 0}
        ]
    )

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
    # For non-'all' filters, the aggregation pipeline is used
    # Need to return different values for stats, count, and main pipeline calls
    aggr_page_data = {**sample_page,
        "sectionCount": 0,
        "approvedSectionCount": 0,
        "translationSum": 0,
        "computedStatus": "not_started",
        "translationPercent": 0,
        "order": 1,
    }
    # Return stats data first, then count, then the main data
    mock_db.pages.aggregate.return_value.to_list = AsyncMock(
        side_effect=[
            [{"totalPages": 1, "totalSections": 0, "translatedSections": 0}],  # stats
            [{"total": 1}],                                                      # count
            [aggr_page_data],                                                     # main pipeline
        ]
    )

    response = await client.get(
        f'/api/books/{sample_page["book"]["id"]}/pages?filter=SECTIONS_CONFIRMED'
    )

    assert response.status_code == 200
    data = response.json()
    assert "pages" in data  # Now returns FilteredPageListResponse
    assert "pagination" in data
    assert "stats" in data


@pytest.mark.asyncio
async def test_list_pages_status_all_is_no_filter(client, mock_db, sample_page):
    mock_db.pages.find.return_value.to_list = AsyncMock(return_value=[sample_page])
    mock_db.pages.count_documents = AsyncMock(return_value=1)
    mock_db.sections.aggregate.return_value.to_list = AsyncMock(
        return_value=[{"_id": sample_page["_id"], "sectionCount": 0, "translatedCount": 0, "approvedCount": 0}]
    )

    response = await client.get(
        f'/api/books/{sample_page["book"]["id"]}/pages?status=ALL'
    )

    assert response.status_code == 200
    mock_db.pages.count_documents.assert_awaited_once_with(
        {"book.id": sample_page["book"]["id"]}
    )
    mock_db.pages.find.assert_called_once_with({"book.id": sample_page["book"]["id"]})


@pytest.mark.asyncio
async def test_list_pages_sort_progress_uses_aggregation(client, mock_db, sample_page):
    # With sort=PROGRESS, the new code enters the aggregation path
    mock_db.pages.aggregate.return_value.to_list = AsyncMock(return_value=[])

    response = await client.get(
        f'/api/books/{sample_page["book"]["id"]}/pages?sort=PROGRESS'
    )

    assert response.status_code == 200
    # Aggregation path was called (not the simple find/sort)
    assert mock_db.pages.aggregate.called


@pytest.mark.asyncio
async def test_list_pages_default_limit(client, mock_db, sample_page):
    mock_db.pages.find.return_value.to_list = AsyncMock(return_value=[sample_page])
    mock_db.pages.count_documents = AsyncMock(return_value=1)
    mock_db.sections.aggregate.return_value.to_list = AsyncMock(
        return_value=[{"_id": sample_page["_id"], "sectionCount": 0, "translatedCount": 0, "approvedCount": 0}]
    )

    response = await client.get(f'/api/books/{sample_page["book"]["id"]}/pages')

    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 35
    mock_db.pages.find.return_value.skip.return_value.limit.assert_called_with(35)


@pytest.mark.asyncio
async def test_get_page_with_sections(client, mock_db, sample_page, sample_section):
    mock_db.pages.find_one = AsyncMock(return_value=sample_page)
    mock_db.sections.find.return_value.to_list = AsyncMock(return_value=[sample_section])

    with patch("app.api.pages.get_presigned_url", new_callable=AsyncMock, return_value="http://minio/presigned/test.png"):
        response = await client.get(f'/api/books/{sample_page["book"]["id"]}/pages/1')

    assert response.status_code == 200
    data = response.json()
    assert data["page"]["pageNumber"] == 1
    assert data["page"]["imageUrl"] == "http://minio/presigned/test.png"
    assert data["page"]["imageKey"] == "books/user123/pages/1.png"
    assert len(data["sections"]) == 1
    assert data["sections"][0]["originalText"] == "Original Sinhala text"


@pytest.mark.asyncio
async def test_get_page_image_url_null_when_no_image_key(client, mock_db, sample_page):
    no_key_page = {**sample_page, "imageKey": None}
    mock_db.pages.find_one = AsyncMock(return_value=no_key_page)
    mock_db.sections.find.return_value.to_list = AsyncMock(return_value=[])

    response = await client.get(f'/api/books/{sample_page["book"]["id"]}/pages/1')

    assert response.status_code == 200
    data = response.json()
    assert data["page"]["imageUrl"] is None
    assert data["page"]["imageKey"] is None


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
async def test_save_sections(client, mock_db, sample_page, sample_user):
    mock_db.pages.find_one = AsyncMock(return_value=sample_page)
    mock_db.sections.delete_many = AsyncMock()
    mock_db.sections.insert_one = AsyncMock()
    mock_db.pages.update_one = AsyncMock()
    mock_db.users.find_one = AsyncMock(return_value=sample_user)
    mock_db.section_edit_history.insert_one = AsyncMock()

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


@pytest.mark.asyncio
async def test_save_sections_recalculates_order(client, mock_db, sample_page, sample_user):
    mock_db.pages.find_one = AsyncMock(return_value=sample_page)
    mock_db.sections.delete_many = AsyncMock()
    mock_db.sections.insert_one = AsyncMock()
    mock_db.pages.update_one = AsyncMock()
    mock_db.users.find_one = AsyncMock(return_value=sample_user)
    mock_db.section_edit_history.insert_one = AsyncMock()

    sections = [
        {"id": "s3", "type": "FOOTNOTE", "x": 10, "y": 500, "width": 200, "height": 50},
        {"id": "s1", "type": "HEADER", "x": 10, "y": 10, "width": 400, "height": 60},
        {"id": "s2", "type": "PARAGRAPH", "x": 10, "y": 100, "width": 400, "height": 300},
    ]

    with patch("app.api.pages.crop_sections") as mock_crop:
        response = await client.put(
            f'/api/pages/{sample_page["_id"]}/sections',
            json=sections,
        )

    assert response.status_code == 200
    insert_calls = mock_db.sections.insert_one.call_args_list
    assert len(insert_calls) == 3
    first_inserted = insert_calls[0][0][0]
    second_inserted = insert_calls[1][0][0]
    assert first_inserted["sectionOrder"] == 0
    assert first_inserted["type"] == "HEADER"
    assert second_inserted["sectionOrder"] == 1
    assert second_inserted["type"] == "PARAGRAPH"


@pytest.mark.asyncio
async def test_finalize_page(client, mock_db, sample_page):
    confirmed_page = {**sample_page, "status": "SECTIONS_CONFIRMED"}
    mock_db.pages.find_one = AsyncMock(return_value=confirmed_page)
    mock_db.sections.aggregate.return_value.to_list = AsyncMock(
        return_value=[
            {"_id": sample_page["_id"], "sectionCount": 2, "translatedCount": 2, "approvedCount": 2}
        ]
    )
    mock_db.pages.update_one = AsyncMock()

    response = await client.post(f'/api/pages/{sample_page["_id"]}/finalize')

    assert response.status_code == 200
    assert response.json()["status"] == "FINALIZED"
    update_call = mock_db.pages.update_one.call_args
    assert str(update_call[0][0]["_id"]) == sample_page["_id"]
    assert update_call[0][1]["$set"]["status"] == "FINALIZED"


@pytest.mark.asyncio
async def test_finalize_page_not_found(client, mock_db):
    mock_db.pages.find_one = AsyncMock(return_value=None)

    response = await client.post("/api/pages/507f1f77bcf86cd799439999/finalize")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_finalize_page_requires_sections_confirmed(client, mock_db, sample_page):
    pending_page = {**sample_page, "status": "PENDING"}
    mock_db.pages.find_one = AsyncMock(return_value=pending_page)

    response = await client.post(f'/api/pages/{sample_page["_id"]}/finalize')

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_finalize_page_requires_all_sections_approved(client, mock_db, sample_page):
    confirmed_page = {**sample_page, "status": "SECTIONS_CONFIRMED"}
    mock_db.pages.find_one = AsyncMock(return_value=confirmed_page)
    mock_db.sections.aggregate.return_value.to_list = AsyncMock(
        return_value=[
            {"_id": sample_page["_id"], "sectionCount": 2, "translatedCount": 2, "approvedCount": 1}
        ]
    )

    response = await client.post(f'/api/pages/{sample_page["_id"]}/finalize')

    assert response.status_code == 400
