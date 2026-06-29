from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone
import hashlib

from app.db.client import get_db
from app.schemas.book import BookCreate, BookResponse, BookUpdate, BookListItem
from app.services.s3 import upload_file
from app.tasks.split_pages import split_pages
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/api/books")
async def list_books(
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    cursor = db.books.find({"ownerId": user_id}).sort("createdAt", -1)
    books = await cursor.to_list(length=100)
    result = []
    for book in books:
        page_count = await db.pages.count_documents({"bookId": str(book["_id"])})
        result.append(
            BookListItem(
                id=str(book["_id"]),
                title=book["title"],
                author=book["author"],
                sourceLanguage=book["sourceLanguage"],
                translateLanguages=book.get("translateLanguages", []),
                status=book.get("status", "UPLOADING"),
                thumbnailKey=book.get("thumbnailKey"),
                pageCount=page_count,
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

    file_key = f"books/{user_id}/{file_hash}.pdf"
    upload_file(file_key, file_data, file.content_type or "application/pdf")

    book_doc = {
        "title": title,
        "author": author,
        "sourceLanguage": sourceLanguage,
        "translateLanguages": translateLanguages,
        "description": description,
        "fileKey": file_key,
        "fileHash": file_hash,
        "thumbnailKey": None,
        "translatorCount": 1,
        "ownerId": user_id,
        "status": "UPLOADING",
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc),
    }
    result = await db.books.insert_one(book_doc)
    book_id = str(result.inserted_id)

    split_pages.delay(book_id)

    return BookResponse(
        id=book_id,
        title=title,
        author=author,
        sourceLanguage=sourceLanguage,
        translateLanguages=translateLanguages,
        description=description,
        fileKey=file_key,
        ownerId=user_id,
        status="UPLOADING",
        createdAt=book_doc["createdAt"],
    )


@router.get("/api/books/{book_id}")
async def get_book(book_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    from bson import ObjectId
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
        ownerId=book.get("ownerId", ""),
        status=book.get("status", "UPLOADING"),
        createdAt=book.get("createdAt"),
        updatedAt=book.get("updatedAt"),
    )


@router.put("/api/books/{book_id}")
async def update_book(book_id: str, body: BookUpdate, db: AsyncIOMotorDatabase = Depends(get_db)):
    from bson import ObjectId
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
    from bson import ObjectId
    result = await db.books.delete_one({"_id": ObjectId(book_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, "Book not found")
    return {"ok": True}


@router.post("/api/books/{book_id}/build")
async def build_book(book_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    from bson import ObjectId
    book = await db.books.find_one({"_id": ObjectId(book_id)})
    if not book:
        raise HTTPException(404, "Book not found")
    from app.tasks.build_book import build_book as build_book_task
    build_book_task.delay(book_id)
    return {"status": "BUILDING"}
