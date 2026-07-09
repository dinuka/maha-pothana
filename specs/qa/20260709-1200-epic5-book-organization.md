# Epic 5: Book Organization & Publishing — QA Test Specification

**Date:** 2026-07-09 12:00
**Author:** QA Agent
**Epic Reference:** Epic 5 — Book Organization & Publishing
**Business Analysis:** `specs/business-analysis/20260709-1200-epic5-book-organization.md`
**Architecture:** `specs/architecture/20260709-1200-epic5-book-organization.md`
**UX/Interaction:** `specs/ux/20260709-1200-epic5-book-organization.md`
**Test Plan:** `specs/qa/test-plan.md` (Section 6 and Regression Checklist)

---

## 1. Scope

This QA specification covers all four user stories in Epic 5 (Book Organization & Publishing):

| User Story | ID                 | Description                                                           |
| ---------- | ------------------ | --------------------------------------------------------------------- |
| US-5.1     | Page Organization  | Reorder, add, delete pages; edit section metadata; version history    |
| US-5.2     | Filter & Sort      | Filter pages by translation status; sort by completion metrics        |
| US-5.3     | Translation Review | Review, approve, reject translations; editor override; re-entry logic |
| US-5.4     | Build Book         | Generate finalized PDF; versioning; download; cancel; rebuild         |

---

## 2. Test Cases

### 2.1 Section 6a: Page Organization (US-5.1)

| TC-ID  | Scenario                        | Steps                                                                                                         | Expected Result                                                                                                                                                                                     |
| ------ | ------------------------------- | ------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ORG-01 | Drag reorder page               | 1. Open book console with page list 2. Drag a page by its drag handle to a new position 3. Drop it            | Page order updates immediately in the list. The `order` field on the backend reflects the new position. The `pageNumber` field remains unchanged (reflects original PDF numbering).                 |
| ORG-02 | Reorder persists on reload      | 1. Reorder some pages 2. Refresh the page                                                                     | New page order is preserved. The page list displays pages in the updated order.                                                                                                                     |
| ORG-03 | Add blank page                  | 1. Click "Add Page" button between two pages in the list                                                      | A new Page document is created with `pageNumber=0`, `originalPageNumber="inserted"`, `order` at the insertion point. Subsequent pages' order values shift up by 1.                                  |
| ORG-04 | Delete page                     | 1. Click delete icon on a page 2. Confirm in the dialog                                                       | The Page document and all child Section, Translation, Comment, and AITextExtraction documents are deleted. Remaining pages' order values are compacted (no gaps).                                   |
| ORG-05 | Delete prevents last page       | 1. Create a book with only 1 page 2. Attempt to delete it                                                     | The delete action is disabled. Tooltip reads: "Book must have at least one page".                                                                                                                   |
| ORG-06 | Reorder conflict detection      | 1. Two editors open the same book 2. Both reorder pages simultaneously 3. One of them receives a 409 Conflict | Toast appears: "Page order was modified by another editor — refresh to see latest". Optimistic UI update reverts to previous order.                                                                 |
| ORG-07 | Reorder undo                    | 1. Reorder a page to a new position 2. Press Ctrl+Z                                                           | Page order reverts to the previous state. Undo fires a reversed reorder API call.                                                                                                                   |
| ORG-08 | Add sections to blank page      | 1. Create a blank page 2. Open the canvas editor for the blank page                                           | The blank page loads with no image (placeholder shown). Sections can be added via draw tool or detected via ML detection, just like a regular page.                                                 |
| ORG-09 | Delete page confirmation dialog | 1. Click the delete icon on a page with 5 sections                                                            | A dialog appears with title "Delete Page N?", body showing section count ("5 sections on this page") and warning that this cannot be undone. "Cancel" closes the dialog. "Delete" removes the page. |
| ORG-10 | Page history panel              | 1. Open a page editor that has confirmed sections with saved edits 2. Click "History" panel                   | A timeline shows past section edit saves with timestamps and editor names. Each entry displays the time of save.                                                                                    |
| ORG-11 | Restore section snapshot        | 1. Open page history 2. Click "Restore" on a historical snapshot                                              | Current sections on the canvas are replaced with the sections from the historical snapshot. A success toast confirms the restoration.                                                               |
| ORG-12 | Section edit history tracked    | 1. Edit sections on a page 2. Save changes (Confirm Sections)                                                 | A new `SectionEditHistory` entry is created in the database with a snapshot of all sections, the editor ID, and a timestamp.                                                                        |
| ORG-13 | Big page list (500+ pages)      | 1. Upload a book with 500+ pages 2. Reorder pages near the bottom of the list                                 | Auto-scroll during drag works smoothly. The page list renders and remains responsive (<500ms load time). Performance is acceptable with no jank.                                                    |

