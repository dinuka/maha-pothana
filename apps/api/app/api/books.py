from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone
from bson import ObjectId
import hashlib
import logging

from app.db.client import get_db
from app.models.page_status import PageStatus
from app.schemas.book import BookResponse, BookUpdate, BookListItem, BookStatsSummary
from app.schemas.refs import OwnerRef
from app.services.book_stats import get_books_stats_summary_doc
from app.services.s3 import upload_file
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
    book_doc["fileKey"] = file_key

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


@router.post("/api/books/{book_id}/build")
async def build_book(book_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    book = await db.books.find_one({"_id": ObjectId(book_id)})

    if not book:
        raise HTTPException(404, "Book not found")

    total_pages = await db.pages.count_documents({"book.id": book_id})
    finalized_pages = await db.pages.count_documents(
        {"book.id": book_id, "status": PageStatus.FINALIZED}
    )
    if total_pages == 0 or finalized_pages < total_pages:
        raise HTTPException(400, "All pages must be finalized before building the book")

    from app.tasks.build_book import build_book as build_book_task

    logger.info("build_book endpoint book_id=%s queued build_book task", book_id)
    build_book_task.delay(book_id)

    return {"status": "BUILDING"}
