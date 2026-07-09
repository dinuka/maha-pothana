# Maha Pothana — Technical Architecture

## Overview

Maha Pothana is a SaaS application for community-driven book translation. It follows a monorepo structure with a Next.js frontend and FastAPI backend, orchestrated via Docker Compose.

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Nginx (Reverse Proxy)                 │
└────┬────────────────────┬───────────────────┬───────────┘
     │ /api/*             │ /*                │ /ws/* ?
┌────▼──────┐    ┌────────▼────────┐    ┌─────▼──────────┐
│  FastAPI   │    │   Next.js 16    │    │  WebSocket     │
│  (Backend) │    │   (Frontend)    │    │  (optional)    │
└──┬─────┬───┘    └────────┬────────┘    └────────────────┘
   │     │                 │
┌──▼──┐ ┌▼──────────────┐  │
│Redis│ │Celery Workers  │  │
│     │ │- Page Split    │  │
│     │ │- OCR/Section   │  │
│     │ │- Translation   │  │
│     │ │- Section Crop  │  │
│     │ │- Book Build    │  │
│     │ │- AI Extract    │  │
│     │ │- Transliterate │  │
└─────┘ └───────┬────────┘  │
                │            │
         ┌──────▼──────┐     │
         │ OpenAI API   │     │
         │ (GPT-4o)     │     │
         └─────────────┘     │
                            │
┌──────────────────────────▼──────────────────────────────┐
│                    MongoDB                                │
│  (Users, Books, Pages, Sections, Translations, Comments, │
│   AITextExtractions, Transliterations, SystemConfig)      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    MinIO (S3-compatible)                 │
│  books/{bookId}/original.pdf                            │
│  books/{bookId}/pages/{pageNum}.png                     │
│  books/{bookId}/sections/{sectionId}.png                │
│  books/{bookId}/thumbnail.png                           │
│  books/{bookId}/finalized.pdf                           │
└─────────────────────────────────────────────────────────┘
```

## Frontend Architecture (apps/web)

### Route Design

```
/                          → Landing page
/auth/signin               → Google SSO login
/dashboard                 → User dashboard (role-aware)
/books                     → Book list
/books/new                 → Upload book form
/books/{bookId}            → Book translate console
/books/{bookId}/pages/{pageNum} → Page editor (section detection)
/translate                 → Translation queue (for translators)
/translate/{sectionId}     → Translation editor
/admin/users               → User management (super admin only)
```

### Component Tree (Key Pages)

```
Dashboard
├── Header (user info, role badge)
├── EditorPanel (if editor)
│   ├── BookList
│   └── UploadButton
└── TranslatorPanel (if translator)
    └── TranslationQueue

BookConsole
├── BookSidebar
│   ├── PageList
│   │   ├── PageItem (draggable, status indicator, progress bar)
│   │   └── AddPageButton (between pages + at bottom)
│   ├── BookSettings
│   └── VersionHistoryPanel (new)
│       └── VersionItem (download, set as current)
├── PageViewer
│   ├── PageImage (with Konva overlay)
│   │   ├── SectionRectangles (draggable, resizable)
│   │   ├── SectionTypeLabels
│   │   └── AddSectionTool
│   └── SectionEditor (sidebar)
├── TranslationReviewPanel (new)
│   ├── SectionImageDisplay
│   ├── TranslationCards (side-by-side)
│   │   ├── TranslationCard (approve, reject, status badge)
│   │   └── EditorOverride (textarea + save)
│   └── ReviewActions
├── TranslationPanel
│   ├── TranslationList (for approved)
│   └── SectionTranslations
└── BuildPanel (new)
    ├── BuildSummary (section counts, warnings)
    ├── BuildButton (with progress when active)
    ├── BuildProgress (progress bar, cancel button)
    └── DownloadButton (after completion)

TranslatePage
├── TranslateHeader (book title, back nav)
├── TranslateFilters (language dropdown, page filter, status filter)
├── TabBar (Translate | History | Stats)
├── TranslateTab (active when Translate selected)
│   ├── SectionImageDisplay (zoomable, shared zoom with source text)
│   │   ├── CroppedSectionImage (from cropped S3 key)
│   │   └── ZoomControls
│   ├── SourceTextPanel (AI/OCR toggle, confidence badge, extract button)
│   │   ├── TextToggle ("AI Extracted" | "OCR")
│   │   ├── OriginalText / AIExtractedText (read-only, labeled)
│   │   ├── ConfidenceBadge (green/yellow/red)
│   │   └── ExtractButton (editors only)
│   ├── TranslationEditor
│   │   ├── TranslatedText (semantic translation)
│   │   ├── TransliterateButton (AI transliteration trigger)
│   │   ├── ExactLetterText (pre-filled from transliteration, editable)
│   │   └── DraftSaveIndicator
│   ├── MyPreviousTranslation (visible to translator before approval)
│   ├── ApprovedTranslation (visible to all after approval)
│   ├── PageContext (prev/next thumbnails)
│   └── CommentSection
├── HistoryTab (active when History selected)
│   ├── HistoryFilters (independent from TranslateTab filters)
│   ├── HistoryList
│   │   └── HistoryItem (thumbnail, snippet, status badge, timestamp)
│   └── InfiniteScrollIndicator
└── StatsTab (active when Stats selected, editor-only)
    ├── TranslationStatsCard (progress bar, counts)
    ├── PerPageBreakdown (green/yellow/gray grid)
    ├── PerLanguageBreakdown
    └── TranslatorStatsTable (sortable columns, expandable rows)
```

### State Management

- React Server Components for data-fetching pages
- Client Components for interactive pages (Konva editor, translation UI)
- React Context for auth state
- **React Query (TanStack Query)** for all client-side data fetching (translation queue, history, stats, drafts)
  - `useQuery` for reads (history, stats, next section)
  - `useMutation` for writes (submit translation, save draft, approve/reject)
  - `queryClient.invalidateQueries` to refetch after mutations
  - 30s stale time for stats queries, immediate refetch for queue
- URL query params for filter state (persisted, shareable, survives reload)
- `useReducer` for complex local state in the translation editor (text, exact letter, draft status, dirty flag)

### Key Libraries

- **konva** + **react-konva** — Canvas-based section rectangle editor
- **next-auth** — Google SSO
- **shadcn/ui** — UI components (installed via `@radix-ui/*` primitives)
- **tailwindcss** — Styling
- **@s3-transfer** or **presigned URLs** — Direct S3 uploads

## Backend Architecture

### FastAPI Application Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app entry
│   ├── config.py            # Settings from env
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py          # Auth routes
│   │   ├── books.py         # Book CRUD
│   │   ├── pages.py         # Page operations
│   │   ├── sections.py      # Section operations
│   │   ├── translations.py  # Translation routes
│   │   ├── users.py         # User management
│   │   ├── extraction.py    # AI text extraction & transliteration routes
│   │   └── admin_settings.py # Admin config for AI extraction
│   ├── models/
│   │   ├── user.py          # MongoDB document models
│   │   ├── book.py
│   │   ├── page.py
│   │   ├── section.py
│   │   ├── translation.py
│   │   └── comment.py
│   ├── schemas/
│   │   └── ...              # Pydantic models (request/response)
│   ├── services/
│   │   ├── s3.py            # MinIO/S3 operations
│   │   ├── pdf.py           # PDF processing
│   │   ├── ocr.py           # OCR + section detection
│   │   ├── crop.py          # Crop section images from page images
│   │   ├── translation.py   # LibreTranslate integration
│   │   └── ai_text.py       # OpenAI GPT-4o Vision + text for extraction & transliteration
│   ├── tasks/
│   │   ├── split_pages.py   # Celery task
│   │   ├── detect_sections.py
│   │   ├── crop_sections.py # Crop and upload section images
│   │   ├── auto_translate.py
│   │   ├── extract_section_text.py  # Single-section AI extraction
│   │   ├── batch_extract_book.py    # Batch extraction with progress
│   │   ├── transliterate_section.py # AI transliteration
│   │   └── build_book.py
│   └── db/
│       ├── client.py        # MongoDB client (Motor)
│       └── indexes.py       # Ensure indexes on startup
├── Dockerfile
└── requirements.txt
```

### API Endpoints

```
POST   /api/auth/google           # Google SSO callback
GET    /api/auth/me               # Current user info

GET    /api/books                 # List books (filtered by role)
POST   /api/books                 # Upload new book
GET    /api/books/{id}            # Book detail
PUT    /api/books/{id}            # Update book metadata
DELETE /api/books/{id}            # Delete book
POST   /api/books/{id}/build      # Trigger final build
GET    /api/books/{id}/stats      # Translation stats (cached, editor-only)
GET    /api/books/{id}/translators/stats  # Per-translator performance (editor-only)

GET    /api/books/{id}/pages      # List pages
GET    /api/books/{id}/pages/{num}  # Page detail with sections

POST   /api/pages/{id}/sections/detect    # Trigger AI section detection
PUT    /api/pages/{id}/sections           # Save confirmed sections

GET    /api/sections/next?bookId={bookId}&language={lang}&page={pageNum}&status={status}
                                     # Get random untranslated section (with filters)
GET    /api/sections/{id}          # Section detail (with cropped image URL)
POST   /api/sections/{id}/translate  # Submit translation
GET    /api/sections/{id}/translations  # All translations for section
GET    /api/sections/{id}/my-translation  # Translator's own pending translation

POST   /api/sections/{id}/comments    # Add comment
GET    /api/sections/{id}/comments    # List comments

GET    /api/translations/history?bookId={bookId}&translatorId={translatorId}
         &language={lang}&page={pageNum}&status={status}&cursor={cursor}&limit={20}
                                     # Translation history (paginated, filtered)
POST   /api/translations/draft     # Upsert translation draft
GET    /api/translations/draft?sectionId={sectionId}  # Fetch draft
DELETE /api/translations/draft/{id}  # Delete draft after submission

POST   /api/books/{id}/invite    # Invite translator
POST   /api/books/{id}/block     # Block translator

POST   /api/sections/{id}/extract  # Trigger single-section AI text extraction (202)
POST   /api/books/{id}/pages/{num}/extract  # Batch extract all sections on a page (202)
POST   /api/books/{id}/extract     # Batch extract ALL sections in a book (202)
GET    /api/sections/{id}/extraction  # Fetch extraction result with confidence
POST   /api/sections/{id}/transliterate?targetScript={script}  # Generate transliteration
GET    /api/sections/{id}/transliterations  # Fetch cached transliterations
PUT    /api/sections/{id}/source-text  # Update source text (AI or OCR), invalidate transliteration cache
GET    /api/books/{id}/extraction/status  # Batch extraction progress

GET    /api/admin/settings/extraction  # Fetch AI extraction config (admin only)
PUT    /api/admin/settings/extraction  # Update AI extraction config (admin only)
GET    /api/admin/extraction/audit     # Extraction audit log (admin only)

# --- Epic 5: Book Organization & Publishing ---

PUT    /api/books/{bookId}/pages/reorder          # Batch reorder pages
POST   /api/books/{bookId}/pages                  # Add blank page
DELETE /api/pages/{pageId}                        # Delete page and cascade
GET    /api/books/{bookId}/pages?filter={status}&sort={field}&order={asc|desc}&page={n}&limit={20}  # Filter/sort pages
GET    /api/pages/{pageId}/history                # Section edit history
PUT    /api/translations/{translationId}/approve   # Approve translation
PUT    /api/translations/{translationId}/reject    # Reject translation (body: {reason?: string})
POST   /api/sections/{sectionId}/translations      # Editor override translation
GET    /api/books/{bookId}/builds/latest            # Poll latest build progress
DELETE /api/books/{bookId}/builds/latest            # Cancel current build
GET    /api/books/{bookId}/builds                   # List all builds
GET    /api/books/{bookId}/versions                  # List all versions
POST   /api/books/{bookId}/versions                 # Create manual version
GET    /api/books/{bookId}/versions/{versionNumber}/download  # Download version PDF
```

### Celery Task Queue

- `split_pages(book_id)` — Extract PDF pages → PNG images → upload to MinIO
- `detect_sections(page_id)` — Run LayoutParser to detect text blocks → save sections
- `crop_sections(page_id)` — After section confirmation, crop each section from page image → upload to MinIO → update section records with `croppedImageKey`
- `auto_translate(section_id)` — Call LibreTranslate for initial translation
- `build_book(book_id)` — Compile approved translations → generate final PDF → upload to MinIO
- `expire_drafts()` — (scheduled, hourly) Delete TranslationDraft documents older than 24h via TTL index
- `extract_section_text(section_id)` — Send cropped image to GPT-4o Vision API → save AI-extracted text + confidence to `AITextExtraction` → update `Section.aiExtractedText`
- `batch_extract_book(book_id)` — Chain of `extract_section_text` tasks for all unextracted sections in a book; progress tracked in Redis; max 5 concurrent via semaphore
- `transliterate_section(section_id, target_script)` — Call GPT-4o for letter-for-letter script conversion → save to `Transliteration` collection; cache-first lookup

## Deployment Architecture

### Docker Compose Services

```yaml
services:
  nginx: # Reverse proxy (port 80)
  nextjs: # Frontend (port 3000)
  fastapi: # Backend API (port 8000)
  celery: # Async task worker
  mongodb: # Database (port 27017)
  redis: # Cache + Celery broker (port 6379)
  minio: # S3-compatible storage (ports 9000, 9001)
  libretranslate: # Free translation API (port 5000)
```

### Data Flow: Book Upload

1. Editor uploads PDF via Next.js (presigned URL → direct to MinIO)
2. Next.js calls FastAPI to create Book document in MongoDB
3. FastAPI enqueues `split_pages` Celery task
4. Celery worker splits PDF, uploads page images to MinIO, creates Page documents
5. Frontend polls book status → shows "Processing complete" when done

### Data Flow: Section Detection

1. Editor opens page in console
2. Frontend requests detection (or detection auto-runs after page split)
3. Celery `detect_sections` runs LayoutParser on page image → creates Section documents
4. Frontend fetches sections and renders Konva rectangles overlay
5. Editor modifies sections, clicks Confirm
6. PUT /sections saves final positions
7. Celery `crop_sections` runs: for each section, crops the region from the page image, uploads cropped PNG to `books/{bookId}/sections/{sectionId}.png`, updates section record with `croppedImageKey`

### Data Flow: Translation

1. Translator opens `/translate` → page auto-loads first section via GET /api/sections/next
2. Backend selects random section (excluding ones already translated by this user), respecting active filters (language, page, status)
3. Section's cropped image loaded from MinIO via presigned URL (`section.croppedImageKey`)
4. Source text displayed alongside the section image (from `Section.originalText`)
5. Auto-translated text pre-fills the translation input as starting point
6. Translation input auto-saves to draft (debounced 5s) via POST /api/translations/draft
7. On page load, existing draft is fetched and pre-fills the input
8. Translator edits, clicks Submit → POST translation → draft deleted
9. Translator can view their own pending translation via GET /api/sections/{id}/my-translation
10. When editor approves a translation, it becomes visible to all translators
11. If editor rejects all translations, section re-enters the pool

### Data Flow: Translation History

1. Translator clicks "History" tab → GET /api/translations/history?bookId=X&limit=20
2. Backend queries Translation collection joined with Section and User, sorted by createdAt descending
3. Translator sees only own translations; editors see all translations for the book
4. History supports cursor-based pagination (infinite scroll loads more)
5. Filters (language, page, status) are applied independently from the Translate tab
6. Clicking a history item navigates to `/translate?section={sectionId}`

### Data Flow: Translation Statistics

1. Editor opens Stats tab → GET /api/books/{bookId}/stats
2. Backend runs MongoDB aggregation pipeline over Translations + Sections + Pages
3. Results cached in Redis with 30s TTL key: `stats:{bookId}`
4. Frontend polls every 30s (aligned with cache TTL) or refetches on tab focus
5. Per-language and per-page breakdowns rendered in charts
6. Per-translator stats via GET /api/books/{bookId}/translators/stats (separate cache key)

### Data Flow: Page Reorder

1. Editor drags page in sidebar
2. Drop triggers PUT /api/books/{bookId}/pages/reorder with `{ orders: [{pageId, order}] }`
3. Backend validates all pageIds belong to this book
4. Backend uses bulkWrite to update all page documents atomically
5. Frontend optimistically updates UI, invalidates page list query on success
6. On conflict (simultaneous edit by another editor): toast warning, refresh

### Data Flow: Translation Review

1. Editor opens review console for a section
2. Frontend calls GET /api/sections/{sectionId}/translations
3. Backend queries Translation collection where sectionId matches
4. Returns array sorted by createdAt, each with translator info
5. Editor approves → PUT /api/translations/{id}/approve
6. Editor rejects → PUT /api/translations/{id}/reject (with optional reason)
7. Editor submits own → POST /api/sections/{sectionId}/translations
8. If all translations rejected → section transitions to "pending" → re-enters translation pool
9. Audit log entries created for each action

### Data Flow: Book Build with Versioning

1. Editor clicks Build → POST /api/books/{bookId}/build
2. Backend validates pre-conditions, creates BookBuild(status=BUILDING) + BookVersion(status=DRAFT)
3. Celery build_book task:
   a. Fetch pages ordered by `order`
   b. Per page: fetch sections ordered by `sectionOrder`
   c. Per section: get most recently approved translation (or original text fallback)
   d. Render page image with overlaid translated text in section bounding boxes
   e. Compile into PDF
   f. Upload to S3: books/{bookId}/versions/{versionNumber}/finalized.pdf
   g. Update BookBuild: status=COMPLETED, fileKey, versionNumber, buildDurationMs
   h. Update BookVersion: status=FINALIZED
4. Frontend polls GET /api/books/{bookId}/builds/latest every 3s
5. On completion, Download button appears with presigned URL
6. Each rebuild increments versionNumber; previous builds remain accessible

### Data Flow: AI Text Extraction

1. Editor clicks "Extract Text" on a section → POST /api/sections/{id}/extract
2. FastAPI enqueues `extract_section_text` Celery task, returns 202 with taskId
3. Worker downloads cropped section image from MinIO
4. Worker acquires Redis semaphore (max 5 concurrent)
5. Worker sends base64 image to OpenAI GPT-4o Vision API
6. Worker receives extracted text, then calls GPT-4o (text-only) for confidence scoring
7. Worker saves result to `AITextExtraction` collection and updates `Section.aiExtractedText`
8. Worker releases semaphore
9. Frontend polls GET /api/sections/{id}/extraction → shows confidence badge

### Data Flow: Batch Extraction

1. Editor clicks "Extract All" → POST /api/books/{id}/extract
2. FastAPI checks cost estimate against `SystemConfig.costLimitPerBook`
3. FastAPI enqueues `batch_extract_book` Celery task
4. Worker creates chain of `extract_section_text` tasks (5 concurrent via semaphore)
5. Progress tracked in Redis: `{bookId}:extraction:progress` (total, completed, failed)
6. Frontend polls GET /api/books/{id}/extraction/status → shows progress bar
7. On completion, summary shown: "154 extracted, 2 failed" with "Retry Failed" button

### Data Flow: Transliteration

1. Translator clicks "Transliterate" → POST /api/sections/{id}/transliterate?targetScript=sinhala
2. FastAPI checks `Transliteration` collection for cached result
3. If cached, returns immediately
4. If not cached, enqueues `transliterate_section` Celery task
5. Worker fetches `Section.aiExtractedText` (falls back to `originalText`)
6. Worker calls GPT-4o (text-only) for letter-for-letter script conversion
7. Worker saves to `Transliteration` collection
8. Frontend pre-fills `exactLetterTranslation` field; translator can edit before submitting

### Data Flow: Source Text Update (Bidirectional Sync)

1. User edits source text → PUT /api/sections/{id}/source-text
2. FastAPI updates `Section.aiExtractedText` or `Section.originalText` based on `source` param
3. FastAPI invalidates cached `Transliteration` documents for this section
4. Frontend re-enables "Transliterate" button (cache cleared)
5. Next auto-translation uses the updated source text

## MongoDB Schema Notes

- **BookVersion** — Stores version history snapshots for the book. Each BookBuild automatically creates a BookVersion record; editors can also manually create versions with custom labels (e.g., "Draft for proofreading v2"). Fields: `bookId` (ref Book), `versionNumber` (int, sequential), `buildId` (ref BookBuild, nullable for manual), `label` (string), `changelog` (string), `fileKey` (string, S3 key for PDF), `createdBy` (ref User), `status` (DRAFT, FINALIZED, ARCHIVED), `createdAt`, `updatedAt`.
- **Motor** (async MongoDB driver) used with FastAPI
- **Document embedding** considered for comments (embedded array in Section) vs. separate collection; separate collection chosen for scalability with high comment volumes
- **Indexes** created on startup via `db/indexes.py`:
  - `users`: `{ googleId: 1 }` unique, `{ email: 1 }` unique
  - `books`: `{ ownerId: 1 }`, `{ fileHash: 1 }`, text index on title/author
  - `pages`: `{ bookId: 1, pageNumber: 1 }`, `{ bookId: 1, order: 1 }`
  - `sections`: `{ pageId: 1, sectionOrder: 1 }`
  - `translations`: `{ sectionId: 1, translatorId: 1 }` unique, `{ sectionId: 1, isApproved: 1 }`, `{ sectionId: 1, rejected: 1 }`, `{ createdAt: -1 }`, `{ translatorId: 1, createdAt: -1 }` (for history queries)
  - `comments`: `{ sectionId: 1, createdAt: 1 }`
  - `invitations`: `{ bookId: 1, userId: 1 }` unique
  - `book_builds`: `{ bookId: 1, versionNumber: -1 }`
  - `book_versions`: `{ bookId: 1, versionNumber: -1 }`
  - `translation_drafts`: `{ sectionId: 1, translatorId: 1 }` unique, TTL index on `createdAt` (24h expiry)
  - `ai_text_extractions`: `{ sectionId: 1 }` unique (AI extraction results)
  - `transliterations`: `{ translationId: 1 }` unique (AI transliteration cache)
  - `system_config`: `{ key: 1 }` unique (admin configuration key-value store)
- **Section schema additions**: `aiExtractedText` (string, nullable) stores AI-extracted text; `originalText` remains as OCR fallback
- **Translation schema additions**: `exactLetterTranslation` (string, nullable) stores transliteration; `transliterationSource` ("ai" | "manual") tracks origin

## Security Considerations

- All API routes (except auth) require JWT validation
- JWT from NextAuth passed as Bearer token from frontend
- Backend validates role-based access via middleware
- File uploads via presigned URLs to prevent path traversal
- Input validation with Pydantic on all endpoints
- Rate limiting on auth and translation endpoints
- CORS configured for Next.js origin only
- **OpenAI API key** stored in env var `OPENAI_API_KEY`, never committed; used server-side only in Celery workers
- **AI extraction cost limits** enforced server-side via `SystemConfig` to prevent budget overruns
- **Admin-only endpoints** for AI configuration require SUPER_ADMIN role

## Offline/Local Development

- Entire stack runs via `docker compose up`
- MinIO replaces AWS S3 (same API, zero code changes for production)
- LibreTranslate runs locally (free, self-hosted)
- Google OAuth requires real credentials (only dev-time external dependency)