### 2.2 Section 6b: Filter & Sort (US-5.2)

| TC-ID  | Scenario                        | Steps                                                          | Expected Result                                                                                                              |
| ------ | ------------------------------- | -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| FLT-01 | Filter by status - All          | 1. Click the "All" filter chip                                 | All pages in the book are displayed, regardless of their translation status.                                                 |
| FLT-02 | Filter by status - Completed    | 1. Click the "Completed" filter chip                           | Only pages where every section has at least one approved translation are shown.                                              |
| FLT-03 | Filter by status - Not Started  | 1. Click the "Not Started" filter chip                         | Only pages with zero submitted translations across all sections are shown.                                                   |
| FLT-04 | Filter by status - In Progress  | 1. Click the "In Progress" filter chip                         | Only pages where at least one section has a submitted translation but not all sections have approved translations are shown. |
| FLT-05 | Filter by status - Needs Review | 1. Click the "Needs Review" filter chip                        | Only pages where all sections have submitted translations pending editor approval are shown.                                 |
| FLT-06 | Sort by page order (asc)        | 1. Select sort option "Page Order Ascending"                   | Pages are ordered by the `order` field ascending. This is the default sort.                                                  |
| FLT-07 | Sort by translation % (desc)    | 1. Select sort option "% Descending"                           | Pages with the highest completion percentage appear first.                                                                   |
| FLT-08 | Filter + sort combination       | 1. Select filter "Completed" 2. Select sort "% Ascending"      | Only completed pages are shown, sorted from least-to-most complete (all will be at 100%, so order is deterministic).         |
| FLT-09 | Filter state in URL             | 1. Set filter to "in_progress" 2. Reload the page              | The URL contains `?filter=in_progress` and the filter is applied on load.                                                    |
| FLT-10 | Progress bar colors             | 1. View pages at 0%, 50%, and 100% completion                  | 0% completion: gray progress bar. 1-99%: blue gradient. 100%: green.                                                         |
| FLT-11 | Summary stats bar               | 1. Open the page list for a book with mixed translation states | Stats bar shows: total pages, total sections, translated section count, pending review count, overall completion percentage. |
| FLT-12 | Empty filter result             | 1. Apply a filter that matches zero pages                      | Empty state displays: "No pages match filter" with a "Clear filter" call-to-action button.                                   |
| FLT-13 | Pre-detection state             | 1. Open a book that has no sections on any page                | Message displayed: "Process pages first to see translation progress" with a link to the first page.                          |
| FLT-14 | Sticky filter bar               | 1. Scroll through a long page list (50+ pages)                 | The filter/sort bar remains visible at the top of the page list as the user scrolls.                                         |

### 2.3 Section 6c: Translation Review (US-5.3)

| TC-ID  | Scenario                            | Steps                                                                         | Expected Result                                                                                                                                                         |
| ------ | ----------------------------------- | ----------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| REV-01 | View all translations for section   | 1. Open the review console for a section that has N submitted translations    | All N submitted translations are displayed side by side. Each card shows translator name, avatar, submission timestamp, and translated text.                            |
| REV-02 | Approve one translation             | 1. Click "Approve" on Translation A                                           | Translation A gets a green "Approved" badge. Border changes to green. `isApproved` field is set to `true` in the database.                                              |
| REV-03 | Approve multiple translations       | 1. Approve Translation A 2. Approve Translation B                             | Both Translation A and B show green "Approved" badges. The section is considered "translated".                                                                          |
| REV-04 | Reject a translation                | 1. Click "Reject" on Translation A                                            | Translation A card dims to 0.6 opacity. Text shows strikethrough. Red "Rejected" badge appears.                                                                         |
| REV-05 | Reject with reason                  | 1. Click "Reject" 2. Type a rejection reason 3. Submit                        | `Translation.rejectionReason` is saved with the provided text. The "Rejected" badge is shown. The rejection reason can be expanded.                                     |
| REV-06 | Reject all translations -> re-entry | 1. Reject all N submitted translations for a section                          | Section status transitions to "pending". The section re-enters the translation pool and appears in the "Next" queue for translators.                                    |
| REV-07 | Re-entry notification               | 1. When all translations for a section are rejected                           | An in-app notification is sent to translators: "Section on page N needs re-translation — all previous translations were rejected".                                      |
| REV-08 | Editor override translation         | 1. Type own translated text 2. Click "Submit as Editor's Choice"              | The editor's version is saved as a Translation document. `isApproved` is set to `true`. The card is labeled "Editor's Choice" with a purple border.                     |
| REV-09 | Copy from submitted translation     | 1. Click "Copy from Kamal" on the editor override textarea                    | The editor's textarea is filled with Kamal's translation text. The source card briefly flashes blue.                                                                    |
| REV-10 | Blocked translator review           | 1. View a section where a blocked user has submitted a translation            | The blocked user's translation is visible in the review UI. It is labeled "Blocked User". The editor can still approve or reject it.                                    |
| REV-11 | Audit trail created                 | 1. Approve some translations and reject others                                | A `TranslationHistoryItem` is created for each approve/reject action with action type APPROVED or REJECTED, editor ID, and timestamp.                                   |
| REV-12 | Review navigation                   | 1. Open the review console with multiple sections 2. Use prev/next navigation | Keyboard shortcuts (left/right arrows) navigate between sections. A counter shows "Section 3 of 12". Wrapping: last section on page goes to first section of next page. |

