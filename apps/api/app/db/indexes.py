from motor.motor_asyncio import AsyncIOMotorDatabase


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    await db.users.create_index("googleId", unique=True)
    await db.users.create_index("email", unique=True)

    await db.books.create_index("ownerId")
    await db.books.create_index("fileHash")
    await db.books.create_index([("title", "text"), ("author", "text")])

    await db.pages.create_index([("bookId", 1), ("pageNumber", 1)])

    await db.sections.create_index([("pageId", 1), ("sectionOrder", 1)])

    await db.translations.create_index([("sectionId", 1), ("translatorId", 1)], unique=True)
    await db.translations.create_index([("sectionId", 1), ("isApproved", 1)])

    await db.comments.create_index([("sectionId", 1), ("createdAt", 1)])

    await db.invitations.create_index([("bookId", 1), ("userId", 1)], unique=True)

    await db.book_editors.create_index([("bookId", 1), ("userId", 1)], unique=True)

    await db.book_builds.create_index("bookId")
