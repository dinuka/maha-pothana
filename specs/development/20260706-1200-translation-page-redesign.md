# Development Implementation Spec: Translation Page Redesign

## Overview

This spec documents the implementation of the Translation Page Redesign feature (US-TR-1 through US-TR-6), transforming the minimal `/translate` page into a full-featured translation console.

## Architecture Decisions

### Backend (FastAPI + Motor + Redis)

**Stats API (`/api/books/{bookId}/stats`):**

- Uses MongoDB aggregation pipeline for `totalSections`, `completedTranslations`, `pendingTranslations`, `averageConfidence`
- Per-page stats via nested `$group` on `page` field from section lookups
- Redis caching with 30s TTL (`stats:{bookId}` key), graceful fallback if Redis unavailable
- `GET /api/books/{bookId}/stats/translators` returns per-translator completion counts

**History API (`/api/translations/history`):**

- Cursor-based pagination using `createdAt` field (not offset) for stable infinite scroll
- Returns last 20 items per request, sorted descending by `createdAt`
- Optional `bookId` query parameter for filtering

**Draft API (`/api/translations/drafts`):**

- CRUD endpoints for auto-save drafts: `GET`, `POST` (upsert), `DELETE`
- `GET /api/translations/drafts?sectionId=X` returns latest draft for a section
- `POST` upserts by `(sectionId, translatorId)` unique key
- MongoDB TTL index on `createdAt` with 24h expiry for automatic cleanup
- Drafts stored in `translation_drafts` collection

**Section Next API (`/api/sections/next`):**

- Extended with optional filter params: `bookId`, `language`, `page`, `status`
- Status filter: `pending` excludes sections with translations, `completed` only sections with translations
- Language filter matches `translation.language` field on translations collection

### Frontend (Next.js + React)

**Component Structure:**

```
apps/web/app/translate/
├── page.tsx                    # Tabbed layout with Suspense boundaries
├── TranslateTab.tsx            # Side-by-side translate UI
├── HistoryTab.tsx              # Infinite scroll history list
├── StatsTab.tsx                # Statistics dashboard
├── TranslateFilters.tsx        # Filter bar (book, language, page, status)
└── components/
    ├── SourceTextPanel.tsx     # Source text + language labels
    ├── DraftSaveIndicator.tsx  # Save status feedback
    ├── HistoryItem.tsx         # Translation history row
    └── TranslatorStatsRow.tsx  # Translator stats row
```

**Data Fetching Pattern:**

- Regular async functions inside `useEffect` for data fetching (not `useCallback`)
- `useRef` for cursor tracking in pagination to avoid stale closures
- `filtersRef` pattern to access latest filters inside async callbacks without triggering re-renders
- ESLint suppressions for `react-hooks/set-state-in-effect` and `react-hooks/exhaustive-deps` on standard data-fetching patterns

**Draft Auto-save:**

- 5-second debounce using `setTimeout`/`clearTimeout` in `useEffect` cleanup
- `localStorage` fallback for offline drafts (key: `draft:{sectionId}`)
- `beforeunload` event listener to warn about unsaved changes
- `DraftSaveIndicator` component shows: idle → saving → saved → error states

**URL-synced Filters:**

- `useSearchParams` from `next/navigation` for reading/writing filter state to URL
- `useRouter` with `replace` (not `push`) to avoid polluting browser history
- Default values: `bookId=any`, `language=any`, `page=any`, `status=pending`

**Tab Layout:**

- Three tabs: Translate, History, Statistics
- ARIA roles: `role="tablist"`, `role="tab"`, `role="tabpanel"`
- `aria-selected` on active tab
- `Suspense` boundaries around each tab content component

### File Storage (MinIO)

- Source text images: `books/{bookId}/sections/{sectionId}.png`
- Cropped section images: `books/{bookId}/sections/{sectionId}.png`
- Book thumbnails: `books/{bookId}/thumbnail.png`

## Files Modified