### 2.4 Section 6d: Build Book (US-5.4)

| TC-ID  | Scenario                                | Steps                                                                           | Expected Result                                                                                                                                                              |
| ------ | --------------------------------------- | ------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| BLD-01 | Build button enabled                    | 1. Open a book that has sections and at least one approved translation          | The "Build Book" button is active and clickable.                                                                                                                             |
| BLD-02 | Build button disabled - no sections     | 1. Open a book with no sections on any page                                     | The "Build Book" button is disabled. Tooltip: "No sections detected".                                                                                                        |
| BLD-03 | Build button disabled - no approvals    | 1. Open a book with sections but zero approved translations                     | The "Build Book" button is disabled. Tooltip: "No approved translations — review and approve first".                                                                         |
| BLD-04 | Build summary panel                     | 1. Open the build panel for a book with mixed states                            | Summary shows: total sections count, approved sections count with percentage, pending/untranslated section counts. Warning displayed if sections lack approved translations. |
| BLD-05 | Confirmation dialog before build        | 1. Click "Build Book" button                                                    | Confirmation dialog appears: title "Build Finalized Book", body shows counts of sections with/without approved translations, "Cancel" and "Build" buttons.                   |
| BLD-06 | Build progress polling                  | 1. Start a build 2. Observe network traffic                                     | Frontend polls `GET /api/books/{bookId}/builds/latest` every 3 seconds while status is BUILDING.                                                                             |
| BLD-07 | Progress bar during build               | 1. Watch the build panel during processing                                      | Progress bar animates smoothly. Label shows "Building page 23 of 45...". Estimated time remaining is displayed.                                                              |
| BLD-08 | Cancel build                            | 1. Click "Cancel Build" during processing 2. Confirm in dialog                  | The Celery task is revoked via `Celery.control.revoke()`. `BookBuild.status` is set to CANCELLED. The build panel returns to idle state.                                     |
| BLD-09 | Build completes                         | 1. Wait for build processing to finish                                          | `BookBuild.status` changes to COMPLETED. Progress bar fills to 100% with a green flash. Download button appears.                                                             |
| BLD-10 | Download PDF                            | 1. Click "Download PDF" after build completes                                   | Browser downloads the PDF file. Filename follows pattern `{book-title}-v{versionNumber}.pdf`.                                                                                |
| BLD-11 | Copy download link                      | 1. Click "Copy Link"                                                            | The presigned S3 URL is copied to clipboard. A toast confirms: "Link copied!".                                                                                               |
| BLD-12 | Rebuild creates new version             | 1. Build a book 2. Make changes 3. Rebuild                                      | Version number increments (v1, v2, v3...). Previous builds remain accessible in version history.                                                                             |
| BLD-13 | Version history panel                   | 1. After 3 builds, open version history                                         | Panel shows version 3, 2, and 1 with status badges (COMPLETED/FAILED), dates, build times, and download buttons.                                                             |
| BLD-14 | Download older version                  | 1. Click "Download" on version 1 in the version history                         | A presigned URL is generated for version 1's PDF. The PDF is downloaded.                                                                                                     |
| BLD-15 | Build failure                           | 1. Mock a build failure (e.g., S3 timeout)                                      | Build status shows "Build failed" with error message. A "Retry Build" button is available.                                                                                   |
| BLD-16 | Build failure notification              | 1. Start a build 2. Navigate away from the book console 3. Build fails          | When the user returns to the book console, a badge/indicator shows "Build failed" with a retry option.                                                                       |
| BLD-17 | Build in-progress prevents second build | 1. Start a build 2. While it is building, try to click "Build" again            | The "Build" button shows "Build in progress" and is disabled. A tooltip explains that a build is already running.                                                            |
| BLD-18 | Concurrent builds                       | 1. Attempt to POST `/api/books/{bookId}/build` while a build is already running | Backend returns 409 Conflict with message "Build already in progress".                                                                                                       |

### 2.5 Section 6e: Error Handling — Epic 5 Edge Cases

