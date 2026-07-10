from app.tasks.celery_app import celery_app
from app.config import settings
from app.models.build_status import BuildStatus, VersionStatus
from app.services.book_pdf import build_book_markdown, resolve_section_content
from app.services.book_html import build_book_html, build_book_pdf_via_weasyprint
from app.services.s3 import get_s3, upload_file
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _build_book(book_id: str, build_id: str | None = None):
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]

    try:
        book = await db.books.find_one({"_id": ObjectId(book_id)})
        if not book:
            logger.info("build_book book_id=%s not found", book_id)
            return {"error": "Book not found"}

        # Get all pages ordered by `order` field
        pages_cursor = db.pages.find({"book.id": book_id}).sort("order", 1)
        pages = await pages_cursor.to_list(length=1000)
        total_pages = len(pages)

        total_sections = 0
        approved_section_count = 0
        sections_by_page: list[tuple[int, list]] = []

        # Process each page
        for page_idx, page in enumerate(pages):
            page_id = str(page["_id"])
            current_page = page_idx + 1

            # Check if build was cancelled
            if build_id:
                current_build = await db.book_builds.find_one({"_id": ObjectId(build_id)})
                if current_build and current_build.get("status") == BuildStatus.CANCELLED:
                    logger.info("build_book book_id=%s cancelled at page %s", book_id, current_page)
                    return {"status": BuildStatus.CANCELLED, "book_id": book_id}

            # Get sections for this page, ordered by sectionOrder
            sections_cursor = db.sections.find({"page.id": page_id}).sort("sectionOrder", 1)
            sections = await sections_cursor.to_list(length=200)
            page_section_count = len(sections)
            total_sections += page_section_count

            # For each section, get the most recently approved translation and resolve content
            page_contents = []
            for sec in sections:
                section_id = str(sec["_id"])
                latest_approved = await db.translations.find_one(
                    {"section.id": section_id, "isApproved": True},
                    sort=[("approvedAt", -1)],
                )
                if latest_approved:
                    approved_section_count += 1
                page_contents.append(resolve_section_content(sec, latest_approved))

            sections_by_page.append((page.get("pageNumber", current_page), page_contents))

            # Update progress in BookBuild
            now = datetime.now(timezone.utc)
            await db.book_builds.update_one(
                {"_id": ObjectId(build_id)} if build_id else {"book.id": book_id, "status": BuildStatus.BUILDING},
                {
                    "$set": {
                        "currentPage": current_page,
                        "totalPages": total_pages,
                        "totalSections": total_sections,
                        "approvedSections": approved_section_count,
                        "estimatedRemainingMs": (total_pages - current_page) * 2000,
                        "updatedAt": now,
                    }
                },
            )

        # Compile the finalized PDF from source text, transliteration, and approved translations
        version_doc = await db.book_versions.find_one(
            {"bookId": book_id},
            sort=[("versionNumber", -1)],
        )
        version_number = version_doc["versionNumber"] if version_doc else 1

        book_title = book.get("title", "Untitled Book")

        html_text = build_book_html(book_title, sections_by_page)
        pdf_bytes = build_book_pdf_via_weasyprint(html_text)

        finalized_key = f"books/{book_id}/versions/{version_number}/finalized.pdf"
        await upload_file(finalized_key, pdf_bytes, "application/pdf")

        html_key = f"books/{book_id}/versions/{version_number}/finalized.html"
        await upload_file(html_key, html_text.encode("utf-8"), "text/html")

        markdown_key = f"books/{book_id}/versions/{version_number}/finalized.md"
        markdown_text = build_book_markdown(book_title, sections_by_page)
        await upload_file(markdown_key, markdown_text.encode("utf-8"), "text/markdown")

        # Fetch build to record duration
        build_doc = None
        if build_id:
            build_doc = await db.book_builds.find_one({"_id": ObjectId(build_id)})

        start_time = build_doc.get("createdAt", datetime.now(timezone.utc)) if build_doc else datetime.now(timezone.utc)
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        build_duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

        now = datetime.now(timezone.utc)
        await db.book_builds.update_one(
            {"_id": ObjectId(build_id)} if build_id else {"book.id": book_id, "status": BuildStatus.BUILDING},
            {
                "$set": {
                    "fileKey": finalized_key,
                    "htmlFileKey": html_key,
                    "markdownFileKey": markdown_key,
                    "status": BuildStatus.COMPLETED,
                    "currentPage": total_pages,
                    "totalPages": total_pages,
                    "totalSections": total_sections,
                    "approvedSections": approved_section_count,
                    "buildDurationMs": build_duration_ms,
                    "completedAt": now,
                    "updatedAt": now,
                }
            },
        )

        # Update BookVersion to FINALIZED
        await db.book_versions.update_one(
            {"bookId": book_id, "versionNumber": version_number},
            {
                "$set": {
                    "status": VersionStatus.FINALIZED,
                    "fileKey": finalized_key,
                    "htmlFileKey": html_key,
                    "markdownFileKey": markdown_key,
                    "totalSections": total_sections,
                    "approvedSections": approved_section_count,
                    "updatedAt": now,
                }
            },
        )

        logger.info(
            "build_book book_id=%s completed status=COMPLETED pages=%s sections=%s approved=%s",
            book_id, total_pages, total_sections, approved_section_count,
        )

        return {
            "book_id": book_id,
            "status": BuildStatus.COMPLETED,
            "versionNumber": version_number,
            "totalSections": total_sections,
            "approvedSections": approved_section_count,
        }

    except Exception as exc:
        logger.warning("build_book book_id=%s failed error=%s", book_id, exc)
        now = datetime.now(timezone.utc)
        await db.book_builds.update_one(
            {"_id": ObjectId(build_id)} if build_id else {"book.id": book_id, "status": BuildStatus.BUILDING},
            {
                "$set": {
                    "status": BuildStatus.FAILED,
                    "errorMessage": str(exc),
                    "failedAt": now,
                    "updatedAt": now,
                }
            },
        )
        raise exc

    finally:
        client.close()


@celery_app.task(bind=True, max_retries=3)
def build_book(self, book_id: str, build_id: str | None = None):
    logger.info("build_book started book_id=%s build_id=%s", book_id, build_id)
    return run_async(_build_book(book_id, build_id))
