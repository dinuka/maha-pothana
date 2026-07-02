import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone

from app.main import app
from app.config import settings
from app.db.client import get_db
from app.api.deps import get_current_user


def make_mock_cursor(to_list_return=None):
    cursor = MagicMock()
    cursor.sort = MagicMock(return_value=cursor)
    cursor.to_list = AsyncMock(return_value=to_list_return or [])
    cursor.limit = MagicMock(return_value=cursor)
    cursor.skip = MagicMock(return_value=cursor)
    cursor.batch_size = MagicMock(return_value=cursor)
    return cursor


@pytest.fixture(autouse=True)
def patch_settings():
    with patch("app.config.settings.mongodb_url", "mongodb://test:27017/test"):
        yield


@pytest.fixture
def mock_db():
    db = MagicMock()

    for col_name in [
        "users", "books", "pages", "sections",
        "translations", "invitations", "comments",
        "book_editors", "book_builds",
    ]:
        col = MagicMock()
        col.find = MagicMock(return_value=make_mock_cursor())
        col.aggregate = MagicMock(return_value=make_mock_cursor())
        col.find_one = AsyncMock(return_value=None)
        col.insert_one = AsyncMock()
        col.update_one = AsyncMock()
        col.delete_one = AsyncMock()
        col.delete_many = AsyncMock()
        col.count_documents = AsyncMock(return_value=0)
        col.create_index = AsyncMock()
        col.distinct = AsyncMock(return_value=[])
        setattr(db, col_name, col)

    return db


@pytest.fixture
def client(mock_db):
    async def override_get_db():
        return mock_db

    async def override_get_current_user():
        return "507f1f77bcf86cd799439011"

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    c = AsyncClient(transport=transport, base_url="http://test")
    return c


@pytest.fixture
def sample_user():
    return {
        "_id": "507f1f77bcf86cd799439011",
        "googleId": "google-123",
        "email": "test@example.com",
        "name": "Test User",
        "avatarUrl": "https://example.com/avatar.png",
        "roles": ["EDITOR", "TRANSLATOR"],
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc),
    }


@pytest.fixture
def sample_book():
    return {
        "_id": "507f1f77bcf86cd799439012",
        "title": "Test Book",
        "author": "Test Author",
        "sourceLanguage": "si",
        "translateLanguages": ["ta", "en"],
        "description": "A test book",
        "fileKey": "books/user123/hash.pdf",
        "fileHash": "abc123",
        "thumbnailKey": None,
        "translatorCount": 1,
        "owner": {"id": "507f1f77bcf86cd799439011"},
        "status": "UPLOADING",
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc),
    }


@pytest.fixture
def sample_page():
    return {
        "_id": "507f1f77bcf86cd799439013",
        "book": {"id": "507f1f77bcf86cd799439012"},
        "pageNumber": 1,
        "originalPageNumber": "1",
        "imageKey": "books/user123/pages/1.png",
        "width": 800,
        "height": 1200,
        "status": "PENDING",
        "createdAt": datetime.now(timezone.utc),
    }


@pytest.fixture
def sample_section():
    return {
        "_id": "507f1f77bcf86cd799439014",
        "page": {"id": "507f1f77bcf86cd799439013"},
        "sectionOrder": 1,
        "type": "PARAGRAPH",
        "x": 10,
        "y": 10,
        "width": 780,
        "height": 200,
        "originalText": "Original Sinhala text",
        "croppedImageKey": None,
    }


@pytest.fixture
def sample_translation():
    return {
        "_id": "507f1f77bcf86cd799439015",
        "section": {"id": "507f1f77bcf86cd799439014"},
        "translator": {"id": "507f1f77bcf86cd799439011"},
        "translatedText": "Translated text",
        "exactLetterTranslation": "Exact letter translation",
        "isApproved": False,
        "approvedBy": None,
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc),
    }
