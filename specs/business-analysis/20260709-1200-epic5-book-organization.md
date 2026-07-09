# Epic 5: Book Organization & Publishing — Expanded User Stories

**Date:** 2026-07-09 12:00
**Author:** Business Analysis Agent
**Epic Reference:** Epic 5 — Book Organization & Publishing

---

## Context

Epic 5 covers the final stages of the book translation workflow: after sections have been detected, confirmed, and translated, editors need tools to organize the book structure, track translation progress, review and approve translations, and build the finalized output PDF. These four user stories define the complete editor workflow from post-translation through publishing.

This document expands the minimal stories defined in `user-stories.md` with detailed, implementation-ready acceptance criteria and API/service considerations.

---

## User Stories

### US-5.1: Organize Pages & Sections

**As an** editor
**I want to** reorder, add, and delete pages; and continue editing section metadata
**So that** the final book structure is correct before building.

**Acceptance Criteria:**

**Page Reordering (Drag & Drop):**

- The book console displays a page list view showing all pages sorted by their `order` field (defaults to `pageNumber` on creation)
- Each page item shows: thumbnail, `pageNumber`, `originalPageNumber` (if different), section count, and translation progress bar
- Editor can drag any page item vertically within the list to change its display order
- During drag, a visual drop indicator (horizontal line) shows where the page will land
- On drop, the frontend sends a batch `PUT /api/books/{bookId}/pages/reorder` request with the new order array `[{ pageId, order }]`
- The backend updates the `order` field on each affected page document atomically
- The `pageNumber` field remains unchanged — it always reflects the original PDF page number
- After reorder, the page list immediately reflects the new order without a page reload
- Undo/redo is supported for reorder actions within the current session

**Add Page:**

