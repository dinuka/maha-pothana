# Maha Pothana — User Stories

## Epic 1: Authentication & Onboarding

### US-1.1 Google SSO Login

**As a** visitor
**I want to** sign in with my Google account
**So that** I can access the platform without creating a new password.

**Acceptance Criteria:**

- User clicks "Sign in with Google" button
- Google OAuth flow completes
- On first login, user is auto-assigned both Editor and Translator roles
- On subsequent logins, user lands on dashboard with existing roles
- Invalid/revoked Google tokens show an error message

### US-1.2 Role Management (Super Admin)

**As a** super admin
**I want to** modify user roles and permissions
**So that** I can control access within the system.

**Acceptance Criteria:**

- Super Admin sees a user management page
- Can view all users with their current roles
- Can add/remove Editor or Translator role for any user
- Changes take effect immediately (no re-login required for role-based UI)

## Epic 2: Book Management

### US-2.1 Upload a Book (Editor)

**As an** editor
**I want to** upload a book PDF with title and metadata
**So that** it can be added to the translation system.

**Acceptance Criteria:**

- Editor provides: book title, author, source language, target language(s), description (metadata)
- File picker accepts PDF files only
- System checks for duplicate uploads (same filename + file hash)
- On duplicate, show error: "This book has already been uploaded"
- Valid upload shows progress indicator
- After upload, auto-redirect to book translate console
- Book appears in "My Books" list with thumbnail

### US-2.2 View Uploaded Books

**As an** editor
**I want to** see all my uploaded books with thumbnails
**So that** I can navigate to any book's console.

**Acceptance Criteria:**

- Grid/list view of all books uploaded by the editor
- Each item shows: thumbnail, title, author, progress (translation %)
- Clicking a book navigates to its translate console
- Search and filter by title/author
- Sort by upload date, title, translation progress

## Epic 3: Page Processing

### US-3.1 Automatic Page Separation

**As a** system
**I want to** automatically split uploaded books into individual pages
**So that** editors can process them one by one.

**Acceptance Criteria:**

- After upload, system extracts each page as a separate image
- Pages numbered sequentially starting from 1
- Each page stored in S3 under `books/{bookId}/pages/{pageNumber}.png`
- Processing happens asynchronously (Celery worker)
- Editor sees processing status per page

### US-3.2 View Page Image on Canvas

**As an** editor
**I want to** see the actual page image rendered on the Konva canvas
**So that** I can visually identify sections overlaid on the real page content.

**Acceptance Criteria:**

- The page image loads from a presigned S3 URL (not a raw S3 key)
- The image is rendered as the canvas background using `fillPatternImage` or `Konva.Image`
- Image dimensions determine the initial canvas size (capped to container width, maintaining aspect ratio)
- A loading spinner is shown while the image is being fetched
- If the image fails to load, an error state with a retry button is displayed
- When no page image URL is provided, the fallback "No page image available" message is shown

### US-3.3 Section Detection & Display

**As an** editor
**I want to** trigger automatic section detection on a page and view results
**So that** I can see ML-detected sections as colored rectangles overlaid on the page image.

**Acceptance Criteria:**

- A "Detect Sections" button triggers the detection API (`POST /api/pages/{pageId}/sections/detect`)
- A processing indicator is shown while detection runs
- On completion, detected sections appear as colored rectangles overlaid on the page image
- Each section type is color-coded: HEADER (blue), PARAGRAPH (green), FOOTNOTE (orange), IMAGE_CAPTION (purple), PAGE_NUMBER (gray), OTHER (violet)
- Each rectangle is labeled with its section type text in the top-left corner
- Clicking a rectangle selects it and shows a Transformer with resize handles
- Detected sections are non-destructive — all modifications happen locally until confirmed

### US-3.4 Edit Sections (Canvas Manipulation)

**As an** editor
**I want to** modify detected sections by dragging, resizing, deleting, or adding new ones
**So that** the section layout accurately reflects the page structure before translation.

**Acceptance Criteria:**

- Click and drag to move a selected section rectangle freely within the canvas
- Drag corner/edge transform handles to resize a section
- Minimum section size constraint: width >= 10px, height >= 10px
- A "Delete" button (enabled only when a section is selected) removes the section from the local state
- An "Add Section" toggle button enters draw mode; click-drag on canvas draws a new rectangle (min 10x10px)
- A type selector dropdown allows changing the section type of the currently selected section
- Changes are accumulated locally until "Confirm Sections" is pressed
- Zoom controls (+/- buttons and percentage display) scale the canvas view without affecting stored coordinates
- Undo/Redo support for section modifications during the editing session

### US-3.5 Confirm & Save Sections

**As an** editor
**I want to** confirm and save the finalized sections to the database
**So that** they become available for cropping and translation.

**Acceptance Criteria:**

