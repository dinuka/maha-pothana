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
└─────┘ └───────────────┘  │
                           │
┌──────────────────────────▼──────────────────────────────┐
│                    MongoDB                                │
│  (Users, Books, Pages, Sections, Translations, Comments) │
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
│   │   └── PageItem (status indicator)
│   └── BookSettings
├── PageViewer
│   ├── PageImage (with Konva overlay)
│   │   ├── SectionRectangles (draggable, resizable)
│   │   ├── SectionTypeLabels
│   │   └── AddSectionTool
│   └── SectionEditor (sidebar)
└── TranslationPanel
    ├── TranslationList (for approved)
    └── SectionTranslations

TranslatePage
├── SectionImage (zoomable, from cropped S3 key)
├── AutoTranslationDisplay
├── TranslationEditor
│   ├── TranslatedText (semantic translation)
│   └── ExactLetterText (optional transliteration)
├── MyPreviousTranslation (visible to translator before approval)
├── ApprovedTranslation (visible to all after approval)
├── PageContext (prev/next thumbnails)
└── CommentSection
```

### State Management

- React Server Components for data-fetching pages
- Client Components for interactive pages (Konva editor, translation UI)
- React Context for auth state
- SWR or React Query for client-side data fetching

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
│   │   └── users.py         # User management
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
│   │   └── translation.py   # LibreTranslate integration
│   ├── tasks/
│   │   ├── split_pages.py   # Celery task
│   │   ├── detect_sections.py
│   │   ├── crop_sections.py # Crop and upload section images
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

GET    /api/books/{id}/pages      # List pages
GET    /api/books/{id}/pages/{num}  # Page detail with sections

POST   /api/pages/{id}/sections/detect    # Trigger AI section detection
PUT    /api/pages/{id}/sections           # Save confirmed sections

GET    /api/sections/next          # Get random untranslated section
GET    /api/sections/{id}          # Section detail (with cropped image URL)
POST   /api/sections/{id}/translate  # Submit translation
GET    /api/sections/{id}/translations  # All translations for section
GET    /api/sections/{id}/my-translation  # Translator's own pending translation

POST   /api/sections/{id}/comments    # Add comment
GET    /api/sections/{id}/comments    # List comments

GET    /api/users                # List users (admin)
PUT    /api/users/{id}/roles     # Update user roles (admin)

POST   /api/books/{id}/invite    # Invite translator
POST   /api/books/{id}/block     # Block translator
```

### Celery Task Queue

- `split_pages(book_id)` — Extract PDF pages → PNG images → upload to MinIO
- `detect_sections(page_id)` — Run LayoutParser to detect text blocks → save sections
- `crop_sections(page_id)` — After section confirmation, crop each section from page image → upload to MinIO → update section records with `croppedImageKey`
- `auto_translate(section_id)` — Call LibreTranslate for initial translation
- `build_book(book_id)` — Compile approved translations → generate final PDF → upload to MinIO

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

1. Translator opens translation page → GET /api/sections/next
2. Backend selects random section (excluding ones already translated by this user)
3. Section's cropped image loaded from MinIO via presigned URL (`section.croppedImageKey`)
4. Auto-translated text fetched from LibreTranslate (async or cache)
5. Translator edits, saves → POST translation (with optional `exactLetterTranslation`)
6. Translator can view their own pending translation via GET /api/sections/{id}/my-translation
7. When editor approves a translation, it becomes visible to all translators
8. If editor rejects all translations, section re-enters the pool

### Data Flow: Book Build

1. Editor clicks "Build" → POST /api/books/{id}/build
2. FastAPI enqueues `build_book` Celery task
3. Worker iterates pages in order (using `originalPageNumber` for display labels), lays out approved translations, renders PDF
4. Final PDF uploaded to MinIO
5. Book status updated to COMPLETED

## MongoDB Schema Notes

- **Motor** (async MongoDB driver) used with FastAPI
- **Document embedding** considered for comments (embedded array in Section) vs. separate collection; separate collection chosen for scalability with high comment volumes
- **Indexes** created on startup via `db/indexes.py`:
  - `users`: `{ googleId: 1 }` unique, `{ email: 1 }` unique
  - `books`: `{ ownerId: 1 }`, `{ fileHash: 1 }`, text index on title/author
  - `pages`: `{ bookId: 1, pageNumber: 1 }`
  - `sections`: `{ pageId: 1, sectionOrder: 1 }`
  - `translations`: `{ sectionId: 1, translatorId: 1 }` unique, `{ sectionId: 1, isApproved: 1 }`
  - `comments`: `{ sectionId: 1, createdAt: 1 }`
  - `invitations`: `{ bookId: 1, userId: 1 }` unique

## Security Considerations

- All API routes (except auth) require JWT validation
- JWT from NextAuth passed as Bearer token from frontend
- Backend validates role-based access via middleware
- File uploads via presigned URLs to prevent path traversal
- Input validation with Pydantic on all endpoints
- Rate limiting on auth and translation endpoints
- CORS configured for Next.js origin only

## Offline/Local Development

- Entire stack runs via `docker compose up`
- MinIO replaces AWS S3 (same API, zero code changes for production)
- LibreTranslate runs locally (free, self-hosted)
- Google OAuth requires real credentials (only dev-time external dependency)
