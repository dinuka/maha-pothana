import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_google_auth_new_user(client, mock_db):
    mock_db.users.find_one = AsyncMock(return_value=None)
    mock_db.users.insert_one = AsyncMock()

    response = await client.post("/api/auth/google", json={
        "googleId": "new-google-id",
        "email": "new@example.com",
        "name": "New User",
        "avatarUrl": "https://example.com/avatar.png",
    })

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "new@example.com"
    assert data["user"]["roles"] == ["EDITOR", "TRANSLATOR"]
    assert data["token"] is not None
    mock_db.users.insert_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_google_auth_existing_user(client, mock_db, sample_user):
    mock_db.users.find_one = AsyncMock(return_value=sample_user)
    mock_db.users.update_one = AsyncMock()

    response = await client.post("/api/auth/google", json={
        "googleId": sample_user["googleId"],
        "email": sample_user["email"],
        "name": sample_user["name"],
        "avatarUrl": sample_user["avatarUrl"],
    })

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["id"] == str(sample_user["_id"])
    assert data["user"]["email"] == sample_user["email"]
    mock_db.users.update_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_me_authenticated(client, mock_db, sample_user):
    mock_db.users.find_one = AsyncMock(return_value=sample_user)

    response = await client.get("/api/auth/me", headers={
        "Authorization": f"Bearer test-token",
    })

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == sample_user["email"]
    assert data["roles"] == ["EDITOR", "TRANSLATOR"]


@pytest.mark.asyncio
async def test_get_me_user_not_found(client, mock_db):
    mock_db.users.find_one = AsyncMock(return_value=None)

    response = await client.get("/api/auth/me", headers={
        "Authorization": "Bearer test-token",
    })

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