- "Confirm Sections" button saves all section positions, sizes, types, and order to the API
- The API payload format matches the backend expectation (raw array of section objects, not wrapped)
- On success, page status transitions to SECTIONS_CONFIRMED on the backend
- A success toast/notification is displayed
- On failure, an error message is shown with the option to retry
- After confirmation, sections appear in the translation pool
- Confirmed sections can still be re-edited by re-opening the page
- After confirmation, a "Re-detect Sections" option is available if the editor wants to re-run detection

### US-3.6 Section Detection Error Handling

**As an** editor
**I want to** be notified if section detection fails
**So that** I can retry or troubleshoot the issue.

**Acceptance Criteria:**

- Detection failures are communicated with a clear error message
- Page status transitions to DETECTION_FAILED on backend failure
- A "Retry Detection" button is available on failed pages
- Network timeouts and server errors are handled gracefully

## Epic 4: Translation

### US-4.1 View Random Section for Translation

**As a** translator
**I want to** see a random untranslated section
**So that** I can contribute translations efficiently.

**Acceptance Criteria:**

- A "Next" button fetches a random untranslated section
- Section displays: the cropped section image, auto-detected text content
- Auto-translated text shown as a starting point
- Translator can edit the auto-translated text
- Save button submits the translation

### US-4.2 View Page Context

**As a** translator
**I want to** see the full page and adjacent pages
**So that** I can understand context for better translation.

**Acceptance Criteria:**

- Toggle to view the entire page with the section highlighted
- "Previous page" and "Next page" thumbnails/links
- Clicking adjacent pages navigates to them
- Current section remains visually highlighted

### US-4.3 Zoom Text

**As a** translator
**I want to** zoom in/out on section text
**So that** I can read small or unclear text.

**Acceptance Criteria:**

- +/- buttons to zoom the image
- Zoom level displayed as percentage
- Reset zoom to 100% button
- Zoom does not affect saved section coordinates

### US-4.4 Add Translator Comment

**As a** translator
**I want to** add a comment to a section
**So that** I can ask questions or note ambiguities.

**Acceptance Criteria:**

- Comment text area below the section
- Comment saved with translator name and timestamp
- Comments visible to editors and other translators
- Threaded replies possible

### US-4.5 Configurable Translator Count

**As an** editor
**I want to** set the number of translators required per book
**So that** each section gets translated by N different translators.

**Acceptance Criteria:**

- Editor sets N (e.g., 2) per book in settings
- A section is complete only when N translations are submitted
- A translator can see their **own** pending translation before the editor approves or rejects it
- A translator cannot see other translators' pending translations before approval
- After the editor approves at least one translation, all translators can see the approved translation and discuss via comments
- Editor can view all N translations side by side

## Epic 5: Book Organization & Publishing

> **Detailed analysis available in:** `specs/business-analysis/20260709-1200-epic5-book-organization.md`

---

### US-5.1 Organize Pages & Sections

**As an** editor
**I want to** reorder, add, and delete pages; and continue editing section metadata
**So that** the final book structure is correct before building.

**Acceptance Criteria:**

**Page Reordering (Drag & Drop):**

- Book console displays a page list sorted by the `order` field (defaults to `pageNumber`)
- Each page item shows: thumbnail, page number, section count, and translation progress
- Editor can drag pages vertically to reorder; a visual drop indicator shows the target position
- On drop, frontend sends `PUT /api/books/{bookId}/pages/reorder` with the new order array
- The `pageNumber` field remains unchanged (reflects original PDF numbering)
- Undo/redo for reorder actions within the current session

**Add Page:**

- "Add Page" button available at bottom of list and between any two pages
- New blank page created with `pageNumber=0`, `originalPageNumber="inserted"`, no source image
- Subsequent pages' `order` values shift to accommodate the insertion

**Delete Page:**

- Delete action per page with confirmation dialog showing page number and section count
- Backend cascades delete: Page document + all Section, Translation, Comment, AITextExtraction docs
- Remaining pages' `order` values compacted (no gaps)
- Minimum one page constraint — delete disabled if only one page remains

**Edit Section Content, Position, Type:**

- Editors can re-open any page's canvas editor from the page list
- Existing Epic 3 section editing (drag, resize, type change) available even after confirmation
- Changes tracked via `SectionEditHistory`

**Version History:**

- A "History" panel on the page editor shows a timeline of section snapshots with timestamps and editor names
- Editors can view past snapshots (read-only) or restore a previous version

---

### US-5.2 Filter & Sort Translation Progress

**As an** editor
**I want to** filter pages by translation status and sort by completion metrics
**So that** I can quickly identify incomplete work and track overall progress.

**Acceptance Criteria:**

**Filter by Translation Status:**

- Filter bar with options: All, Not Started, In Progress, Completed, Needs Review
- Each filter is color-coded (gray/blue/green/amber) and shows the count of matching pages
- Filter state is persisted in the URL query string for shareable links

