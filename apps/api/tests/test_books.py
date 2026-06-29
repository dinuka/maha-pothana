import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId


@pytest.mark.asyncio
async def test_list_books(client, mock_db, sample_book):
    mock_db.books.find.return_value.to_list = AsyncMock(return_value=[sample_book])
    mock_db.pages.count_documents = AsyncMock(return_value=5)

    response = await client.get("/api/books", headers={
        "Authorization": "Bearer test-token",
    })

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test Book"
    assert data[0]["pageCount"] == 5


@pytest.mark.asyncio
async def test_create_book(client, mock_db, sample_book):
    mock_db.books.find_one = AsyncMock(return_value=None)
    mock_db.books.insert_one = AsyncMock()
    mock_db.books.insert_one.return_value.inserted_id = sample_book["_id"]

    with patch("app.api.books.upload_file") as mock_upload:
        with patch("app.api.books.split_pages") as mock_split:
            response = await client.post(
                "/api/books",
                data={
                    "title": "Test Book",
                    "author": "Test Author",
                    "sourceLanguage": "si",
                    "translateLanguages": ["ta", "en"],
                    "description": "A test book",
                },
                files={"file": ("test.pdf", b"%PDF-1.4 mock pdf content", "application/pdf")},
                headers={"Authorization": "Bearer test-token"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Book"
    assert data["status"] == "UPLOADING"
    mock_upload.assert_called_once()
    mock_split.delay.assert_called_once()


@pytest.mark.asyncio
async def test_create_book_duplicate(client, mock_db, sample_book):
    mock_db.books.find_one = AsyncMock(return_value=sample_book)

    response = await client.post(
        "/api/books",
        data={
            "title": "Duplicate Book",
            "author": "Test Author",
            "sourceLanguage": "si",
            "translateLanguages": ["ta"],
        },
        files={"file": ("test.pdf", b"%PDF-1.4 mock pdf content", "application/pdf")},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 409
    assert "already been uploaded" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_book(client, mock_db, sample_book):
    mock_db.books.find_one = AsyncMock(return_value=sample_book)

    response = await client.get(f'/api/books/{sample_book["_id"]}')

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Book"
    assert data["author"] == "Test Author"
    assert data["sourceLanguage"] == "si"


@pytest.mark.asyncio
async def test_get_book_not_found(client, mock_db):
    mock_db.books.find_one = AsyncMock(return_value=None)

    response = await client.get("/api/books/507f1f77bcf86cd799439999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_book(client, mock_db):
    mock_db.books.update_one = AsyncMock()
    mock_db.books.update_one.return_value.matched_count = 1

    response = await client.put(
        f'/api/books/507f1f77bcf86cd799439012',
        json={"title": "Updated Title", "author": "Updated Author"},
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True
    mock_db.books.update_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_book_not_found(client, mock_db):
    mock_db.books.update_one = AsyncMock()
    mock_db.books.update_one.return_value.matched_count = 0

    response = await client.put(
        f'/api/books/507f1f77bcf86cd799439999',
        json={"title": "Updated Title"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_book(client, mock_db):
    mock_db.books.delete_one = AsyncMock()
    mock_db.books.delete_one.return_value.deleted_count = 1

    response = await client.delete(f'/api/books/507f1f77bcf86cd799439012')
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_book_not_found(client, mock_db):
    mock_db.books.delete_one = AsyncMock()
    mock_db.books.delete_one.return_value.deleted_count = 0

    response = await client.delete(f'/api/books/507f1f77bcf86cd799439999')
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_build_book(client, mock_db, sample_book):
    mock_db.books.find_one = AsyncMock(return_value=sample_book)

    with patch("app.tasks.build_book.build_book") as mock_build:
        response = await client.post(
            f'/api/books/{sample_book["_id"]}/build'
        )

    assert response.status_code == 200
    assert response.json()["status"] == "BUILDING"
    mock_build.delay.assert_called_once()


@pytest.mark.asyncio
async def test_build_book_not_found(client, mock_db):
    mock_db.books.find_one = AsyncMock(return_value=None)

    response = await client.post("/api/books/507f1f77bcf86cd799439999/build")
    assert response.status_code == 404
