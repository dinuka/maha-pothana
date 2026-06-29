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

### US-3.2 Section Detection

**As an** editor
**I want to** view detected sections on a page
**So that** I can organize them for translation.

**Acceptance Criteria:**

- Page image displayed with overlaid colored rectangles for each detected section
- Section types identified: header, paragraph, footnote, image caption, page number
- Each rectangle labeled with section type
- Editor can click a rectangle to see its properties
- Detected sections are non-destructive — can be modified before confirming

### US-3.3 Edit Sections

**As an** editor
**I want to** modify detected sections (drag, resize, delete, add)
**So that** the section layout is accurate before translation.

**Acceptance Criteria:**

- Click and drag to move a section rectangle
- Drag corner/edge handles to resize a section
- Delete button removes a section (with undo)
- Draw tool to create a new section rectangle
- Each section has a type selector (header/paragraph/footnote/etc)
- Changes are saved locally until "Confirm" is pressed

### US-3.4 Confirm Sections

**As an** editor
**I want to** confirm and export the finalized sections
**So that** they become available for translation.

**Acceptance Criteria:**

- "Confirm" button saves all section positions and types to DB
- Each section gets a unique ID
- Section data includes: position (x, y, width, height), type, page number, order
- After confirmation, sections appear in the translation pool
- Confirmed sections can still be edited by re-opening the page

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

### US-5.1 Organize Pages & Sections

**As an** editor
**I want to** add, edit, and delete pages and sections
**So that** the final book structure is correct.

**Acceptance Criteria:**

- Page list view with drag-to-reorder
- Add a blank page between existing pages
- Delete a page (with confirmation)
- Edit section content, position, type
- Changes tracked with version history

### US-5.2 Filter & Sort Translation Progress

**As an** editor
**I want to** filter and sort pages by translation status
**So that** I can focus on incomplete work.

**Acceptance Criteria:**

- Filter: All, Completed, In Progress, Not Started
- Sort: by page number, by translation % ascending/descending
- Visual progress bar per page
- Summary stats: X of Y sections translated

### US-5.3 Review Translations

**As an** editor
**I want to** see all translations for a section
**So that** I can select or provide the best one.

**Acceptance Criteria:**

- If N translators required, show all N translations side by side
- Each translation labeled with translator name and timestamp
- Editor can **approve multiple translations** if they convey the same meaning or accurately represent the source
- Editor can **reject any or all translations** if they are incorrect
- Editor can write their **own translation** using the submitted ones as reference
- If all translations are rejected, the section re-enters the translation pool; translators must keep translating until at least one is approved
- Approved translation marked clearly with badge

### US-5.4 Build Finalized Book

**As an** editor
**I want to** generate the finalized translated book
**So that** it can be downloaded or published.

**Acceptance Criteria:**

- "Build" button generates the book with approved translations
- Processing runs asynchronously
- Progress indicator during build
- Final book stored in S3 as PDF
- Download link available
- Editor can rebuild anytime (overwrites previous)

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
