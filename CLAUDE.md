# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Maha Pothana is a collaborative book translation platform. Editors upload PDFs, annotate pages with section rectangles (via Konva.js canvas), and translators work through sections one-by-one to produce translated books. It's a Turborepo monorepo with a Next.js 16 frontend and FastAPI + Celery backend.

## Commands

Run from repo root unless noted:

```sh
pnpm dev                                    # frontend (port 3000) + backend (port 8000) dev servers
pnpm build                                  # build all packages & apps
pnpm lint                                   # strict lint (--max-warnings 0)
pnpm check-types                            # tsc --noEmit (also runs next typegen)
pnpm format                                 # prettier over **/*.{ts,tsx,md}
pnpm --filter=web test                      # Vitest unit tests (jsdom, 33 tests)
pnpm --filter=web test:watch                # Vitest in watch mode

# Backend (requires MongoDB + Redis running)
cd apps/api && uvicorn app.main:app --reload --port 8000
cd apps/api && python -m pytest tests/ -v   # 41 pytest tests
cd apps/api && celery -A app.tasks.celery_app worker --loglevel=info

# Infrastructure only (MongoDB, Redis, MinIO, LibreTranslate)
docker compose -f infra/docker-compose.dev.yml up -d

# Full production stack
docker compose -f infra/docker-compose.yml build
docker compose -f infra/docker-compose.yml up -d
```

To run a single Vitest test file: `pnpm --filter=web vitest run __tests__/Header.test.tsx`  
To run a single pytest test: `cd apps/api && python -m pytest tests/test_books.py -v`

## Architecture

### Request Flow

Nginx reverse-proxies `/api/*` to FastAPI (port 8000) and `/*` to Next.js (port 3000). Auth flows through NextAuth v5 which posts to `/api/auth/google` on sign-in to register/sync the user with the FastAPI backend.

### Auth Model

- NextAuth v5 handles Google OAuth. On successful sign-in the `signIn` callback POSTs to FastAPI to upsert the user and fetch their roles.
- Roles: `SUPER_ADMIN`, `EDITOR`, `TRANSLATOR` (defined in `apps/web/lib/auth.ts`).
- JWT token is extended with `{ id, roles }` via `jwt` + `session` callbacks.
- FastAPI validates the JWT Bearer token in middleware; routes under `/api/auth/...` are public.
- Between Next.js and FastAPI, the `INTERNAL_API_KEY` env var acts as a shared secret for server-to-server calls.

### Frontend (`apps/web`)

- **Next.js 16 App Router** with React Server Components for data-fetching pages and Client Components for interactive UI.
- **Konva.js / react-konva** for the canvas-based section rectangle editor on book pages.
- **CSS Modules** (`*.module.css`) for page-level styles.
- Tests in `__tests__/` use Vitest + jsdom + `@testing-library/react`. The alias `@` maps to the `apps/web` root.

Routes:

```
/                          → Landing page
/auth/signin               → Google SSO
/dashboard                 → Role-aware dashboard
/books                     → Book list
/books/new                 → Upload book
/books/[bookId]            → Book translate console (Konva section editor)
/books/[bookId]/pages/[pageNum] → Page editor
/translate                 → Translation queue
/translate/[sectionId]     → Translation editor
/admin/users               → User management (SUPER_ADMIN only)
```

### Backend (`apps/api`)

FastAPI with Motor (async MongoDB) and Celery + Redis.

Module layout:

- `app/config.py` — settings loaded from env
- `app/db/` — Motor client + startup index creation
- `app/api/` — FastAPI routers (auth, books, pages, sections, translations, users)
- `app/schemas/` — Pydantic v2 request/response models
- `app/services/` — business logic (s3, pdf, ocr, crop, translation)
- `app/tasks/` — Celery tasks (split_pages, detect_sections, crop_sections, auto_translate, build_book)
- `app/models/` — MongoDB document shape types

Backend conventions:

- Motor raw driver, no Beanie ODM. `AsyncIOMotorDatabase` injected via `Depends(get_db)`.
- Celery tasks use `run_async()` helper to call async Motor code from sync workers.
- Backend tests use `pytest-asyncio` (asyncio_mode = auto), `httpx.AsyncClient` with `ASGITransport`, and mock `AsyncIOMotorDatabase` via `unittest.mock.AsyncMock`.
- No `function` keyword; use `async def`; type hints required everywhere.

### File Storage (MinIO)

S3 key layout:

```
books/{bookId}/original.pdf
books/{bookId}/pages/{pageNum}.png
books/{bookId}/thumbnails/{pageNum}.png
books/{bookId}/sections/{sectionId}.png
books/{bookId}/thumbnail.png
books/{bookId}/finalized.pdf
```

### Shared Packages

- `packages/ui` — `@repo/ui` shared React components. Import as `@repo/ui/button` (not barrel). Components use **named exports** (`export const Button = ...`). Scaffold new components with `turbo gen react-component`.
- `packages/eslint-config` — ESLint 9 flat config. ESLint is pinned to 9.x because `eslint-plugin-react` doesn't support ESLint 10.
- `packages/typescript-config` — shared tsconfig bases.

## Key Data Flows

**Book upload**: Editor uploads PDF via presigned URL → Next.js creates Book in MongoDB → FastAPI enqueues `split_pages` → Celery splits PDF to page PNGs in MinIO → Frontend polls book status.

**Section detection**: Editor triggers detection → Celery `detect_sections` runs LayoutParser on page image → sections saved to MongoDB → Frontend fetches and renders Konva rectangles → Editor confirms → `crop_sections` task crops each section from the page image and uploads to MinIO, updating `croppedImageKey` on each section.

**Translation**: Translator hits `/translate` → GET `/api/sections/next` returns a random unworked section → translator sees cropped image from MinIO + auto-translation from LibreTranslate → submits translation → editor approves/rejects.

## Environment

Copy `.env.example` to `.env`. Required vars: `AUTH_GOOGLE_ID`, `AUTH_GOOGLE_SECRET`, `AUTH_SECRET`. See `.env.example` for the full list including MongoDB, Redis, MinIO, and LibreTranslate URLs.
