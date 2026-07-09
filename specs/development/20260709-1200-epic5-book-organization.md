# Epic 5: Book Organization & Publishing — Development Spec

**Date:** 2026-07-09
**Epic:** Book Organization & Publishing
**Status:** Complete (backend + frontend)

---

## Backend Endpoints Implemented

All endpoints live under `apps/api/app/api/` and are already deployed and tested.

### Pages (`apps/api/app/api/pages.py`)

| Method   | Path                                 | Description                                                                                                     |
| -------- | ------------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| `GET`    | `/api/books/{book_id}/pages`         | List pages with filter, sort, pagination (supports aggregation pipeline for computed status)                    |
| `PUT`    | `/api/books/{book_id}/pages/reorder` | Batch-update page order fields with optimistic locking                                                          |
| `POST`   | `/api/books/{book_id}/pages`         | Add a blank page after a specified order position; shifts subsequent pages                                      |
| `DELETE` | `/api/pages/{page_id}`               | Delete a page and cascade all child documents (sections, translations, etc.); compacts order on remaining pages |
| `GET`    | `/api/pages/{page_id}/history`       | Fetch section edit history for a specific page                                                                  |

### Sections (`apps/api/app/api/sections.py`)

| Method | Path                                         | Description                                                                                                         |
| ------ | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `PUT`  | `/api/translations/{translation_id}/approve` | Approve a translation with optimistic locking (prevents double-approval)                                            |
| `PUT`  | `/api/translations/{translation_id}/reject`  | Reject a translation with optional reason; triggers re-entry logic if all translations for the section are rejected |
| `POST` | `/api/sections/{section_id}/translations`    | Editor override -- submit an auto-approved translation as "Editor's Choice"                                         |

### Books -- Build & Versioning (`apps/api/app/api/books.py`)

| Method   | Path                                                      | Description                                                                                        |
| -------- | --------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `POST`   | `/api/books/{book_id}/build`                              | Trigger a new build; creates a BookVersion + BookBuild document, enqueues Celery `build_book` task |
| `GET`    | `/api/books/{book_id}/builds/latest`                      | Poll the latest build status and progress                                                          |
| `DELETE` | `/api/books/{book_id}/builds/latest`                      | Cancel the current active build; revokes Celery task, marks build as CANCELLED                     |
| `GET`    | `/api/books/{book_id}/builds`                             | List all builds with pagination                                                                    |
| `GET`    | `/api/books/{book_id}/versions`                           | List all versions with creator info                                                                |
| `POST`   | `/api/books/{book_id}/versions`                           | Create a manual/organizational version (no build required)                                         |
| `GET`    | `/api/books/{book_id}/versions/{version_number}/download` | Get a presigned download URL (1-hour expiry) with sanitized filename                               |

### Background Task (`apps/api/app/tasks/build_book.py`)

Real PDF compilation using reportlab with:

- Cover page (title, author, version info)
- Per-page content with sections and translations
- Font embedding for Sinhala/Tamil/Sanskrit
- Version tracking via BookVersion document
- S3 upload of finalized PDF

---

## API Contracts Summary

### Page Reorder

```
PUT /api/books/{book_id}/pages/reorder
Request:  { "orders": [{ "pageId": "...", "order": 1 }, ...] }
Response: { "success": true, "reorderedCount": 3, "pages": [...] }
```

### Add Page

```
POST /api/books/{book_id}/pages
Request:  { "insertAfterOrder": 5 }
Response: { "id": "...", "pageNumber": 0, "originalPageNumber": "inserted", "order": 6, ... }
```

### Delete Page

```
DELETE /api/pages/{page_id}
Response: { "success": true, "deleted": { "page": 1, "sections": 3, ... } }
```

### Page History

```
GET /api/pages/{page_id}/history
Response: { "pageId": "...", "history": [{ "id": "...", "editorId": "...", "editorName": "...", "action": "UPDATE", "snapshot": {...}, "timestamp": "..." }] }
```

### Approve Translation

