# Epic 5: Book Organization & Publishing — Architecture Specification

**Date:** 2026-07-09 12:00
**Author:** Architecture Agent
**Epic Reference:** Epic 5 — Book Organization & Publishing
**Business Analysis Reference:** `specs/business-analysis/20260709-1200-epic5-book-organization.md`

---

## 1. State Machine: Translation Review

```
                    ┌──────────────────────────────────────┐
                    │         Translation submitted         │
                    │  (POST /api/sections/{id}/translate)  │
                    └──────────────┬───────────────────────┘
                                   │
                                   ▼
                           ┌───────────────┐
                           │   PENDING     │
                           │  (awaiting    │
                           │   review)     │
                           └───────┬───────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                              │
                    ▼                              ▼
            ┌──────────────┐             ┌──────────────────┐
            │   APPROVED   │             │    REJECTED      │
            │ (isApproved  │             │ (rejected=true,  │
            │  = true)     │             │  rejectedBy=id,  │
            └──────┬───────┘             │  rejectionReason)│
                   │                     └────────┬─────────┘
                   │                              │
                   │                     ┌────────┴─────────┐
                   │                     │  All translations │
                   │                     │  for section are  │
                   │                     │  REJECTED?        │
                   │                     └────────┬─────────┘
                   │                              │
                   │                    ┌─────────┴──────────┐
                   │                    │                    │
                   │              ┌─────▼──────┐      ┌─────▼──────┐
                   │              │    YES     │      │    NO      │
                   │              │ Section    │      │ At least   │
                   │              │ re-enters  │      │ one is     │
                   │              │ translation│      │ APPROVED → │
                   │              │ pool       │      │ stay here  │
                   │              │ (status:   │      └────────────┘
                   │              │  pending)  │
                   │              └────────────┘
                   │
                   │         ┌───────────────────────────────┐
                   │         │   Editor Override              │
                   │         │   (POST /api/sections/{id}/    │
                   │         │    translations by editor)     │
                   │         │   → Auto-approved               │
                   │         │   → Badge: "Editor's Choice"    │
                   │         └───────────────┬───────────────┘
                   │                         │
                   └─────────────┬───────────┘
                                 │
                                 ▼
                    ┌───────────────────────────┐
                    │ All REJECTED translations │
                    │  remain visible in review │
                    │  UI (dimmed + strikethru) │
                    └───────────────────────────┘
```

### State Transitions

| From         | Event                 | To                         | Side Effects                                                                          |
| ------------ | --------------------- | -------------------------- | ------------------------------------------------------------------------------------- |
| PENDING      | Editor clicks Approve | APPROVED                   | `isApproved=true`, `approvedBy=editorId`, audit entry APPROVED                        |
| PENDING      | Editor clicks Reject  | REJECTED                   | `rejected=true`, `rejectedBy=editorId`, `rejectionReason` saved, audit entry REJECTED |
| All REJECTED | (automatic)           | Section re-enters pool     | `Section.status` toggled to pending; notification to translators                      |
| Any state    | Editor submits own    | Editor's Choice (APPROVED) | Auto-approved, labeled "Editor's Choice", badge displayed                             |

### Section Status Computation (derived, not stored)

| Section Condition                                                | Computed Status          |
| ---------------------------------------------------------------- | ------------------------ |
| No translations exist                                            | `pending` (untranslated) |
| At least one translation submitted, none approved, none rejected | `awaiting_review`        |
| At least one translation approved                                | `translated`             |
| All translations rejected, no new submissions                    | `pending_re_translation` |

---

## 2. API Contracts

### 2.1 PUT /api/books/{bookId}/pages/reorder

Batch reorder pages by updating the `order` field on each page.

**Method:** PUT
**Path:** `/api/books/{bookId}/pages/reorder`
**Auth:** EDITOR, SUPER_ADMIN

**Request Body:**

```json
{
  "orders": [
    { "pageId": "507f1f77bcf86cd799439011", "order": 1 },
    { "pageId": "507f1f77bcf86cd799439012", "order": 2 },
    { "pageId": "507f1f77bcf86cd799439013", "order": 3 }
  ]
}
```

**Response — 200 OK:**

```json
{
  "success": true,
  "reorderedCount": 3,
  "pages": [
    { "id": "507f1f77bcf86cd799439011", "order": 1, "pageNumber": 1 },
    { "id": "507f1f77bcf86cd799439012", "order": 2, "pageNumber": 3 },
    { "id": "507f1f77bcf86cd799439013", "order": 3, "pageNumber": 2 }
  ]
}
```

**Error — 400 Bad Request:**

```json
{
  "detail": "Page 507f1f77bcf86cd799439099 does not belong to this book"
}
```

**Error — 409 Conflict:**

```json
{
  "detail": "Page order was modified by another editor. Please refresh and try again."
}
```