| TC-ID     | Scenario                           | Steps                                                                           | Expected Result                                                                                                              |
| --------- | ---------------------------------- | ------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| E5-ERR-01 | Reorder network error              | 1. Reorder pages 2. API request fails (timeout or 500)                          | Toast: "Failed to update page order. [Retry]". UI reverts to the pre-drag page order.                                        |
| E5-ERR-02 | Reorder validation error           | 1. Send a reorder request with a pageId that does not belong to the book        | Toast: "Some pages could not be reordered. [Refresh]".                                                                       |
| E5-ERR-03 | Delete last page blocked           | 1. Try to delete the only remaining page                                        | Delete button is disabled. Tooltip: "A book must have at least one page".                                                    |
| E5-ERR-04 | Delete network error               | 1. Delete a page 2. DELETE API fails                                            | Toast: "Failed to delete page. [Retry]". The page item re-appears in the list with animation.                                |
| E5-ERR-05 | Add page network error             | 1. Click "Add Page" 2. POST API fails                                           | The optimistically inserted page item is removed from the list. Toast: "Failed to add page. [Retry]".                        |
| E5-ERR-06 | Approve conflict (409)             | 1. Translation was already approved/rejected by another editor 2. Click Approve | Toast: "This translation was already approved/rejected by another editor". Translations list auto-refreshes.                 |
| E5-ERR-07 | Reject network error               | 1. Click Reject with reason 2. API request fails                                | Toast: "Failed to reject translation. [Retry]". Card remains in Pending state with rejection reason preserved in textarea.   |
| E5-ERR-08 | Editor override API failure        | 1. Submit editor's translation 2. POST API fails                                | Toast: "Failed to submit editor's translation. [Retry]". Editor's text remains in textarea for retry.                        |
| E5-ERR-09 | Section image load error in review | 1. Open review console with expired presigned URL                               | Image shows broken placeholder. Text: "Reference image unavailable". A [Retry] button reloads the presigned URL.             |
| E5-ERR-10 | Build failure (S3)                 | 1. S3 upload times out after 3 retries                                          | Red error card: "Build failed". Error message: "S3 upload failed after 3 retries: connection timeout". [Retry Build] button. |
| E5-ERR-11 | Build failure (PDF gen)            | 1. PDF generation crashes on page N                                             | Red error card: "Build failed". Error message: "PDF generation failed at page N: {error}". [Retry Build] button.             |
| E5-ERR-12 | Build failure (DB read)            | 1. Cannot read page/section data during build                                   | Red error card: "Build failed". Error message: "Failed to read page N: {error}". [Retry Build] button.                       |
| E5-ERR-13 | Build cancel fails                 | 1. Click Cancel Build 2. DELETE endpoint fails after timeout                    | Toast: "Failed to cancel — build may complete shortly". Frontend continues polling for build result.                         |
| E5-ERR-14 | Concurrent build blocked           | 1. A build is already in progress 2. Click Build                                | Button is disabled. Tooltip: "A build is already in progress". Backend returns 409 if forced.                                |
| E5-ERR-15 | Download URL expired               | 1. Click download after presigned URL has expired (1h+)                         | Toast: "Download link expired — generating new link...". New presigned URL is generated and download auto-starts.            |
| E5-ERR-16 | Version download not found         | 1. Click Download on a version with missing PDF file                            | Toast: "Version not found or has no associated PDF file". [Refresh] button to retry.                                         |

---

## 3. Test Data Requirements

### 3.1 Books

| Data                                 | Purpose                                     | Setup                                              |
| ------------------------------------ | ------------------------------------------- | -------------------------------------------------- |
| Book with 10 pages, 80 sections      | Core test fixture: page org, filters, build | Upload medium PDF, run detection, confirm sections |
| Book with 1 page, 8 sections         | Edge case: delete last page                 | Upload single-page PDF, run detection              |
| Book with >500 pages, 4000+ sections | Performance: big page list, filter/sort     | Upload large PDF or generate via API               |
| Book with 0 sections on any page     | Pre-detection empty state                   | Upload PDF, skip section detection                 |
| Book with blank (inserted) pages     | Blank page interaction                      | Add blank pages via API or UI                      |

### 3.2 Translations

| Data                                          | Purpose                 | Setup                                        |
| --------------------------------------------- | ----------------------- | -------------------------------------------- |
| Mix of approved/rejected/pending translations | Filter, stats, review   | Create translations and approve/reject some  |
| 2+ translators with submissions               | Multi-translator review | Create user accounts and submit translations |
| Section with all N translations rejected      | Re-entry logic test     | Reject all translations for a section        |
| Blocked user's translation                    | Blocked user label test | Block translator, verify translation visible |
| Section with editor's choice override         | Editor override test    | Submit editor override translation           |

