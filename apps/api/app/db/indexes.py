from motor.motor_asyncio import AsyncIOMotorDatabase


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    await db.users.create_index("googleId", unique=True)
    await db.users.create_index("email", unique=True)

    await db.books.create_index("owner.id")
    await db.books.create_index("fileHash")
    await db.books.create_index([("title", "text"), ("author", "text")])

    await db.pages.create_index([("book.id", 1), ("pageNumber", 1)])
    await db.pages.create_index([("book.id", 1), ("status", 1), ("pageNumber", 1)])
    await db.pages.create_index([("book.id", 1), ("order", 1)])

    await db.sections.create_index([("page.id", 1), ("sectionOrder", 1)])

    await db.translations.create_index([("section.id", 1), ("translator.id", 1)], unique=True)
    await db.translations.create_index([("section.id", 1), ("isApproved", 1)])
    await db.translations.create_index([("section.id", 1), ("rejected", 1)])
    await db.translations.create_index([("createdAt", -1)])
    await db.translations.create_index([("translator.id", 1), ("createdAt", -1)])

    await db.translation_activity.create_index([("bookId", 1), ("createdAt", -1)])
    await db.translation_activity.create_index([("bookId", 1), ("action", 1), ("createdAt", -1)])

    await db.comments.create_index([("section.id", 1), ("createdAt", 1)])

    await db.invitations.create_index([("book.id", 1), ("user.id", 1)], unique=True)

    await db.book_editors.create_index([("book.id", 1), ("user.id", 1)], unique=True)

    await db.book_builds.create_index("book.id")
    await db.book_builds.create_index([("book.id", 1), ("versionNumber", -1)])

    await db.book_versions.create_index([("bookId", 1), ("versionNumber", -1)])

    await db.translation_drafts.create_index(
        [("sectionId", 1), ("translatorId", 1)], unique=True
    )
    await db.translation_drafts.create_index("createdAt", expireAfterSeconds=86400)

    await db.ai_text_extractions.create_index("sectionId", unique=True)
    await db.ai_text_extractions.create_index("status")

    await db.transliterations.create_index(
        [("sectionId", 1), ("targetScript", 1)], unique=True
    )

    await db.system_config.create_index("key", unique=True)

    await db.redis_progress.create_index("bookId")

    await db.book_stats.create_index("bookId", unique=True)

    await db.section_edit_history.create_index([("pageId", 1), ("timestamp", -1)])

    await db.generation_runs.create_index("sectionId", unique=True)

    await db.model_usage.create_index([("sectionId", 1), ("createdAt", -1)])
    await db.model_usage.create_index([("callType", 1), ("createdAt", -1)])
    await db.model_usage.create_index([("model", 1), ("createdAt", -1)])
    await db.model_usage.create_index("createdAt")