- An "Add Page" button is available at the bottom of the page list and between any two pages
- Clicking "Add Page" inserts a new blank Page document with:
  - `pageNumber = 0` (marks it as editor-inserted, not from original PDF)
  - `originalPageNumber = "inserted"` (special sentinel value)
  - `order =` the position where it was inserted (all subsequent pages' order values are shifted up by 1)
  - `imageKey = null`, `thumbnailKey = null` (no source image — blank placeholder)
  - `status = PENDING`
- The inserted page appears in the list immediately
- Editor can add sections to a blank page via the canvas editor, just like a regular page

**Delete Page:**

- Each page has a "Delete" action (icon button or context menu item)
- Clicking "Delete" shows a confirmation dialog:
  - Title: "Delete Page N?"
  - Body: "This will permanently delete the page and all {N} sections on it. This action cannot be undone."
  - Buttons: "Cancel" and "Delete" (destructive, red)
- On confirmation, the frontend calls `DELETE /api/pages/{pageId}`
- The backend deletes the Page document and all associated Section, Translation, Comment, and AITextExtraction documents
- Remaining pages' `order` values are compacted (no gaps)
- The page is removed from the list immediately
- Minimum one page constraint: if the book has only one page, the delete action is disabled with a tooltip "A book must have at least one page"

**Edit Section Content, Position, Type:**

- Editors can navigate to any page's canvas editor from the page list
- Existing section editing capabilities (drag, resize, type change from Epic 3) remain available even after sections are confirmed
- Re-opening a page with confirmed sections loads the saved section positions into the canvas for further editing
- A "Save Changes" button sends updated sections to `PUT /api/pages/{pageId}/sections`
- Changes are tracked via `SectionEditHistory`

**Version History for Page Changes:**

- Each time sections are saved, a new entry is appended to `SectionEditHistory` with a snapshot of all sections on that page
- A "History" panel on the page editor shows a timeline of saves with timestamps and editor names
- Editors can view past snapshots (read-only overlay on the canvas)
- Editors can restore a previous snapshot, which replaces current sections with the historical version

**API Endpoints:**

- `PUT /api/books/{bookId}/pages/reorder` — batch reorder pages `{ orders: [{ pageId: string, order: number }] }`
- `POST /api/books/{bookId}/pages` — add a blank page at a given position `{ insertAfterOrder: number }`
- `DELETE /api/pages/{pageId}` — delete page and all child data
- `GET /api/pages/{pageId}/history` — fetch section edit history for a page

---

### US-5.2: Filter & Sort Translation Progress

**As an** editor
**I want to** filter pages by translation status and sort them by completion metrics
**So that** I can quickly identify incomplete work and track overall progress.

**Acceptance Criteria:**

**Filter by Translation Status:**

- A filter bar at the top of the page list provides the following options:
  - **All** — show all pages regardless of status
  - **Not Started** — pages where zero sections have any submitted translation
  - **In Progress** — pages where at least one section has a submitted translation but not all sections have an approved translation
  - **Completed** — pages where every section has at least one approved translation
  - **Needs Review** — pages where all sections have submitted translations pending editor approval
- Filter chips are visually distinct with color coding:
  - Not Started: gray
  - In Progress: blue
  - Completed: green
  - Needs Review: amber/orange
- Filter state is persisted in the URL query string (e.g., `?filter=in_progress`) for shareable links
- Active filter count is displayed: "Showing 12 of 45 pages"

**Sort Options:**

- Sort dropdown with choices:
  - Page order (default, ascending) — uses the `order` field
  - Translation % ascending — least completed first
  - Translation % descending — most completed first
  - Page order descending
- Sorting is applied on top of the active filter
- A sort indicator (arrow) shows the current sort direction

**Visual Progress Bar Per Page:**

- Each page in the list displays a progress bar showing `approvedSections / totalSections`
- Progress bar color follows:
  - 0%: gray
  - 1–99%: blue gradient
  - 100%: green
- Progress percentage label to the right of the bar (e.g., "75%")
- Animated transition when progress changes (e.g., after a translation is approved)

**Summary Statistics:**

- A stats bar above the page list shows:
  - Total pages: `45`
  - Total sections: `320`
  - Translated sections: `210` (sections with at least one approved translation)
  - Overall completion: `65%`
  - Sections pending review: `80`
- Stats update in real-time when translations are approved/rejected (via polling or WebSocket)

**Responsiveness & Edge Cases:**

- The filter/sort bar is sticky (remains visible while scrolling through the page list)
- When a filter returns zero results, show an empty state: "No pages match the selected filter" with a "Clear filter" button
- When a book has no sections on any page (pre-detection), show: "Process pages first to see translation progress"
- Filter and sort work correctly with paginated page lists

**API Endpoints:**

- `GET /api/books/{bookId}/pages?filter={status}&sort={field}&order={asc|desc}&page={n}&limit={20}`
- `GET /api/books/{bookId}/stats` — aggregate progress stats (already exists)

---

### US-5.3: Review Translations

**As an** editor
**I want to** review all submitted translations for each section, approve or reject them, and provide my own translation if needed
**So that** only high-quality, accurate translations make it into the final book.

**Acceptance Criteria:**

**Translation Review Console:**

- The review console is accessible from the page list (clicking a section with submitted translations) or from a dedicated "Review" tab
- The console shows one section at a time with the cropped section image at the top for reference
- Below the image, all submitted translations for that section are displayed side by side (2-up for N=2, 3-up for N=3, etc.)
- If the translator count N is 1, a single translation card fills the width
- The layout is responsive: on narrow screens, translations stack vertically

**Translation Cards:**

- Each translation card contains:
  - Translator name and avatar
  - Submission timestamp (relative: "2 hours ago" + absolute on hover)
  - Language badge (if multi-language book)
  - The translated text in a readable font, with word-wrap preserving paragraph breaks
  - Action buttons: Approve (green checkmark), Reject (red X)
  - Status badge: "Pending", "Approved", "Rejected"
- Approved translations have a green badge and are visually elevated (highlighted border)
- Rejected translations are dimmed with strikethrough text and a red badge

**Approve Multiple Translations:**

- Editor can approve multiple translations for the same section if they convey the same meaning accurately
- When multiple translations are approved, all are marked with `isApproved: true`
- The section is considered "translated" and does not need further work
- For build purposes, the most recently approved translation is used (or a configurable preference)

**Reject Translations:**

- Clicking "Reject" shows an optional text area: "Reason for rejection (optional)"
- If a reason is provided, it is saved to `Translation.rejectionReason`
- On reject, the Translation document is updated: `rejected: true`, `rejectedBy: editorId`, `rejectionReason: string`
- The translator receives a notification (in-app) that their translation was rejected, with the reason if provided

**Editor Override (Own Translation):**

- An "Editor Translation" section is available below the submitted translations
- The editor can type their own translation text into a text area
- The editor can reference any submitted translation by clicking "Copy" on a translation card
- On save, the editor's translation is stored as a regular Translation document with `translatorId` set to the editor's ID and `isApproved: true` (auto-approved since editor provided it)
- The editor's translation is labeled with an "Editor's Choice" badge

**Re-entry Logic for Rejected Translations:**

- If ALL translations for a section are rejected, the section status transitions back to "pending translation"
- The section re-enters the translation pool and appears in the "Next" queue for translators
- A notification is sent: "Section on page N needs re-translation — all previous translations were rejected"
- Previously rejected translators are NOT excluded — they may submit an improved translation
- The section remains in this state until at least one translation is approved

**Audit Trail:**

- Every approve/reject action is recorded in `TranslationHistoryItem` with action type APPROVED or REJECTED
- The `SectionEditHistory` or a dedicated `ReviewAuditLog` captures who performed each action and when

**Edge Cases:**

- If a translator was blocked after submitting, their translation is still shown in the review UI with a "Blocked User" label but the editor can still approve/reject it
- If the translator count changes after translations were submitted, existing translations remain visible; only the display layout adjusts
- When the editor overrides, the original translator's submission remains visible alongside the editor's version

**API Endpoints:**

- `GET /api/sections/{sectionId}/translations` — fetch all translations for a section
- `PUT /api/translations/{translationId}/approve` — approve a translation
- `PUT /api/translations/{translationId}/reject` — reject a translation (body: `{ reason?: string }`)
- `POST /api/sections/{sectionId}/translations` — editor submits their own translation (body: `{ translatedText: string }`)

---

### US-5.4: Build Finalized Book

**As an** editor
**I want to** generate the finalized translated book as a PDF with all approved translations
**So that** it can be downloaded, shared, or published.

**Acceptance Criteria:**

**Build Pre-conditions:**

- The "Build Book" button is enabled only when the book has:
  - At least one page with sections
  - At least one approved translation
- If pre-conditions are not met, the button is disabled with a tooltip explaining what is missing:
  - "No sections detected — process pages first"
  - "No approved translations — review and approve translations first"
- A summary panel next to the build button shows:
  - Total sections: 320
  - Approved sections: 290 (90.6%)
  - Untranslated sections: 30 (sections with no translation at all)
  - Sections pending review: 15 (submitted but not yet approved/rejected)
  - Warning if untranslated + pending > 0: "This build will skip {N} sections without approved translations"

**Trigger Build:**

- Clicking "Build Book" opens a confirmation dialog:
  - Title: "Build Finalized Book"
  - Body: "This will generate a PDF from all approved translations. {N} sections without approved translations will use the original source text as a placeholder. Continue?"
  - Options: "Cancel" and "Build"
- On confirmation, the frontend calls `POST /api/books/{bookId}/build`
- The backend creates a `BookBuild` document with `status: BUILDING`
- A `BookVersion` is also created in `DRAFT` status referencing the build

**Async Processing:**

- The build runs asynchronously via a Celery task (`build_book`)
- The Celery task:
  1. Fetches all pages ordered by `order` field
  2. For each page, fetches all sections ordered by `sectionOrder`
  3. For each section, gets the most recently approved translation text (or falls back to original text if none approved)
  4. Lays out the translated text onto the page image using the section bounding boxes
  5. Generates a PDF from the annotated page images
  6. Uploads the PDF to S3 at `books/{bookId}/versions/{versionNumber}/finalized.pdf`
  7. Updates the `BookBuild.fileKey` and sets `status: COMPLETED`
  8. Updates the `BookVersion` status to `FINALIZED`
- If the task fails:
  - `BookBuild.status` is set to `FAILED`
  - `BookBuild.errorMessage` stores the error details
  - `BookVersion.status` remains `DRAFT`
  - The editor can retry

**Progress Indication:**

- The frontend polls `GET /api/books/{bookId}/builds/latest` every 3 seconds while status is BUILDING
- A progress bar shows the current page being processed: "Building page 23 of 45..."
- Estimated time remaining: "About 30 seconds left" (based on average per-page processing time)
- A "Cancel Build" button is available — sends `DELETE /api/books/{bookId}/builds/latest` to abort the Celery task
- On completion, the progress bar fills to 100% and transitions to a "Download" button

**Download:**

- When build is complete, a prominent "Download PDF" button appears
- Clicking "Download" calls `GET /api/books/{bookId}/versions/{versionNumber}/download`
- The backend generates a presigned S3 URL with a 1-hour expiry
- The file is served with the filename `{book-title}-v{versionNumber}.pdf` as a download attachment
- A "Copy Link" option copies the presigned URL to clipboard for sharing

**Rebuild & Versioning:**

- Editor can rebuild at any time (after more translations are approved)
- Each rebuild increments `versionNumber`
- Previous builds/versions remain accessible from a "Version History" panel
- The version history panel shows:
  - Version number, build date, status (COMPLETED/FAILED), number of approved sections at time of build
  - Clicking a past version downloads that version's PDF
  - A "Set as Current" option marks a version as the default/canonical version for sharing

**Notification:**

- On build completion, an in-app notification is sent: "Book build complete — version {N} is ready for download"
- If the editor navigates away during build, they see a badge/indicator on the book console: "Build complete" / "Build failed"
- Failed builds show a notification: "Build failed — {error message}" with a "Retry" button

**Edge Cases:**

- Empty sections (no text, no translation): rendered as a blank placeholder within their bounding box
- Sections with only image content (IMAGE_CAPTION type): the cropped section image is embedded directly in the PDF
- Concurrent builds: if a build is already running, the "Build" button is disabled with "Build in progress"
- Large books (500+ pages): build runs in batches to avoid memory issues; progress is reported per batch

**API Endpoints:**

- `POST /api/books/{bookId}/build` — trigger a new build
- `GET /api/books/{bookId}/builds/latest` — poll latest build status and progress
- `DELETE /api/books/{bookId}/builds/latest` — cancel current build
- `GET /api/books/{bookId}/builds` — list all builds (version history)
- `GET /api/books/{bookId}/versions/{versionNumber}/download` — get download URL for a specific version

---

## Cross-Cutting Concerns

### Performance

- Page list with filter/sort must load in under 500ms for books with up to 500 pages
- Build processing targets 1 page per 2 seconds (250-page book in ~8 minutes)
- Polling for build progress should use exponential backoff after initial rapid polling

### Error Handling

- Reorder conflicts: if two editors reorder simultaneously, last-write-wins with a toast: "Page order was modified by another editor — refresh to see latest"
- Build failures due to S3 connectivity: retry automatically up to 3 times with 10-second delay
- Database errors during page delete: full rollback of all child document deletions

### Permissions

- All operations in this Epic require EDITOR or SUPER_ADMIN role (except Download finalized book, which is available to TRANSLATOR as well)
- See `actors.md` for the full permissions matrix

### Data Model Impact

- Page entity gains an `order` field (int) for drag-to-reorder support
- Translation entity gains `rejected`, `rejectedBy`, `rejectionReason` fields
- BookBuild entity gains `versionNumber`, `errorMessage`, `buildDurationMs`, `totalSections`, `approvedSections`, `createdBy` fields
- New `BookVersion` entity added for version history