**Error — 403 Forbidden:**

```json
{
  "detail": "Only editors can reorder pages"
}
```

**Status Codes:**
| Code | Description |
|------|-------------|
| 200 | Pages reordered successfully |
| 400 | Validation failure (pageId not in book, duplicate orders, etc.) |
| 403 | User is not an editor of this book |
| 409 | Concurrent edit conflict detected |

---

### 2.2 POST /api/books/{bookId}/pages — Add blank page

**Method:** POST
**Path:** `/api/books/{bookId}/pages`
**Auth:** EDITOR, SUPER_ADMIN

**Request Body:**

```json
{
  "insertAfterOrder": 5
}
```

**Response — 201 Created:**

```json
{
  "id": "507f1f77bcf86cd799439099",
  "bookId": "507f1f77bcf86cd799439000",
  "pageNumber": 0,
  "originalPageNumber": "inserted",
  "order": 6,
  "imageKey": null,
  "thumbnailKey": null,
  "status": "PENDING",
  "createdAt": "2026-07-09T12:00:00Z"
}
```

**Error — 400 Bad Request:**

```json
{
  "detail": "insertAfterOrder must be >= 0 and <= page count"
}
```

**Notes:**

- `pageNumber` is set to `0` for all editor-inserted pages (no original PDF numbering)
- `originalPageNumber` is set to the sentinel value `"inserted"`
- All pages with `order > insertAfterOrder` are incremented by 1
- The new page has no source image — `imageKey` and `thumbnailKey` are `null`
- The page starts with `status: PENDING` (no sections)

---

### 2.3 DELETE /api/pages/{pageId} — Delete page and cascade

**Method:** DELETE
**Path:** `/api/pages/{pageId}`
**Auth:** EDITOR, SUPER_ADMIN

**Request Body:** None

**Response — 200 OK:**

```json
{
  "success": true,
  "deleted": {
    "page": 1,
    "sections": 5,
    "translations": 8,
    "comments": 3,
    "aiTextExtractions": 1
  }
}
```

**Error — 400 Bad Request:**

```json
{
  "detail": "Cannot delete the only page of a book. A book must have at least one page."
}
```

**Cascade Deletion:**
All documents referencing the page are deleted atomically:

1. Page document
2. All Section documents where `pageId = pageId`
3. All Translation documents where `sectionId` is in the deleted sections
4. All Comment documents where `sectionId` is in the deleted sections
5. All AITextExtraction documents where `sectionId` is in the deleted sections

**Order Compaction:** After deletion, remaining pages have their `order` values compacted (no gaps, starting from 1).

**Implementation:** Uses a MongoDB session for atomic rollback:

```
session.start_transaction()
  page = pages_collection.find_one_and_delete({_id: pageId})
  sections = sections_collection.find({pageId: pageId}).to_list()
  section_ids = [s._id for s in sections]
  sections_collection.delete_many({_id: {$in: section_ids}})
  translations_collection.delete_many({sectionId: {$in: section_ids}})
  comments_collection.delete_many({sectionId: {$in: section_ids}})
  ai_text_collection.delete_many({sectionId: {$in: section_ids}})
  # Compact order on remaining pages
  remaining_pages = pages_collection.find({bookId: bookId}).sort("order", 1)
  bulk_ops = []
  for i, page in enumerate(remaining_pages, start=1):
      bulk_ops.append(UpdateOne({_id: page._id}, {$set: {order: i}}))
  if bulk_ops:
      pages_collection.bulk_write(bulk_ops)
session.commit_transaction()
```

---

### 2.4 GET /api/books/{bookId}/pages — List/filter/sort pages

**Method:** GET
**Path:** `/api/books/{bookId}/pages`
**Auth:** EDITOR, TRANSLATOR, SUPER_ADMIN

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| filter | string | "all" | `all`, `not_started`, `in_progress`, `completed`, `needs_review` |
| sort | string | "order" | `order`, `translation_percent` |
| order | string | "asc" | `asc`, `desc` |
| page | int | 1 | Page number for pagination |
| limit | int | 20 | Items per page (max 100) |

**Response — 200 OK:**

```json
{
  "pages": [
    {
      "id": "507f1f77bcf86cd799439011",
      "pageNumber": 1,
      "originalPageNumber": "1",
      "order": 1,
      "status": "SECTIONS_CONFIRMED",
      "thumbnailUrl": "https://minio.example.com/books/abc/pages/1-thumb.png?token=...",
      "sectionCount": 5,
      "approvedSectionCount": 3,
      "translationPercent": 60.0,
      "computedStatus": "in_progress"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 45,
    "totalPages": 3
  },
  "stats": {
    "totalPages": 45,
    "totalSections": 320,
    "translatedSections": 210,
    "pendingReviewSections": 80,
    "overallPercent": 65.6
  }
}
```

