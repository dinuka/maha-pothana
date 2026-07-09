from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone
from bson import ObjectId
import hashlib
import logging
import re

from app.db.client import get_db
from app.models.page_status import PageStatus
from app.schemas.book import BookResponse, BookUpdate, BookListItem, BookStatsSummary
from app.schemas.book_organization import (
    BuildProgressResponse,
    CancelBuildResponse,
    BuildListItem,
    BuildListPagination,
    BuildListResponse,
    VersionListItem,
    VersionListResponse,
    CreateVersionRequest,
    CreateVersionResponse,
    DownloadResponse,
)
from app.schemas.refs import OwnerRef
from app.services.book_stats import get_books_stats_summary_doc
from app.services.s3 import upload_file, get_presigned_url
from app.tasks.split_pages import split_pages
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/books")
async def list_books(
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    cursor = db.books.find({"owner.id": user_id}).sort("createdAt", -1)
    books = await cursor.to_list(length=100)
    book_ids = [str(book["_id"]) for book in books]
    stats_by_book = await get_books_stats_summary_doc(db, book_ids)
    result = []
    for book in books:
        book_id = str(book["_id"])
        page_count = await db.pages.count_documents({"book.id": book_id})
        result.append(
            BookListItem(
                id=book_id,
                title=book["title"],
                author=book["author"],
                sourceLanguage=book["sourceLanguage"],
                translateLanguages=book.get("translateLanguages", []),
                status=book.get("status", "UPLOADING"),
                thumbnailKey=book.get("thumbnailKey"),
                pageCount=page_count,
                stats=stats_by_book.get(book_id, BookStatsSummary()),
            )
        )
    return result


@router.get("/api/books/available")
async def list_available_books(
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    cursor = db.books.find({"status": "READY"}).sort("createdAt", -1)
    books = await cursor.to_list(length=100)
    book_ids = [str(book["_id"]) for book in books]
    stats_by_book = await get_books_stats_summary_doc(db, book_ids)
    result = []
    for book in books:
        book_id = str(book["_id"])
        page_count = await db.pages.count_documents({"book.id": book_id})
        result.append(
            BookListItem(
                id=book_id,
                title=book["title"],
                author=book["author"],
                sourceLanguage=book["sourceLanguage"],
                translateLanguages=book.get("translateLanguages", []),
                status=book.get("status", "UPLOADING"),
                thumbnailKey=book.get("thumbnailKey"),
                pageCount=page_count,
                stats=stats_by_book.get(book_id, BookStatsSummary()),
            )
        )
    return result


@router.post("/api/books")
async def create_book(
    title: str = Form(...),
    author: str = Form(...),
    sourceLanguage: str = Form(...),
    translateLanguages: list[str] = Form(...),
    description: str | None = Form(None),
    file: UploadFile = File(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    file_data = await file.read()
    file_hash = hashlib.sha256(file_data).hexdigest()

    existing = await db.books.find_one({"fileHash": file_hash})
    if existing:
        raise HTTPException(409, "This book has already been uploaded")

    book_doc = {
        "title": title,
        "author": author,
        "sourceLanguage": sourceLanguage,
        "translateLanguages": translateLanguages,
        "description": description,
        "fileKey": None,
        "fileHash": file_hash,
        "thumbnailKey": None,
        "translatorCount": 1,
        "owner": {"id": user_id},
        "status": "UPLOADING",
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc),
    }
    result = await db.books.insert_one(book_doc)
    book_id = str(result.inserted_id)

    file_key = f"books/{book_id}/original.pdf"
    await upload_file(file_key, file_data, file.content_type or "application/pdf")
    await db.books.update_one({"_id": result.inserted_id}, {"$set": {"fileKey": file_key}})

    logger.info("create_book book_id=%s fileKey=%s queued split_pages", book_id, file_key)

    split_pages.delay(book_id)

    return BookResponse(
        id=book_id,
        title=title,
        author=author,
        sourceLanguage=sourceLanguage,
        translateLanguages=translateLanguages,
        description=description,
        fileKey=file_key,
        owner=OwnerRef(id=user_id),
        status="UPLOADING",
        createdAt=book_doc["createdAt"],
    )


@router.get("/api/books/{book_id}")
async def get_book(book_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    book = await db.books.find_one({"_id": ObjectId(book_id)})

    if not book:
        raise HTTPException(404, "Book not found")

    return BookResponse(
        id=str(book["_id"]),
        title=book["title"],
        author=book["author"],
        sourceLanguage=book["sourceLanguage"],
        translateLanguages=book.get("translateLanguages", []),
        description=book.get("description"),
        fileKey=book.get("fileKey"),
        thumbnailKey=book.get("thumbnailKey"),
        translatorCount=book.get("translatorCount", 1),
        owner=OwnerRef(id=book["owner"]["id"]),
        status=book.get("status", "UPLOADING"),
        createdAt=book.get("createdAt"),
        updatedAt=book.get("updatedAt"),
    )


@router.put("/api/books/{book_id}")
async def update_book(book_id: str, body: BookUpdate, db: AsyncIOMotorDatabase = Depends(get_db)):
    update = {k: v for k, v in body.model_dump().items() if v is not None}

    if not update:
        raise HTTPException(400, "No fields to update")

    update["updatedAt"] = datetime.now(timezone.utc)

    result = await db.books.update_one({"_id": ObjectId(book_id)}, {"$set": update})

    if result.matched_count == 0:
        raise HTTPException(404, "Book not found")

    return {"ok": True}


@router.delete("/api/books/{book_id}")
async def delete_book(book_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    result = await db.books.delete_one({"_id": ObjectId(book_id)})

    if result.deleted_count == 0:
        raise HTTPException(404, "Book not found")

    return {"ok": True}


# --- Epic 5: Book Build endpoints ---


@router.post("/api/books/{book_id}/build")
async def trigger_build(
    book_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Trigger a build of the finalized book."""
    book = await db.books.find_one({"_id": ObjectId(book_id)})
    if not book:
        raise HTTPException(404, "Book not found")

    # Check pre-conditions
    total_pages = await db.pages.count_documents({"book.id": book_id})
    if total_pages == 0:
        raise HTTPException(400, "Book has no pages")

    # Check if a build is already in progress
    active_build = await db.book_builds.find_one({
        "book.id": book_id,
        "status": "BUILDING",
    })
    if active_build:
        raise HTTPException(409, "A build is already in progress")

    # Check for approved translations
    approved_translations = await db.translations.count_documents({
        "isApproved": True,
    })
    # We count approved translations across all sections
    if approved_translations == 0:
        # Check if there are any sections at all
        sections_count = await db.sections.count_documents({})
        if sections_count > 0:
            raise HTTPException(400, "No approved translations — review and approve translations first")

    # Get next version number
    last_version = await db.book_versions.find_one(
        {"bookId": book_id},
        sort=[("versionNumber", -1)],
    )
    version_number = (last_version["versionNumber"] + 1) if last_version else 1

    now = datetime.now(timezone.utc)

    # Create BookVersion
    await db.book_versions.insert_one({
        "bookId": book_id,
        "versionNumber": version_number,
        "label": f"v{version_number}",
        "status": "DRAFT",
        "buildId": None,
        "changelog": None,
        "fileKey": None,
        "createdBy": user_id,
        "totalSections": 0,
        "approvedSections": 0,
        "createdAt": now,
        "updatedAt": now,
    })

    # Create BookBuild
    build_result = await db.book_builds.insert_one({
        "book": {"id": book_id},
        "versionNumber": version_number,
        "status": "BUILDING",
        "currentPage": 0,
        "totalPages": total_pages,
        "fileKey": None,
        "errorMessage": None,
        "buildDurationMs": None,
        "totalSections": 0,
        "approvedSections": 0,
        "createdBy": user_id,
        "createdAt": now,
        "updatedAt": now,
    })
    build_id = str(build_result.inserted_id)

    await db.book_versions.update_one(
        {"bookId": book_id, "versionNumber": version_number},
        {"$set": {"buildId": build_id}},
    )

    # Enqueue the Celery task
    from app.tasks.build_book import build_book as build_book_task

    logger.info("trigger_build book_id=%s version=%s build_id=%s", book_id, version_number, build_id)
    build_book_task.delay(book_id, build_id)

    return {"status": "BUILDING", "versionNumber": version_number, "buildId": build_id}


@router.get("/api/books/{book_id}/builds/latest")
async def get_latest_build(
    book_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Poll the latest build status and progress."""
    # Check for active building build first
    build = await db.book_builds.find_one(
        {"book.id": book_id},
        sort=[("createdAt", -1)],
    )

    if not build:
        return BuildProgressResponse(
            status="NONE",
            message="No builds have been created for this book yet",
        )

    return BuildProgressResponse(
        id=str(build["_id"]),
        bookId=book_id,
        status=build.get("status", "NONE"),
        versionNumber=build.get("versionNumber"),
        currentPage=build.get("currentPage"),
        totalPages=build.get("totalPages"),
        estimatedRemainingMs=build.get("estimatedRemainingMs"),
        startedAt=build.get("createdAt"),
        totalSections=build.get("totalSections"),
        approvedSections=build.get("approvedSections"),
        buildDurationMs=build.get("buildDurationMs"),
        fileKey=build.get("fileKey"),
        completedAt=build.get("completedAt"),
        errorMessage=build.get("errorMessage"),
        failedAt=build.get("failedAt"),
    )


@router.delete("/api/books/{book_id}/builds/latest")
async def cancel_build(
    book_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Cancel the current active build."""
    active_build = await db.book_builds.find_one({
        "book.id": book_id,
        "status": "BUILDING",
    })
    if not active_build:
        raise HTTPException(400, "No active build to cancel")

    build_id = str(active_build["_id"])

    # Try to revoke Celery task
    try:
        from app.tasks.celery_app import celery_app as celery
        celery.control.revoke(build_id, terminate=True, signal="SIGTERM")
    except Exception:
        logger.warning("Failed to revoke Celery task build_id=%s", build_id)

    now = datetime.now(timezone.utc)
    await db.book_builds.update_one(
        {"_id": ObjectId(build_id)},
        {
            "$set": {
                "status": "CANCELLED",
                "errorMessage": "Cancelled by user",
                "updatedAt": now,
                "failedAt": now,
            }
        },
    )

    # Update related version
    version_num = active_build.get("versionNumber")
    if version_num:
        await db.book_versions.update_one(
            {"bookId": book_id, "versionNumber": version_num},
            {"$set": {"status": "ARCHIVED", "updatedAt": now}},
        )

    return CancelBuildResponse(success=True, message="Build cancelled successfully")


@router.get("/api/books/{book_id}/builds")
async def list_builds(
    book_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """List all builds for a book."""
    total = await db.book_builds.count_documents({"book.id": book_id})
    total_pages = max(1, (total + limit - 1) // limit) if total > 0 else 0

    cursor = db.book_builds.find({"book.id": book_id}).sort("createdAt", -1).skip((page - 1) * limit).limit(limit)
    builds = await cursor.to_list(length=limit)

    items = []
    for b in builds:
        creator = None
        if b.get("createdBy"):
            creator_user = await db.users.find_one({"_id": ObjectId(b["createdBy"])})
            if creator_user:
                creator = {"id": b["createdBy"], "name": creator_user.get("name", "Unknown")}

        items.append(
            BuildListItem(
                id=str(b["_id"]),
                versionNumber=b.get("versionNumber", 0),
                status=b.get("status", "UNKNOWN"),
                totalSections=b.get("totalSections"),
                approvedSections=b.get("approvedSections"),
                buildDurationMs=b.get("buildDurationMs"),
                createdBy=creator,
                createdAt=b.get("createdAt"),
                completedAt=b.get("completedAt"),
            )
        )

    return BuildListResponse(
        builds=items,
        pagination=BuildListPagination(
            page=page, limit=limit, total=total, totalPages=total_pages,
        ),
    )


@router.get("/api/books/{book_id}/versions")
async def list_versions(
    book_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """List all versions for a book."""
    cursor = db.book_versions.find({"bookId": book_id}).sort("versionNumber", -1)
    versions = await cursor.to_list(length=100)

    items = []
    for v in versions:
        creator = None
        if v.get("createdBy"):
            creator_user = await db.users.find_one({"_id": ObjectId(v["createdBy"])})
            if creator_user:
                creator = {"id": v["createdBy"], "name": creator_user.get("name", "Unknown")}

        items.append(
            VersionListItem(
                versionNumber=v["versionNumber"],
                label=v.get("label"),
                status=v.get("status", "DRAFT"),
                buildId=v.get("buildId"),
                changelog=v.get("changelog"),
                createdBy=creator,
                totalSections=v.get("totalSections"),
                approvedSections=v.get("approvedSections"),
                createdAt=v.get("createdAt"),
            )
        )

    return VersionListResponse(versions=items)


@router.post("/api/books/{book_id}/versions")
async def create_manual_version(
    book_id: str,
    body: CreateVersionRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Create a manual version (for organizational/tracking purposes)."""
    book = await db.books.find_one({"_id": ObjectId(book_id)})
    if not book:
        raise HTTPException(404, "Book not found")

    max_version = await db.book_versions.find_one(
        {"bookId": book_id},
        sort=[("versionNumber", -1)],
    )
    version_number = (max_version["versionNumber"] + 1) if max_version else 1

    now = datetime.now(timezone.utc)
    await db.book_versions.insert_one({
        "bookId": book_id,
        "versionNumber": version_number,
        "label": body.label,
        "status": "DRAFT",
        "buildId": None,
        "changelog": body.changelog,
        "fileKey": None,
        "createdBy": user_id,
        "totalSections": 0,
        "approvedSections": 0,
        "createdAt": now,
        "updatedAt": now,
    })

    return CreateVersionResponse(
        versionNumber=version_number,
        bookId=book_id,
        label=body.label,
        changelog=body.changelog,
        status="DRAFT",
        fileKey=None,
        createdBy=user_id,
        createdAt=now,
    )


@router.get("/api/books/{book_id}/versions/{version_number}/download")
async def download_version(
    book_id: str,
    version_number: int,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Get a presigned download URL for a version's PDF."""
    version = await db.book_versions.find_one({
        "bookId": book_id,
        "versionNumber": version_number,
    })
    if not version:
        raise HTTPException(404, "Version not found")

    if not version.get("fileKey"):
        raise HTTPException(403, "This version has no downloadable PDF")

    book = await db.books.find_one({"_id": ObjectId(book_id)})
    if not book:
        raise HTTPException(404, "Book not found")

    # Generate presigned URL with 1-hour expiry
    download_url = await get_presigned_url(version["fileKey"], expires=3600)

    # Sanitize book title for filename
    title = book.get("title", "book")
    safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '-')
    filename = f"{safe_title}-v{version_number}.pdf"

    now = datetime.now(timezone.utc)
    expires_at = datetime.fromtimestamp(now.timestamp() + 3600, tz=timezone.utc)

    return DownloadResponse(
        downloadUrl=download_url,
        filename=filename,
        expiresAt=expires_at,
        versionNumber=version_number,
    )