### 3.3 Builds

| Data                      | Purpose                     | Setup                                            |
| ------------------------- | --------------------------- | ------------------------------------------------ |
| Book with multiple builds | Version history             | Trigger 3 builds with different approved sets    |
| Failed build record       | Failed state display        | Mock build failure or create failed build record |
| Build in progress         | Concurrent build prevention | Mock long-running build                          |

### 3.4 Test User Accounts

| User                        | Role        | Purpose                                    |
| --------------------------- | ----------- | ------------------------------------------ |
| editor-1@test.com           | EDITOR      | Page org, filter/sort, review, build       |
| editor-2@test.com           | EDITOR      | Concurrent reorder/review conflict testing |
| translator-a@test.com       | TRANSLATOR  | Translation submissions for review         |
| translator-b@test.com       | TRANSLATOR  | Multi-translator scenario                  |
| translator-blocked@test.com | TRANSLATOR  | Blocked user test                          |
| admin@test.com              | SUPER_ADMIN | Full access verification                   |

---

## 4. Test Environment Setup

### 4.1 Infrastructure Prerequisites

All services must be running:

```bash
docker compose -f infra/docker-compose.dev.yml up -d
```

| Service        | Purpose                        | Port       |
| -------------- | ------------------------------ | ---------- |
| MongoDB        | Data storage                   | 27017      |
| Redis          | Celery broker, caching         | 6379       |
| MinIO          | S3 file storage (PDFs, images) | 9000, 9001 |
| LibreTranslate | Auto-translation               | 5000       |

### 4.2 Application Servers

```bash
# Terminal 1: Frontend
pnpm dev

# Terminal 2: Backend
cd apps/api && uvicorn app.main:app --reload --port 8000

# Terminal 3: Celery worker
cd apps/api && celery -A app.tasks.celery_app worker --loglevel=info
```

### 4.3 Mocked Services for Testing

#### Mock S3 (MinIO)

- MinIO runs locally as part of Docker Compose
- For download testing: verify presigned URL generation and expiry
- To test URL expiry: manually set `DOWNLOAD_URL_EXPIRY_SECONDS=60` in `.env` and wait 60 seconds

#### Mock Celery for Build Testing

- To test build failure modes: inject mock error into `build_book.py` task
- To test build progress: use a sleep-based mock that reports incremental progress
- To test build cancellation: add a long sleep (30s+) to the build task

#### Mock Concurrent Edits

- Open two browser sessions (incognito + normal) logged in as editor-1 and editor-2
- Perform simultaneous operations to trigger 409 conflict scenarios

### 4.4 API Endpoints for Direct Testing

```bash
# Reorder pages
curl -X PUT "http://localhost:8000/api/books/{bookId}/pages/reorder" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"orders": [{"pageId": "page1", "order": 2}, {"pageId": "page2", "order": 1}]}'

# Add blank page
curl -X POST "http://localhost:8000/api/books/{bookId}/pages" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"insertAfterOrder": 5}'

# Delete page
curl -X DELETE "http://localhost:8000/api/pages/{pageId}" \
  -H "Authorization: Bearer {token}"

# List pages with filters
curl "http://localhost:8000/api/books/{bookId}/pages?filter=in_progress&sort=translation_percent&order=desc&page=1&limit=20" \
  -H "Authorization: Bearer {token}"

# Approve translation
curl -X PUT "http://localhost:8000/api/translations/{translationId}/approve" \
  -H "Authorization: Bearer {token}"

# Reject translation
curl -X PUT "http://localhost:8000/api/translations/{translationId}/reject" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Does not match source text"}'

# Editor override translation
curl -X POST "http://localhost:8000/api/sections/{sectionId}/translations" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"translatedText": "Editor translation", "sourceTranslationId": "trans123"}'

# Trigger build
curl -X POST "http://localhost:8000/api/books/{bookId}/build" \
  -H "Authorization: Bearer {token}"

# Poll build status
curl "http://localhost:8000/api/books/{bookId}/builds/latest" \
  -H "Authorization: Bearer {token}"

# Cancel build
curl -X DELETE "http://localhost:8000/api/books/{bookId}/builds/latest" \
  -H "Authorization: Bearer {token}"

# List builds
curl "http://localhost:8000/api/books/{bookId}/builds" \
  -H "Authorization: Bearer {token}"

# List versions
curl "http://localhost:8000/api/books/{bookId}/versions" \
  -H "Authorization: Bearer {token}"

# Download version
curl "http://localhost:8000/api/books/{bookId}/versions/{v}/download" \
  -H "Authorization: Bearer {token}"

# Page history
curl "http://localhost:8000/api/pages/{pageId}/history" \
  -H "Authorization: Bearer {token}"
```