**Filter Computation:**

- `not_started`: pages where `sectionCount = 0` or `approvedSections = 0`
- `in_progress`: pages where `approvedSections > 0` and `approvedSections < sectionCount`
- `completed`: pages where `approvedSections = sectionCount` and `sectionCount > 0`
- `needs_review`: pages where all sections have submitted translations (none pending), but none approved
- `all`: no filter applied

**Performance:** Compound index `{ bookId: 1, order: 1 }` ensures efficient sorted queries. Filtering by `computedStatus` is applied post-query with server-side aggregation pipeline.

---

### 2.5 GET /api/pages/{pageId}/history — Section edit history

**Method:** GET
**Path:** `/api/pages/{pageId}/history`
**Auth:** EDITOR, SUPER_ADMIN

**Query Parameters:** None (returns all history for the page)

**Response — 200 OK:**

```json
{
  "pageId": "507f1f77bcf86cd799439011",
  "history": [
    {
      "id": "507f1f77bcf86cd799439aaa",
      "editorId": "507f1f77bcf86cd799439001",
      "editorName": "Jane Editor",
      "action": "UPDATE",
      "snapshot": {
        "sections": [
          {
            "id": "sec1",
            "type": "PARAGRAPH",
            "x": 100,
            "y": 200,
            "width": 400,
            "height": 50,
            "sectionOrder": 1
          }
        ]
      },
      "timestamp": "2026-07-09T11:30:00Z"
    }
  ]
}
```

**Status Codes:**

- 200 — History returned
- 404 — Page not found

---

### 2.6 PUT /api/translations/{translationId}/approve — Approve translation

**Method:** PUT
**Path:** `/api/translations/{translationId}/approve`
**Auth:** EDITOR, SUPER_ADMIN

**Request Body:** None

**Response — 200 OK:**

```json
{
  "success": true,
  "translation": {
    "id": "507f1f77bcf86cd799439bbb",
    "sectionId": "507f1f77bcf86cd799439011",
    "translatorId": "507f1f77bcf86cd799439002",
    "translatorName": "Sam Translator",
    "isApproved": true,
    "approvedBy": "507f1f77bcf86cd799439001",
    "approvedAt": "2026-07-09T12:00:00Z",
    "translatedText": "Translated content..."
  }
}
```

**Status Codes:**

- 200 — Translation approved
- 404 — Translation not found
- 409 — Translation already approved or rejected

---

### 2.7 PUT /api/translations/{translationId}/reject — Reject translation

**Method:** PUT
**Path:** `/api/translations/{translationId}/reject`
**Auth:** EDITOR, SUPER_ADMIN

**Request Body:**

```json
{
  "reason": "Translation does not match the source text meaning"
}
```

**Response — 200 OK:**

```json
{
  "success": true,
  "translation": {
    "id": "507f1f77bcf86cd799439bbb",
    "sectionId": "507f1f77bcf86cd799439011",
    "rejected": true,
    "rejectedBy": "507f1f77bcf86cd799439001",
    "rejectionReason": "Translation does not match the source text meaning",
    "rejectedAt": "2026-07-09T12:00:00Z"
  }
}
```

**Status Codes:**

- 200 — Translation rejected
- 400 — Missing `reason` in body (optional, but body must be valid JSON)
- 404 — Translation not found
- 409 — Translation already approved or rejected

---

### 2.8 POST /api/sections/{sectionId}/translations — Editor override translation

**Method:** POST
**Path:** `/api/sections/{sectionId}/translations`
**Auth:** EDITOR, SUPER_ADMIN

**Request Body:**

```json
{
  "translatedText": "Editor's own translation of the section content...",
  "sourceTranslationId": "507f1f77bcf86cd799439bbb"
}
```

**Notes:**

- `sourceTranslationId` is optional — the editor can copy from an existing translation as a starting point (for reference in audit trail)
- The editor's translation is auto-approved (`isApproved: true`)
- The translation is labeled with `translatorId` = the editor's ID and displayed with "Editor's Choice" badge

**Response — 201 Created:**

```json
{
  "id": "507f1f77bcf86cd799439ccc",
  "sectionId": "507f1f77bcf86cd799439011",
  "translatorId": "507f1f77bcf86cd799439001",
  "translatorName": "Jane Editor",
  "isApproved": true,
  "isEditorOverride": true,
  "translatedText": "Editor's own translation of the section content...",
  "createdAt": "2026-07-09T12:00:00Z"
}
```

**Status Codes:**

- 201 — Translation submitted and auto-approved
- 400 — Invalid request body

---

### 2.9 GET /api/books/{bookId}/builds/latest — Poll latest build

**Method:** GET
**Path:** `/api/books/{bookId}/builds/latest`
**Auth:** EDITOR, TRANSLATOR, SUPER_ADMIN