| File                                                       | Change                                                                                    |
| ---------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `apps/api/app/api/sections.py`                             | Added filter params (`bookId`, `language`, `page`, `status`) to `/api/sections/next`      |
| `apps/api/app/api/books_stats.py`                          | New - Stats endpoints with Redis caching                                                  |
| `apps/api/app/api/translations_history.py`                 | New - History endpoint with cursor pagination                                             |
| `apps/api/app/api/translations_draft.py`                   | New - Draft CRUD endpoints                                                                |
| `apps/api/app/main.py`                                     | Registered 3 new routers                                                                  |
| `apps/api/app/db/indexes.py`                               | Added `translation_drafts` TTL index                                                      |
| `apps/api/app/schemas/stats.py`                            | New - `TranslationStatsResponse`, `LanguageStats`, `PageStats`, `TranslatorStatsResponse` |
| `apps/api/app/schemas/history.py`                          | New - `TranslationHistoryItem`, `TranslationHistoryResponse`                              |
| `apps/api/app/schemas/draft.py`                            | New - `DraftCreate`, `DraftResponse`                                                      |
| `apps/web/app/translate/page.tsx`                          | Rewritten - Tabbed layout with Suspense                                                   |
| `apps/web/app/translate/TranslateTab.tsx`                  | New - Side-by-side translate UI                                                           |
| `apps/web/app/translate/HistoryTab.tsx`                    | New - Infinite scroll history                                                             |
| `apps/web/app/translate/StatsTab.tsx`                      | New - Statistics dashboard                                                                |
| `apps/web/app/translate/TranslateFilters.tsx`              | New - Filter bar                                                                          |
| `apps/web/app/translate/components/SourceTextPanel.tsx`    | New - Source text display                                                                 |
| `apps/web/app/translate/components/DraftSaveIndicator.tsx` | New - Draft save feedback                                                                 |
| `apps/web/app/translate/components/HistoryItem.tsx`        | New - History row                                                                         |
| `apps/web/app/translate/components/TranslatorStatsRow.tsx` | New - Translator stats row                                                                |
| `apps/web/hooks/useTranslationDraft.ts`                    | New - Auto-save hook with debounce                                                        |
| `apps/web/hooks/useTranslationFilters.ts`                  | New - URL-synced filters hook                                                             |
| `apps/web/lib/api/translations.ts`                         | New - API client functions                                                                |

## Files Added (Tests)

| File                                           | Tests                                                             |
| ---------------------------------------------- | ----------------------------------------------------------------- |
| `apps/api/tests/test_books_stats.py`           | 7 tests - Stats endpoints, Redis caching, per-translator stats    |
| `apps/api/tests/test_translations_history.py`  | 4 tests - History pagination, book filtering, empty state         |
| `apps/api/tests/test_translations_draft.py`    | 6 tests - Draft CRUD, upsert, TTL expiry                          |
| `apps/web/__tests__/TranslatePage.test.tsx`    | 8 tests - Tab rendering, tab switching, ARIA attributes           |
| `apps/web/__tests__/HistoryTab.test.tsx`       | 7 tests - History display, infinite scroll, empty state           |
| `apps/web/__tests__/StatsTab.test.tsx`         | 7 tests - Stats display, progress bars, per-page stats            |
| `apps/web/__tests__/TranslateFilters.test.tsx` | 10 tests - Filter rendering, book/language loading, status filter |

## Test Results

- Backend: **88 tests passed** (all existing + 17 new)
- Frontend: **57 tests passed** (all existing + 32 new)
- TypeScript: **Clean** (`pnpm check-types` passes)
- ESLint: Only pre-existing warnings from `PageEditor.tsx` (unused eslint-disable + unexpected any)

## Known Issues / Notes

- Pre-existing ESLint warnings in `apps/web/components/PageEditor.tsx` (2 warnings) are not related to this feature
- Redis caching gracefully falls back to no-cache if Redis is unavailable
- Draft auto-save uses 5-second debounce to avoid excessive API calls
- Translation history uses cursor-based pagination for stable infinite scroll
- `translation_drafts` collection has 24h TTL index for automatic cleanup