---

## 5. Regression Test Checklist

### 5.1 Page Organization (US-5.1)

- [ ] Pages can be reordered via drag-and-drop with visual drop indicator
- [ ] Reordered page order persists on page reload
- [ ] Blank pages can be added between pages with correct pageNumber=0 and originalPageNumber="inserted"
- [ ] Pages can be deleted with cascade of child documents (sections, translations, comments, AI text extractions)
- [ ] Delete prevents removal of the last remaining page (tooltip)
- [ ] Reorder conflict detection shows toast warning on simultaneous edit (409)
- [ ] Ctrl+Z undoes page reorder actions
- [ ] Blank pages accept sections in canvas editor (draw tool and ML detection)
- [ ] Page history panel shows timeline of section snapshots with timestamps and editor names
- [ ] Section snapshots can be restored from history
- [ ] SectionEditHistory entries created on each section save
- [ ] Page list loads quickly for 500+ page books (<500ms)

### 5.2 Filter & Sort (US-5.2)

- [ ] Filter by status works correctly (All, Not Started, In Progress, Completed, Needs Review)
- [ ] Filter state persists in URL and survives reload
- [ ] Sort by page order ascending/descending works
- [ ] Sort by translation percentage ascending/descending works
- [ ] Filter + sort combination works correctly
- [ ] Progress bar colors: gray (0%), blue gradient (1-99%), green (100%)
- [ ] Animated transitions when progress changes
- [ ] Summary stats bar shows accurate aggregate counts
- [ ] Empty filter result shows "No pages match filter" with clear CTA
- [ ] Pre-detection state shows "Process pages first" message
- [ ] Filter/sort bar is sticky during scroll

### 5.3 Translation Review (US-5.3)

- [ ] Review console shows all submitted translations side-by-side
- [ ] Approve marks translation with green badge and isApproved=true
- [ ] Multiple translations can be approved
- [ ] Reject dims card with strikethrough and red badge
- [ ] Reject with reason saves rejectionReason to Translation
- [ ] Rejecting all translations causes section to re-enter translation pool
- [ ] Re-entry notification sent to translators
- [ ] Editor override creates auto-approved "Editor's Choice" translation
- [ ] Copy from submitted translation fills editor textarea
- [ ] Blocked user translations still visible with "Blocked User" label
- [ ] Audit trail (TranslationHistoryItem) created for each approve/reject action
- [ ] Review navigation shows section counter and supports keyboard prev/next

### 5.4 Build Book (US-5.4)

- [ ] Build button enabled only with sections + approved translations
- [ ] Disabled states show correct tooltip explanations
- [ ] Build summary panel shows accurate counts with warnings
- [ ] Build confirmation dialog shows skipped sections count
- [ ] Frontend polls build progress every 3 seconds
- [ ] Progress bar animates and shows "Building page X of Y..."
- [ ] Estimated time remaining updates with each poll
- [ ] Cancel build terminates Celery task and sets CANCELLED status
- [ ] Download PDF button appears on build completion
- [ ] Download PDF filename matches "{title}-v{version}.pdf"
- [ ] Copy Link copies presigned URL to clipboard with toast confirmation
- [ ] Rebuild increments version number (v1, v2, v3...)
- [ ] Version history panel shows all builds with status badges and download buttons
- [ ] Older versions remain downloadable
- [ ] Build failure shows error message with Retry button
- [ ] Build failure notification/indicator persists when editor navigates away
- [ ] In-progress build prevents triggering a second build
- [ ] Concurrent build request returns 409 Conflict

### 5.5 Error Handling (Cross-Cutting)

- [ ] Reorder network errors show appropriate toast with retry
- [ ] Reorder validation errors handled gracefully
- [ ] Delete confirmation dialog shown with correct page number and section count
- [ ] Delete network error reverts optimistic UI
- [ ] Add page network error removes optimistic item
- [ ] Approve/reject conflict (409) shows appropriate toast
- [ ] Reject network error preserves reason in textarea
- [ ] Editor override API failure preserves text for retry
- [ ] Build S3 failures handled with retry option
- [ ] Build PDF generation failures show page number in error
- [ ] Build cancellation timeout handled gracefully
- [ ] Download URL expiry generates new link automatically

---

## 6. Automation Priorities

### Priority 1: Critical Path (Automate First)

These test cases cover the most critical user workflows and should be automated first:

| Priority | TC-ID            | Reason for Priority                                         |
| -------- | ---------------- | ----------------------------------------------------------- |
| P1       | ORG-01           | Core drag-and-drop reorder — primary interaction for US-5.1 |
| P1       | ORG-04           | Page deletion cascade — highest data integrity risk         |
| P1       | ORG-05           | Last-page guard — critical business rule                    |
| P1       | FLT-01 to FLT-05 | Filter correctness — affects all users browsing pages       |
| P1       | FLT-06 to FLT-07 | Sort correctness — affects page list usability              |
| P1       | REV-02           | Approve flow — core review action, high frequency           |
| P1       | REV-04           | Reject flow — core review action, high frequency            |
| P1       | REV-06           | Re-entry logic — critical state machine transition          |
| P1       | BLD-01           | Build button pre-condition check — primary gate             |
| P1       | BLD-06           | Polling mechanism — core async interaction pattern          |
| P1       | BLD-09           | Build completion — primary deliverable                      |
| P1       | BLD-10           | Download PDF — end-to-end value delivery                    |

### Priority 2: High Impact (Automate Second)

| Priority | TC-ID            | Reason for Priority               |
| -------- | ---------------- | --------------------------------- |
| P2       | ORG-02           | Persistence verification          |
| P2       | ORG-03           | Blank page creation flow          |
| P2       | ORG-06           | Concurrent edit conflict handling |
| P2       | ORG-09           | Delete confirmation dialog        |
| P2       | FLT-08           | Filter + sort combination         |
| P2       | FLT-09           | URL state persistence             |
| P2       | FLT-10           | Progress bar color mapping        |
| P2       | REV-03           | Multi-approve scenario            |
| P2       | REV-05           | Reject with reason                |
| P2       | REV-08           | Editor override                   |
| P2       | REV-11           | Audit trail verification          |
| P2       | BLD-02 to BLD-03 | Disabled state tooltips           |
| P2       | BLD-08           | Cancel build                      |
| P2       | BLD-12           | Rebuild versioning                |
| P2       | BLD-18           | Concurrent build prevention       |

### Priority 3: Edge Cases & Error Flows

| Priority | TC-ID                  | Reason for Priority                 |
| -------- | ---------------------- | ----------------------------------- |
| P3       | ORG-07                 | Reorder undo                        |
| P3       | ORG-10 to ORG-12       | History panel and snapshot restore  |
| P3       | ORG-13                 | Big page list performance           |
| P3       | FLT-12 to FLT-14       | Empty states and sticky bar         |
| P3       | REV-07                 | Re-entry notification               |
| P3       | REV-09 to REV-10       | Copy from translation, blocked user |
| P3       | REV-12                 | Review navigation                   |
| P3       | BLD-04                 | Summary panel                       |
| P3       | BLD-05                 | Confirmation dialog                 |
| P3       | BLD-07                 | Progress bar animation              |
| P3       | BLD-11                 | Copy link                           |
| P3       | BLD-13 to BLD-14       | Version history operations          |
| P3       | BLD-15 to BLD-17       | Build failure states                |
| P3       | E5-ERR-01 to E5-ERR-16 | All error handling edge cases       |

### Recommended Automation Approach

| Layer                  | Tool                               | Tests to Cover                                                                                                                                                                      |
| ---------------------- | ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Backend API            | pytest + httpx (async)             | All API contracts: reorder validation, delete cascade, approve/reject state machine, build trigger/pre-conditions                                                                   |
| Frontend (unit)        | Vitest + @testing-library/react    | Component states: PageListItem drag states, TranslationCard (pending/approved/rejected/editor-choice), BuildProgress (idle/building/completed/failed), progress bar color rendering |
| Frontend (integration) | Vitest + MSW (mock service worker) | Page reorder optimistic update + revert, filter/sort URL sync, build polling cycle, review approve/reject UX transitions                                                            |
| E2E (optional)         | Playwright                         | Critical end-to-end flows: reorder + reload persistence, build + download complete flow, review + approve cycle                                                                     |

---

## 7. Test Case to User Story Mapping