**Response — 200 OK (BUILDING):**

```json
{
  "id": "507f1f77bcf86cd799439ddd",
  "bookId": "507f1f77bcf86cd799439000",
  "status": "BUILDING",
  "versionNumber": 3,
  "currentPage": 23,
  "totalPages": 45,
  "estimatedRemainingMs": 44000,
  "startedAt": "2026-07-09T12:00:00Z"
}
```

**Response — 200 OK (COMPLETED):**

```json
{
  "id": "507f1f77bcf86cd799439ddd",
  "bookId": "507f1f77bcf86cd799439000",
  "status": "COMPLETED",
  "versionNumber": 1,
  "totalSections": 320,
  "approvedSections": 290,
  "buildDurationMs": 520000,
  "fileKey": "books/507f.../versions/1/finalized.pdf",
  "completedAt": "2026-07-09T12:01:30Z"
}
```

**Response — 200 OK (FAILED):**

```json
{
  "id": "507f1f77bcf86cd799439ddd",
  "bookId": "507f1f77bcf86cd799439000",
  "status": "FAILED",
  "versionNumber": 1,
  "errorMessage": "S3 upload failed after 3 retries: connection timeout",
  "failedAt": "2026-07-09T12:01:30Z"
}
```

**Response — 200 OK (no builds exist):**

```json
{
  "status": "NONE",
  "message": "No builds have been created for this book yet"
}
```

**Status Codes:**

- 200 — Build status returned (even NO_BUILDS is 200 with `status: "NONE"`)

---

### 2.10 DELETE /api/books/{bookId}/builds/latest — Cancel current build

**Method:** DELETE
**Path:** `/api/books/{bookId}/builds/latest`
**Auth:** EDITOR, SUPER_ADMIN

**Request Body:** None

**Response — 200 OK:**

```json
{
  "success": true,
  "message": "Build cancelled successfully"
}
```

**Error — 400:**

```json
{
  "detail": "No active build to cancel"
}
```

**Implementation:**

1. Find latest BookBuild with `status: BUILDING`
2. Call `Celery.control.revoke(task_id, terminate=True, signal='SIGTERM')`
3. Update BookBuild status to `FAILED` with `errorMessage: "Cancelled by user"`
4. Clean up any partial artifacts

---

### 2.11 GET /api/books/{bookId}/builds — List all builds

**Method:** GET
**Path:** `/api/books/{bookId}/builds`
**Auth:** EDITOR, SUPER_ADMIN

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | int | 1 | Page number |
| limit | int | 20 | Items per page (max 100) |

**Response — 200 OK:**

```json
{
  "builds": [
    {
      "id": "507f1f77bcf86cd799439ddd",
      "versionNumber": 1,
      "status": "COMPLETED",
      "totalSections": 320,
      "approvedSections": 290,
      "buildDurationMs": 52000,
      "createdBy": {
        "id": "507f1f77bcf86cd799439001",
        "name": "Jane Editor"
      },
      "createdAt": "2026-07-09T12:00:00Z",
      "completedAt": "2026-07-09T12:01:30Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 3,
    "totalPages": 1
  }
}
```

---

### 2.12 GET /api/books/{bookId}/versions — List all versions

**Method:** GET
**Path:** `/api/books/{bookId}/versions`
**Auth:** EDITOR, TRANSLATOR, SUPER_ADMIN

**Response — 200 OK:**

```json
{
  "versions": [
    {
      "versionNumber": 3,
      "label": "v3 — Final Proofread",
      "status": "FINALIZED",
      "buildId": "507f1f77bcf86cd799439ddd",
      "changelog": "Fixed translations on pages 5-8",
      "createdBy": {
        "id": "507f1f77bcf86cd799439001",
        "name": "Jane Editor"
      },
      "totalSections": 320,
      "approvedSections": 310,
      "createdAt": "2026-07-09T11:00:00Z"
    }
  ]
}
```

---

### 2.13 POST /api/books/{bookId}/versions — Create manual version

**Method:** POST
**Path:** `/api/books/{bookId}/versions`
**Auth:** EDITOR, SUPER_ADMIN

**Request Body:**

```json
{
  "label": "Draft for proofreading v2",
  "changelog": "Added translations for chapters 1-5"
}
```

**Response — 201 Created:**

```json
{
  "versionNumber": 2,
  "bookId": "507f1f77bcf86cd799439000",
  "label": "Draft for proofreading v2",
  "changelog": "Added translations for chapters 1-5",
  "status": "DRAFT",
  "fileKey": null,
  "createdBy": "507f1f77bcf86cd799439001",
  "createdAt": "2026-07-09T12:00:00Z"
}
```

**Notes:**