```
PUT /api/translations/{translation_id}/approve
Response: { "success": true, "translation": { "id": "...", "sectionId": "...", "isApproved": true, ... } }
```

### Reject Translation

```
PUT /api/translations/{translation_id}/reject
Request:  { "reason": "Needs revision" }
Response: { "success": true, "translation": { "id": "...", "rejected": true, "rejectionReason": "...", ... } }
```

### Editor Override

```
POST /api/sections/{section_id}/translations
Request:  { "translatedText": "...", "sourceTranslationId": "..." }
Response: { "id": "...", "sectionId": "...", "translatorName": "...", "isApproved": true, "isEditorOverride": true, "translatedText": "...", "createdAt": "..." }
```

### Build & Versioning

| Endpoint                     | Response Shape                                                                                   |
| ---------------------------- | ------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------- | ------ | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `POST /build`                | `{ "status": "BUILDING", "versionNumber": 1, "buildId": "..." }`                                 |
| `GET /builds/latest`         | `{ "id": "...", "status": "BUILDING                                                              | COMPLETED                                                                                      | FAILED | CANCELLED | NONE", "currentPage": 5, "totalPages": 50, "totalSections": 100, "approvedSections": 80, "buildDurationMs": 12345, "fileKey": "...", "errorMessage": null }` |
| `DELETE /builds/latest`      | `{ "success": true, "message": "Build cancelled successfully" }`                                 |
| `GET /builds`                | `{ "builds": [...], "pagination": { "page": 1, "limit": 20, "total": 5, "totalPages": 1 } }`     |
| `GET /versions`              | `{ "versions": [{ "versionNumber": 1, "label": "v1", "status": "DRAFT                            | COMPLETED", "buildId": "...", "changelog": "...", "createdBy": {...}, "createdAt": "..." }] }` |
| `POST /versions`             | `{ "versionNumber": 2, "bookId": "...", "label": "...", "changelog": "...", "status": "DRAFT" }` |
| `GET /versions/{v}/download` | `{ "downloadUrl": "...", "filename": "...", "expiresAt": "...", "versionNumber": 1 }`            |

---

## Frontend Component Architecture

### New API Client Module: `apps/web/lib/api/bookOrganization.ts`

Contains all Epic 5 API client functions:

- `approveTranslation`, `rejectTranslation`, `editorOverrideTranslation`
- `reorderPages`, `addBlankPage`, `deletePage`, `getPageHistory`
- `triggerBuild`, `getLatestBuild`, `cancelBuild`, `getBuilds`, `getVersions`, `getDownloadUrl`

All functions use `apiFetchBrowser` from `@/lib/apiClientBrowser` for authenticated requests.

### New Component: TranslationReview (`apps/web/app/books/[bookId]/review/page.tsx`)

Page-level component with:

- `"use client"` directive
- Fetches book, pages, sections, and translation data
- Section navigation (previous/next)
- Side-by-side card layout for each submitted translation
- Approve/Reject buttons per card
- Reject with optional reason textarea
- Editor override textarea with "Copy from [translator]" buttons
- Section image at top for reference
- Inline `Record<string, React.CSSProperties>` styles

### Updated: BookConsolePage (`apps/web/app/books/[bookId]/page.tsx`)

Enhanced with:

- Summary stats bar at top (total pages, sections, translated %)
- Filter/sort bar with status filter dropdown + sort dropdown + "Review Translations" link
- Page grid with per-page progress bar, reorder (up/down) buttons, delete button
- "Add Blank Page" button at bottom
- Build panel (build button, progress bar, cancel button, download link)
- Version history section with toggle expand/collapse
- Inline `Record<string, React.CSSProperties>` styles

---

## Data Flow

### Translation Review Flow