**Sort Options:**

- Sort by: page order (default), translation % ascending, translation % descending
- Sort indicator shows current direction; sorting applies on top of active filter

**Visual Progress:**

- Each page in the list displays a progress bar: `approvedSections / totalSections`
- Color: gray (0%), blue gradient (1-99%), green (100%)
- Percentage label to the right of the bar

**Summary Statistics:**

- Stats bar: total pages, total sections, translated sections, overall completion %, sections pending review
- Updates in near-real-time as translations are approved/rejected

**Edge Cases:**

- Empty state when filter returns zero results: "No pages match — clear filter"
- Pre-detection state: "Process pages first to see translation progress"

---

### US-5.3 Review Translations

**As an** editor
**I want to** review all submitted translations for each section, approve or reject them, and provide my own translation if needed
**So that** only high-quality, accurate translations make it into the final book.

**Acceptance Criteria:**

**Review Console:**

- Accessible from the page list or a dedicated "Review" tab
- Shows one section at a time with cropped section image at top for reference
- All N submitted translations displayed side by side (responsive: stacked on narrow screens)

**Translation Cards:**

- Each card shows: translator name + avatar, submission timestamp (relative), translated text, Approve/Reject buttons
- Approved translations have a green badge and highlighted border
- Rejected translations are dimmed with strikethrough and a red badge

**Approve Multiple:**

- Editor can approve multiple translations for the same section
- The section is considered "translated" once at least one translation is approved
- For build, the most recently approved translation is used

**Reject:**

- Reject shows optional text area for reason; saved to `Translation.rejectionReason`
- Translator receives in-app notification with rejection reason (if provided)

**Editor Override:**

- Editor can write their own translation, auto-approved and labeled "Editor's Choice"
- Editor can copy text from any submitted translation as a starting point

**Re-entry Logic:**

- If ALL translations for a section are rejected, section re-enters the translation pool
- Previously rejected translators may submit improved versions
- A notification triggers: "Section on page N needs re-translation"

**Audit Trail:**

- Every approve/reject action recorded in `TranslationHistoryItem`

---

### US-5.4 Build Finalized Book

**As an** editor
**I want to** generate the finalized translated book as a PDF with all approved translations
**So that** it can be downloaded, shared, or published.

**Acceptance Criteria:**

**Pre-conditions:**

- "Build Book" button enabled only when book has sections and at least one approved translation
- Disabled state shows tooltip explaining what is missing
- Summary panel shows: total/approved/untranslated/pending section counts
- Warning if any sections lack approved translations: "This build will skip {N} sections"

**Trigger Build:**

- Confirmation dialog shows counts and warns about skipped sections
- On confirm, `POST /api/books/{bookId}/build` creates a `BookBuild` with `status: BUILDING`
- A `BookVersion` is created in `DRAFT` status

**Async Processing (Celery):**

- Iterates pages by `order`, sections by `sectionOrder`
- For each section: places most recently approved translation text into bounding box on page image
- Sections without approved translations use original source text as placeholder
- IMAGE_CAPTION sections embed the cropped image directly
- Generates PDF, uploads to `books/{bookId}/versions/{versionNumber}/finalized.pdf`
- On failure: `status: FAILED`, `errorMessage` populated; editor can retry

**Progress & Polling:**

- Frontend polls `GET /api/books/{bookId}/builds/latest` every 3 seconds
- Progress bar: "Building page 23 of 45..."
- Estimated time remaining shown
- "Cancel Build" button available during processing

**Download:**

- On completion, "Download PDF" button appears
- Presigned S3 URL (1-hour expiry) with filename `{book-title}-v{versionNumber}.pdf`
- "Copy Link" option for sharing

**Rebuild & Versioning:**

- Rebuild anytime; each build increments `versionNumber`
- Version history panel: version number, build date, status, approved section count
- Past versions remain downloadable
- "Set as Current" option marks the canonical version

**Notifications:**

- In-app notification on completion: "Version {N} ready for download"
- Badge on book console if user navigated away during build
- Failed builds: notification with error message and "Retry" button

**Edge Cases:**

- Concurrent builds not allowed — button disabled if build in progress
- Large books (500+ pages): batched processing with per-batch progress

## Epic 6: Team Management

### US-6.1 Invite Translators to Book

**As an** editor
**I want to** invite users to translate my book
**So that** I can build a translation team.

**Acceptance Criteria:**

- Search users by email/name
- Send invitation from book settings
- Invited user sees the book in "Assigned to me" list
- Invitation notification appears on dashboard

### US-6.2 Block Translator from Book

**As an** editor
**I want to** block a translator from my book
**So that** problematic users cannot access it.

**Acceptance Criteria:**

- Block option on translator list
- Blocked translator cannot see the book
- Existing translations by that user remain (with "blocked user" label)
- Unblock option available