- Manual versions have `buildId = null` and `fileKey = null` (no associated build or PDF)
- The version is recorded for organizational/tracking purposes
- Only when a build is run against this version does `fileKey` and `buildId` get populated
- Version number auto-increments from the current max for the book

---

### 2.14 GET /api/books/{bookId}/versions/{versionNumber}/download — Download version PDF

**Method:** GET
**Path:** `/api/books/{bookId}/versions/{versionNumber}/download`
**Auth:** EDITOR, TRANSLATOR, SUPER_ADMIN (translators are allowed to download)

**Query Parameters:** None

**Response — 200 OK:**

```json
{
  "downloadUrl": "https://minio.example.com/books/507f1f77/versions/3/finalized.pdf?X-Amz-Algorithm=...&X-Amz-Expires=3600&X-Amz-Signature=...",
  "filename": "book-title-v3.pdf",
  "expiresAt": "2026-07-09T13:00:00Z",
  "versionNumber": 3
}
```

**Error — 404:**

```json
{
  "detail": "Version not found or has no associated PDF file"
}
```

**Error — 403:**

```json
{
  "detail": "This version is not finalized and has no downloadable PDF"
}
```

**Implementation:** Generates a presigned S3 URL with 1-hour expiry. The `filename` is derived from the book title sanitized and the version number.

---

## 3. Error Handling Strategies

### 3.1 Concurrent Page Reorder

**Problem:** Two editors could reorder pages simultaneously, causing conflicting `order` values.

**Solution — Atomic Bulk Write with Version Check:**

```
1. Backend receives list of { pageId, order } pairs
2. Validate all pageIds belong to bookId (single query with $in filter)
3. Start atomic bulkWrite operation:
   for each pair:
       result = pages_collection.bulk_write([
           UpdateOne(
               { _id: pageId, bookId: bookId },
               { $set: { order: newOrder, updatedAt: now } }
           )
       ])
4. If matchedCount != 1 for any pair → the page was deleted or book changed
5. Return 200 on all success, 409 on any mismatch
```

**Frontend Strategy:**

- Optimistic update: immediately move page in local list
- Invalidate query on success
- On error (409): revert optimistic update, show toast "Page order was modified by another editor — refresh to see latest"

### 3.2 Build Cancellation

**Problem:** A long build must be cancellable without leaving partially built artifacts.

**Solution:**

```
1. DELETE /api/books/{bookId}/builds/latest
2. Backend finds BookBuild with status=BUILDING
3. Backend calls Celery control.revoke(task_id, terminate=True, signal='SIGTERM')
4. Backend updates BookBuild: status=CANCELLED, errorMessage="Cancelled by user"
5. Backend updates BookVersion: status=ARCHIVED (if it was DRAFT)
6. Frontend receives 200, shows "Build cancelled" message
```

**Cleanup:** The Celery worker's `build_book` task catches `WorkerTerminate` or `sigterm` and performs cleanup:

- Delete any partial PDF from S3
- Mark the BookBuild as CANCELLED (if not already)
- The build document remains for audit history

### 3.3 Page Deletion Cascade — Atomic Rollback

**Problem:** Deleting a page must cascade to sections, translations, comments, and AI text extractions. If any step fails, all changes should be rolled back.

**Solution: MongoDB Sessions with Transaction:**

```
async with await client.start_session() as session:
    async with session.start_transaction():
        page = await pages_collection.find_one_and_delete(
            {"_id": pageId}, session=session
        )
        sections = await sections_collection.find(
            {"pageId": pageId}, session=session
        ).to_list(None)
        section_ids = [s["_id"] for s in sections]

        # Delete in dependency order
        await translations_collection.delete_many(
            {"sectionId": {"$in": section_ids}}, session=session
        )
        await comments_collection.delete_many(
            {"sectionId": {"$in": section_ids}}, session=session
        )
        await ai_text_collection.delete_many(
            {"sectionId": {"$in": section_ids}}, session=session
        )
        await sections_collection.delete_many(
            {"_id": {"$in": section_ids}}, session=session
        )

        # Compact order on remaining pages
        remaining = await pages_collection.find(
            {"bookId": bookId}
        ).sort("order", 1).to_list(None)
        ops = [
            UpdateOne({"_id": p["_id"]}, {"$set": {"order": i}})
            for i, p in enumerate(remaining, start=1)
        ]
        if ops:
            await pages_collection.bulk_write(ops, session=session)
```

**Note:** MongoDB replica sets are required for transactions. In single-node dev mode, use a write concern majority and accept the weaker guarantee. Production should always use a replica set.

### 3.4 Translation Approval Conflict

**Problem:** Two editors attempt to approve/reject the same translation simultaneously.

**Solution:** Use `find_one_and_update` with a condition filter to implement optimistic locking:

```
# Approve — only if translation is still pending
result = await translations_collection.find_one_and_update(
    {
        "_id": translationId,
        "isApproved": False,
        "rejected": {"$ne": True}
    },
    {"$set": {"isApproved": True, "approvedBy": editorId, ...}},
    return_document=True
)
if result is None:
    return "Translation has already been approved or rejected" (409 Conflict)
```

---

## 4. Performance Targets

### 4.1 Page List with Filters

**Target:** <500ms for books with up to 500 pages

**Strategy:**

1. **Compound Index:** `{ bookId: 1, order: 1 }` for sorted queries
2. **Aggregation Pipeline:** Use MongoDB aggregation with $lookup to compute section counts per page:
   ```
   db.pages.aggregate([
     { $match: { bookId: bookId } },
     { $sort: { order: 1 } },
     { $lookup: {
         from: "sections",
         localField: "_id",
         foreignField: "pageId",
         pipeline: [
           { $lookup: {
             from: "translations",
             localField: "_id",
             foreignField: "sectionId",
             pipeline: [
               { $match: { isApproved: true } },
               { $count: "approved" }
             ],
             as: "approvedTranslations"
           }},
           { $addFields: {
             approvedCount: { $ifNull: [{ $arrayElemAt: ["$approvedTranslations.approved", 0] }, 0] }
           }},
           { $group: {
             _id: "$pageId",
             totalSections: { $sum: 1 },
             approvedSections: { $sum: "$approvedCount" }
           }}
         ],
         as: "sections"
     }},
     { $addFields: {
         sectionCount: { $ifNull: [{ $arrayElemAt: ["$sections.totalSections", 0] }, 0] },
         approvedSections: { $ifNull: [{ $arrayElemAt: ["$sections.approvedSections", 0] }, 0] },
         computedStatus: { $switch: {
             branches: [
               { case: { $eq: ["$sectionCount", 0] }, then: "not_started" },
               { case: { $eq: ["$approvedSections", 0] }, then: "not_started" },
               { case: { $eq: ["$approvedSections", "$sectionCount"] }, then: "completed" }
             ],
             default: "in_progress"
         }}
     }},
     { $match: { computedStatus: filterValue } },  # optional filter stage
     { $skip: (page - 1) * limit },
     { $limit: limit }
   ])
   ```
3. **Caching:** Stats aggregation (summary bar) can be cached in Redis with 10s TTL
4. **Materialized Counts:** For very large books (>500 pages), consider storing section counts directly on the Page document via a post-save hook on Translation approve/reject

### 4.2 Build Processing

**Target:** 1 page per 2 seconds (250-page book ~8 minutes)

**Strategy:**

1. Page image rendering is the bottleneck — use parallel processing:
   - Fetch pages, sections, and translations in parallel bulk queries
   - Render pages sequentially but use async I/O for S3 uploads
2. Image processing stack:
   - Use **Pillow** (PIL) for image manipulation (text overlay on section bounding boxes)
   - Use **img2pdf** or **reportlab** for PDF compilation
   - Consider **WeasyPrint** if HTML-to-PDF rendering is more performant
3. Memory management for large books:
   - Process batches of 10 pages at a time
   - Upload each batch to S3 as a partial PDF
   - Merge partial PDFs at the end
   - Release page images from memory after each batch
4. Progress tracking: store `currentPage` in Redis under `build:{buildId}:progress`, update after each page

### 4.3 Build Progress Polling

**Target:** 3s initial interval with exponential backoff

**Strategy:**

```
Frontend polling logic:
  1. Start with 3s interval
  2. After 30s of building → increase to 5s interval
  3. After 2min of building → increase to 10s interval
  4. After 5min of building → increase to 15s interval (cap)
  5. On status COMPLETED or FAILED → stop polling
  6. On network error → retry after 5s (max 3 retries)
  7. If user navigates away → stop polling, resume on return
```

Backend optimizations:

- Polling endpoint returns cached status (updated by Celery task on each page completion)
- Cache in Redis: `build:{buildId}:latest` TTL 10s
- If cache miss → query MongoDB directly

---

## 5. Security Considerations

### 5.1 Role-Based Access