| User Story                                     | Test Cases                                         |
| ---------------------------------------------- | -------------------------------------------------- |
| **US-5.1: Organize Pages & Sections**          | ORG-01 through ORG-13, E5-ERR-01 through E5-ERR-05 |
| Sub-feature: Drag-to-reorder                   | ORG-01, ORG-02, ORG-06, ORG-07, ORG-13             |
| Sub-feature: Add blank page                    | ORG-03, ORG-08, E5-ERR-05                          |
| Sub-feature: Delete page                       | ORG-04, ORG-05, ORG-09, E5-ERR-03, E5-ERR-04       |
| Sub-feature: Version history                   | ORG-10, ORG-11, ORG-12                             |
| **US-5.2: Filter & Sort Translation Progress** | FLT-01 through FLT-14                              |
| Sub-feature: Filter by status                  | FLT-01, FLT-02, FLT-03, FLT-04, FLT-05             |
| Sub-feature: Sort options                      | FLT-06, FLT-07, FLT-08                             |
| Sub-feature: Visual progress                   | FLT-10, FLT-11                                     |
| Sub-feature: Edge cases                        | FLT-09, FLT-12, FLT-13, FLT-14                     |
| **US-5.3: Review Translations**                | REV-01 through REV-12, E5-ERR-06 through E5-ERR-09 |
| Sub-feature: View translations                 | REV-01                                             |
| Sub-feature: Approve                           | REV-02, REV-03, E5-ERR-06                          |
| Sub-feature: Reject                            | REV-04, REV-05, E5-ERR-07                          |
| Sub-feature: Re-entry logic                    | REV-06, REV-07                                     |
| Sub-feature: Editor override                   | REV-08, REV-09, E5-ERR-08                          |
| Sub-feature: Blocked user                      | REV-10                                             |
| Sub-feature: Audit & navigation                | REV-11, REV-12, E5-ERR-09                          |
| **US-5.4: Build Finalized Book**               | BLD-01 through BLD-18, E5-ERR-10 through E5-ERR-16 |
| Sub-feature: Build pre-conditions              | BLD-01, BLD-02, BLD-03, BLD-04, BLD-05             |
| Sub-feature: Build execution                   | BLD-06, BLD-07, BLD-08, E5-ERR-13, E5-ERR-14       |
| Sub-feature: Build completion                  | BLD-09, BLD-10, BLD-11, E5-ERR-15, E5-ERR-16       |
| Sub-feature: Versioning                        | BLD-12, BLD-13, BLD-14                             |
| Sub-feature: Build failure                     | BLD-15, BLD-16, E5-ERR-10, E5-ERR-11, E5-ERR-12    |
| Sub-feature: Concurrent build                  | BLD-17, BLD-18                                     |

---

## 8. High-Risk Areas

| Risk Area                               | Description                                                                                                                          | Mitigation                                                                                               |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------- |
| **Page deletion cascade**               | Deleting a page cascades to sections, translations, comments, and AI text extractions. A partial failure could orphan documents.     | Test with MongoDB transaction rollback simulation. Verify atomicity.                                     |
| **Concurrent reorder conflict**         | Two editors reordering simultaneously can cause order value corruption.                                                              | Test with simultaneous API calls. Verify 409 response and data integrity after conflict.                 |
| **All-rejected re-entry loop**          | If all translations are rejected, the section re-enters the pool. A cycle of rejection without approval could frustrate translators. | Verify re-entry notification. Test repeated rejection cycles. Ensure translators are notified each time. |
| **Build cancellation artifact cleanup** | Cancelling a build mid-processing could leave partial PDFs in S3.                                                                    | Test cancel flow and verify no partial artifacts remain.                                                 |
| **Build progress polling race**         | Frontend polls every 3s. If backend cache is stale, the UI could show incorrect progress.                                            | Test polling with slow/fast builds. Verify progress is monotonic (never goes backwards).                 |
| **Download URL expiry**                 | Presigned URLs expire after 1 hour. Users clicking old links see errors.                                                             | Test auto-generation of new URLs on expiry. Verify toast message.                                        |
| **Big book performance (500+ pages)**   | Filter/sort queries and build processing could be slow.                                                                              | Test with 500+ page fixture. Verify <500ms page list load and stable build processing.                   |

---

## 9. Defect Severity Guidelines

| Severity          | Definition                                               | Example                                                                                             |
| ----------------- | -------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| **S1 — Critical** | Core functionality broken, data loss risk, no workaround | Page reorder corrupts order values; build produces wrong PDF; delete cascade orphans data           |
| **S2 — High**     | Major feature impaired, workaround exists                | Filter returns wrong results; approve fails silently; rejection reason not saved                    |
| **S3 — Medium**   | Non-critical feature broken, cosmetic issue              | Progress bar animation missing; toast duration too short; confirmation dialog missing section count |
| **S4 — Low**      | Minor visual or UX polish                                | Page list scroll position resets on filter change (not sticky); drag handle alignment off by 2px    |

---

## 10. Document References

| Document                     | Path                                                               |
| ---------------------------- | ------------------------------------------------------------------ |
| Business Analysis — Epic 5   | `specs/business-analysis/20260709-1200-epic5-book-organization.md` |
| Architecture — Epic 5        | `specs/architecture/20260709-1200-epic5-book-organization.md`      |
| UX/Interaction — Epic 5      | `specs/ux/20260709-1200-epic5-book-organization.md`                |
| Test Plan (Section 6)        | `specs/qa/test-plan.md`                                            |
| Page Editor Fix QA           | `specs/qa/20260702-2115-page-editor-fix.md`                        |
| Translation Page Redesign QA | `specs/qa/20260706-1200-translation-page-redesign.md`              |
