import pytest
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_list_users(client, mock_db, sample_user):
    mock_db.users.find.return_value.to_list = AsyncMock(return_value=[sample_user])

    response = await client.get("/api/users")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["email"] == "test@example.com"
    assert data[0]["roles"] == ["EDITOR", "TRANSLATOR"]


@pytest.mark.asyncio
async def test_update_roles(client, mock_db, sample_user):
    mock_db.users.update_one = AsyncMock()
    mock_db.users.update_one.return_value.matched_count = 1

    response = await client.put(
        f'/api/users/{sample_user["_id"]}/roles',
        json={"roles": ["ADMIN", "EDITOR"]},
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True
    mock_db.users.update_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_roles_user_not_found(client, mock_db):
    mock_db.users.update_one = AsyncMock()
    mock_db.users.update_one.return_value.matched_count = 0

    response = await client.put(
        f'/api/users/507f1f77bcf86cd799439999/roles',
        json={"roles": ["ADMIN"]},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_invite_translator(client, mock_db, sample_book, sample_user):
    mock_db.books.find_one = AsyncMock(return_value=sample_book)
    mock_db.users.find_one = AsyncMock(return_value=sample_user)
    mock_db.invitations.find_one = AsyncMock(return_value=None)
    mock_db.invitations.insert_one = AsyncMock()

    response = await client.post(
        f'/api/books/{sample_book["_id"]}/invite',
        json={"email": "invitee@example.com"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "PENDING"
    mock_db.invitations.insert_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_invite_translator_book_not_found(client, mock_db):
    mock_db.books.find_one = AsyncMock(return_value=None)

    response = await client.post(
        f'/api/books/507f1f77bcf86cd799439999/invite',
        json={"email": "invitee@example.com"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_invite_translator_user_not_found(client, mock_db, sample_book):
    mock_db.books.find_one = AsyncMock(return_value=sample_book)
    mock_db.users.find_one = AsyncMock(return_value=None)

    response = await client.post(
        f'/api/books/{sample_book["_id"]}/invite',
        json={"email": "unknown@example.com"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_invite_translator_already_invited(client, mock_db, sample_book, sample_user):
    mock_db.books.find_one = AsyncMock(return_value=sample_book)
    mock_db.users.find_one = AsyncMock(return_value=sample_user)
    mock_db.invitations.find_one = AsyncMock(return_value={"_id": "existing-invite"})

    response = await client.post(
        f'/api/books/{sample_book["_id"]}/invite',
        json={"email": "invitee@example.com"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_block_translator(client, mock_db):
    mock_db.invitations.update_one = AsyncMock()
    mock_db.invitations.update_one.return_value.matched_count = 1

    response = await client.post(
        f'/api/books/507f1f77bcf86cd799439012/translators/507f1f77bcf86cd799439011/block',
    )

    assert response.status_code == 200
    assert response.json()["status"] == "BLOCKED"


@pytest.mark.asyncio
async def test_block_translator_not_found(client, mock_db):
    mock_db.invitations.update_one = AsyncMock()
    mock_db.invitations.update_one.return_value.matched_count = 0

    response = await client.post(
        f'/api/books/507f1f77bcf86cd799439012/translators/user999/block',
    )

    assert response.status_code == 404