| Endpoint                                      | Required Role                   |
| --------------------------------------------- | ------------------------------- |
| PUT /api/books/{bookId}/pages/reorder         | EDITOR, SUPER_ADMIN             |
| POST /api/books/{bookId}/pages                | EDITOR, SUPER_ADMIN             |
| DELETE /api/pages/{pageId}                    | EDITOR, SUPER_ADMIN             |
| GET /api/books/{bookId}/pages                 | EDITOR, TRANSLATOR, SUPER_ADMIN |
| GET /api/pages/{pageId}/history               | EDITOR, SUPER_ADMIN             |
| PUT /api/translations/{translationId}/approve | EDITOR, SUPER_ADMIN             |
| PUT /api/translations/{translationId}/reject  | EDITOR, SUPER_ADMIN             |
| POST /api/sections/{sectionId}/translations   | EDITOR, SUPER_ADMIN             |
| GET /api/books/{bookId}/builds/latest         | EDITOR, TRANSLATOR, SUPER_ADMIN |
| DELETE /api/books/{bookId}/builds/latest      | EDITOR, SUPER_ADMIN             |
| GET /api/books/{bookId}/builds                | EDITOR, SUPER_ADMIN             |
| GET /api/books/{bookId}/versions              | EDITOR, TRANSLATOR, SUPER_ADMIN |
| POST /api/books/{bookId}/versions             | EDITOR, SUPER_ADMIN             |
| GET /api/books/{bookId}/versions/{v}/download | EDITOR, TRANSLATOR, SUPER_ADMIN |

**Key Decision:** Download is available to TRANSLATOR role because translators need to see the final output of their work. All other write operations require EDITOR.

### 5.2 Input Validation

| Endpoint                                 | Validation                                                                     |
| ---------------------------------------- | ------------------------------------------------------------------------------ |
| PUT /api/books/{bookId}/pages/reorder    | Each `pageId` must belong to `bookId`; all orders must be contiguous from 1..N |
| POST /api/books/{bookId}/pages           | `insertAfterOrder` must be >= 0 and <= current page count                      |
| DELETE /api/pages/{pageId}               | Minimum one page — delete disabled if only page remains                        |
| PUT /api/translations/{id}/approve       | Translation must be in PENDING state (not already approved/rejected)           |
| PUT /api/translations/{id}/reject        | Translation must be in PENDING state                                           |
| POST /api/sections/{id}/translations     | `translatedText` required, max length 10000 chars                              |
| DELETE /api/books/{bookId}/builds/latest | Only one active BUILDING build can exist per book                              |

### 5.3 Cross-Book Validation

- All book-scoped endpoints validate that the requesting user has access to the book (is editor or translator)
- `DELETE /api/pages/{pageId}` validates that page's `bookId` allows the requesting user
- `PUT /api/books/{bookId}/pages/reorder` validates all pageIds belong to the book before making changes
- Presigned download URLs cannot be re-used across different books (URL scope-bound to the specific S3 key)

### 5.4 Download URL Security