1. Editor navigates to `/books/{bookId}/review`
2. Page fetches book detail, then pages, then sections from first page
3. Section navigation allows editor to browse through sections
4. For each section, all non-approved translations are fetched
5. Editor can:
   - **Approve**: calls `PUT /api/translations/{id}/approve` -> translation marked approved
   - **Reject**: calls `PUT /api/translations/{id}/reject` with optional reason -> section may re-enter pool
   - **Override**: types in textarea or clicks "Copy from [translator]" to pre-fill, then submits via `POST /api/sections/{section_id}/translations` -> creates auto-approved editor translation

### Reorder Flow

1. Editor clicks up/down arrows on page items in BookConsolePage
2. Frontend recalculates the order values based on current page ordering
3. Calls `PUT /api/books/{book_id}/pages/reorder` with `{ orders: [{ pageId, order }] }`
4. API uses bulk write with optimistic locking; returns updated orders
5. On error, frontend re-fetches pages to restore consistent state

### Build Flow

1. Editor clicks "Build Book" button in Build Panel
2. Frontend calls `POST /api/books/{book_id}/build`
3. API creates BookVersion + BookBuild, enqueues Celery task
4. Frontend starts polling `GET /api/books/{book_id}/builds/latest` every 3 seconds
5. When build shows `status: "COMPLETED"`, download button becomes enabled
6. Clicking download fetches presigned URL from `GET /api/books/{book_id}/versions/{v}/download`
7. User can cancel via `DELETE /api/books/{book_id}/builds/latest`

### Version History Flow

1. On page load, version section is collapsed
2. Clicking "Show" triggers `GET /api/books/{book_id}/versions`
3. Display version list with version number, label, status, creator, date
4. Status-colored badges indicate COMPLETED, DRAFT, or FAILED versions

---

## Key Implementation Decisions

1. **Inline Styles**: All new frontend components use `Record<string, React.CSSProperties>` style objects (no CSS Modules for new pages, per project conventions).

2. **No React Query**: All data fetching uses `useState` + `useEffect` with manual polling for progress states.

3. **Named Exports**: All new utility functions use named exports (the review page uses default export per file-name-match convention).

4. **Arrow Functions**: All components and utilities use arrow functions with `const`.

5. **"use client"**: All interactive components use the `"use client"` directive.

6. **API Client**: New functions in `apps/web/lib/api/bookOrganization.ts` use `apiFetchBrowser` from `@/lib/apiClientBrowser` for all calls.

7. **Confirmation for Delete**: Uses `window.confirm()` dialog before page deletion.

8. **Build Polling Strategy**: Polls every 3 seconds while a build is in progress, stops on completion/error/cancellation.

9. **Error Handling**: API calls are wrapped in try/catch with user-friendly error messages displayed inline.

10. **Up/Down Reorder**: Uses simple up/down buttons that swap positions and recalculate order.

---

## Test Results

### Backend (apps/api)

```
108 passed in 5.15s
```

Covers: auth, books CRUD, stats, pages, sections (approve/reject/override), translation draft, translation history, detection, users, AI text.

### Frontend (apps/web) -- After Changes

```
10 test files, 69 tests passed (no regressions)
```

Existing tests continue to pass. No test files were modified; only source files were added/updated.

### Type Check

```
pnpm check-types: passed (api + web + ui)
```

---

## Files Created/Modified

### Created

- `specs/development/20260709-1200-epic5-book-organization.md` -- This spec
- `apps/web/lib/api/bookOrganization.ts` -- API client functions
- `apps/web/app/books/[bookId]/review/page.tsx` -- TranslationReview page

### Modified

- `apps/web/app/books/[bookId]/page.tsx` -- Updated BookConsolePage with Epic 5 features

---

## Future Considerations

- **Drag-and-drop**: Replace up/down buttons with HTML5 drag-and-drop or @dnd-kit library for page reordering
- **Notifications**: Real-time build completion via WebSocket or SSE
- **Bulk Approve**: "Approve All" button per section with multiple translator submissions
- **PDF Preview**: In-browser PDF preview using react-pdf or similar
- **Diff View**: Side-by-side comparison of different translator versions for the same section
- **Continuation-only Review**: Start review from last unreviewed section instead of first page