- **Expiry:** 1 hour (configurable via `DOWNLOAD_URL_EXPIRY_SECONDS` env var)
- **Filename sanitization:** `{bookTitle}-v{versionNumber}.pdf` where `bookTitle` is stripped of path traversal characters (`..`, `/`, `\`, null bytes)
- **Rate limiting:** Max 10 download URL generations per user per 5-minute window
- **No direct S3 access:** Users must go through the API; S3 bucket policy prevents direct listing

### 5.5 Audit Trail

Every approve/reject/reorder action is recorded:

```
TranslationHistoryItem {
  action: "APPROVED" | "REJECTED" | "EDITOR_SUBMIT",
  performedBy: userId,
  performedByName: "Jane Editor",
  translationId: "...",
  sectionId: "...",
  pageNumber: 3,
  sectionOrder: 2,
  createdAt: timestamp
}
```

For page reordering, an audit entry is logged:

```
AuditLog {
  action: "PAGE_REORDER",
  performedBy: userId,
  bookId: "...",
  metadata: {
    previousOrder: [{pageId, order: 1}, {pageId, order: 2}],
    newOrder: [{pageId, order: 2}, {pageId, order: 1}]
  },
  timestamp: timestamp
}
```

---

## 6. Data Model Changes Summary

| Entity      | Field Change             | Type      | Notes                                    |
| ----------- | ------------------------ | --------- | ---------------------------------------- |
| Page        | `order` (new)            | int       | Display order, independent of pageNumber |
| Translation | `rejected` (new)         | boolean?  | True when editor rejects                 |
| Translation | `rejectedBy` (new)       | ObjectId? | Editor who rejected                      |
| Translation | `rejectionReason` (new)  | string?   | Editor's reason for rejection            |
| BookBuild   | `versionNumber` (new)    | int       | Auto-incremented per book                |
| BookBuild   | `errorMessage` (new)     | string?   | Build failure reason                     |
| BookBuild   | `buildDurationMs` (new)  | int?      | Build time on completion                 |
| BookBuild   | `totalSections` (new)    | int?      | Sections at time of build                |
| BookBuild   | `approvedSections` (new) | int?      | Approved translations at build time      |
| BookBuild   | `createdBy` (new)        | ObjectId  | Editor who triggered build               |
| BookVersion | (entirely new entity)    | —         | Version history snapshots                |

---

## 7. New Indexes

| Collection      | Index                              | Purpose                                        |
| --------------- | ---------------------------------- | ---------------------------------------------- |
| `pages`         | `{ bookId: 1, order: 1 }`          | Fast sorted page list queries                  |
| `book_builds`   | `{ bookId: 1, versionNumber: -1 }` | Latest build lookup, version history           |
| `book_versions` | `{ bookId: 1, versionNumber: -1 }` | Version history listing                        |
| `translations`  | `{ sectionId: 1, rejected: 1 }`    | Query rejected translations for re-entry logic |

---

## 8. Frontend Component Architecture

### Key React Query Hooks (Epic 5)

```typescript
// Page Organization
useReorderPages(bookId: string)         → useMutation for PUT /api/books/{bookId}/pages/reorder
useAddPage(bookId: string)              → useMutation for POST /api/books/{bookId}/pages
useDeletePage(bookId: string)           → useMutation for DELETE /api/pages/{pageId}
usePageHistory(pageId: string)          → useQuery for GET /api/pages/{pageId}/history
usePages(bookId, filters)              → useQuery for GET /api/books/{bookId}/pages?filter=...

// Translation Review
useApproveTranslation(translationId)    → useMutation for PUT approve
useRejectTranslation(translationId)     → useMutation for PUT reject
useSubmitEditorTranslation(sectionId)   → useMutation for POST translations
useSectionTranslations(sectionId)       → useQuery for GET all translations

// Book Build & Versions
useBuildBook(bookId: string)            → useMutation for POST build
useLatestBuild(bookId: string)          → useQuery with refetchInterval: 3000 (polling)
useCancelBuild(bookId: string)          → useMutation for DELETE builds/latest
useBuildList(bookId: string)            → useQuery for GET builds
useVersionList(bookId: string)          → useQuery for GET versions
useCreateManualVersion(bookId: string)  → useMutation for POST versions
useDownloadUrl(bookId, versionNumber)   → useQuery for GET download
```

### Key UX Flows

**Page Reorder (Drag & Drop):**

1. Use a drag-and-drop library (e.g., `@dnd-kit/core` or `react-beautiful-dnd`)
2. On drag start: apply visual feedback (opacity, elevation)
3. On drag over: show horizontal drop indicator line
4. On drop: immediately reorder the list optimistically, fire mutation
5. On mutation success: invalidate page list query
6. On mutation error: revert to previous order, show toast

**Translation Review (Multi-card):**

- Fetch all translations for section on mount
- Represent each with a card showing translator info, text, actions
- Approve: optimistic update card to green, fire approval mutation
- Reject: show inline reason input, on submit fire rejection mutation
- Editor override: textarea at bottom of cards list, submit creates auto-approved translation
- After any approval/rejection: invalidate section translations query and page stats

**Build Progress:**

- On build trigger: navigate to build panel, start polling every 3s
- Progress bar with "Building page X of Y" label
- Estimated time remaining computed from `(totalPages - currentPage) * avgTimePerPage`
- Cancel button visible during BUILDING state
- On COMPLETE: show download button with presigned URL
- On FAILED: show error message with retry button

---

## 9. Implementation Notes for Developers

### Backend File Changes

**New files needed:**

- `app/api/book_organization.py` or add to `app/api/books.py` and `app/api/pages.py`
- `app/schemas/book_organization.py` — Pydantic models for new request/response bodies
- Test files for all new endpoints

**Files to modify:**

- `app/api/books.py` — add reorder, add page, builds, versions endpoints
- `app/api/pages.py` — add delete page, history endpoint
- `app/api/translations.py` — add approve, reject endpoints
- `app/api/sections.py` — add editor override translation endpoint
- `app/tasks/build_book.py` — enhance with versioning support
- `app/services/s3.py` — add presigned URL generation for version downloads (if not already present)
- `app/db/indexes.py` — add new indexes

### Frontend File Changes

**New files needed:**

- Sidebar page list with drag-and-drop support
- Translation review panel component
- Build panel component (progress, cancel, download)
- Version history panel

**Files to modify:**

- Existing BookConsole component to integrate new panels
- Page list to show progress bars and drag handles
- Translation panel to integrate review flow
- Book detail page to include build button and version history

### Test Coverage Requirements

**Backend tests (pytest):**

- Test page reorder with valid and invalid payloads
- Test page reorder conflict (simultaneous update)
- Test page addition and deletion, including cascade
- Test delete of the last page (should fail)
- Test translation approval and rejection
- Test that rejected translations trigger re-entry logic
- Test editor override auto-approval
- Test build trigger with pre-conditions
- Test build cancellation
- Test build polling endpoint
- Test version listing and download URL generation

**Frontend tests (Vitest):**

- Test drag-and-drop page reorder interaction
- Test filter/sort UI with various states
- Test translation approve/reject button states
- Test progress bar rendering with different completion values
- Test build polling UI transitions (BUILDING → COMPLETED → DOWNLOAD)
- Test empty states and error states
