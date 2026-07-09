# Translation Page Redesign — Technical Architecture

**Date:** 2026-07-06 12:00
**Author:** Architecture Agent
**Epic Reference:** Epic 4 — Translation
**Related BA:** `specs/business-analysis/20260706-1200-translation-page-redesign.md`

---

## 1. Scope

Transform the minimal `/translate` page (single "Next Section" button) into a full-featured translation console with tabs for translating, viewing history, and monitoring statistics. Covers 6 user stories: US-TR-1 through US-TR-6.

---

## 2. Key Technical Decisions

| Decision                | Choice                                                                       | Rationale                                                                                                      |
| ----------------------- | ---------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Page layout             | **Tab bar** (Translate \| History \| Stats)                                  | Clean separation of concerns; translators don't see Stats tab; simple to implement with `?tab=` query param    |
| Stats endpoint design   | **Single aggregated endpoint** per concern (`/stats`, `/translators/stats`)  | Reduces round trips; each aggregation is independent and cached separately                                     |
| Caching strategy        | **Redis with 30s TTL** for stats; React Query `staleTime: 30000` on frontend | Stats are expensive aggregation queries; 30s cache avoids hammering MongoDB while staying "near real-time"     |
| Auto-load first section | **useEffect on mount** calls `/api/sections/next`                            | No SSR needed for this; translator's view is fully client-side                                                 |
| Frontend data fetching  | **React Query (TanStack Query)**                                             | Provides caching, background refetch, optimistic updates, and cleanup; better than raw SWR for this complexity |
| History pagination      | **Cursor-based** (last `createdAt` as cursor)                                | Avoids skip/limit performance issues on large datasets; natural fit for infinite scroll                        |
| Draft auto-save         | **Backend API with 24h TTL collection** + localStorage fallback              | Server-side drafts survive device switches; localStorage is immediate fallback if API is slow                  |
| Filter state            | **URL query params**                                                         | Shareable links, survives reload, independent between tabs via `?tab=history&lang=si&page=5`                   |

---

## 3. API Contract

### 3.1 GET /api/sections/next (Updated)

Adds filter parameters to the existing endpoint.

**Query Parameters:**

| Param      | Type   | Required | Notes                                        |
| ---------- | ------ | -------- | -------------------------------------------- |
| `bookId`   | string | No       | Scope to a specific book (previously global) |
| `language` | string | No       | Filter by target language                    |
| `page`     | int    | No       | Filter by page number                        |
| `status`   | string | No       | `pending`, `translated`, `approved`          |

**Response (200):** `NextSectionResponse` (unchanged schema)

**Response (404):** `{ "detail": "No sections available" }`

**Behavior Changes:**

- When `bookId` is provided, only sections from that book are considered
- Language filter matches sections whose parent book has that language in `translateLanguages`
- Page filter matches `Page.pageNumber`
- Status filter: `pending` = no translation yet, `translated` = has unapproved translation, `approved` = has approved translation
- Filters compose (AND logic)

---

### 3.2 GET /api/books/{bookId}/stats

Returns book-level translation progress. Editor-only.

**Response (200):**

```json
{
  "totalSections": 120,
  "translatedSections": 45,
  "pendingSections": 12,
  "inProgressSections": 8,
  "translationPercent": 37.5,
  "byLanguage": {
    "si": { "total": 120, "translated": 45, "percent": 37.5 },
    "ta": { "total": 120, "translated": 20, "percent": 16.7 }
  },
  "byPage": [
    { "pageNumber": 1, "total": 5, "translated": 5, "percent": 100.0 },
    { "pageNumber": 2, "total": 4, "translated": 2, "percent": 50.0 },
    { "pageNumber": 3, "total": 6, "translated": 0, "percent": 0.0 }
  ]
}
```

**Pydantic Schema:**

```python
class LanguageStats(BaseModel):
    total: int
    translated: int
    percent: float

class PageStats(BaseModel):
    pageNumber: int
    total: int
    translated: int
    percent: float

class TranslationStatsResponse(BaseModel):
    totalSections: int
    translatedSections: int
    pendingSections: int
    inProgressSections: int
    translationPercent: float
    byLanguage: dict[str, LanguageStats]
    byPage: list[PageStats]
```

**Backend Aggregation Pipeline (MongoDB):**

```python
# 1. Count total sections for this book
total_pipeline = [
    {"$lookup": {"from": "pages", "localField": "page.id", "foreignField": "_id", "as": "page"}},
    {"$unwind": "$page"},
    {"$match": {"page.book.id": book_id}},
    {"$count": "total"}
]

# 2. Aggregation: sections with approved translations
stats_pipeline = [
    {"$lookup": {"from": "pages", "localField": "page.id", "foreignField": "_id", "as": "page"}},
    {"$unwind": "$page"},
    {"$match": {"page.book.id": book_id}},
    {"$lookup": {
        "from": "translations",
        "let": {"section_id": {"$toString": "$_id"}},
        "pipeline": [
            {"$match": {"$expr": {"$eq": ["$section.id", "$$section_id"]}}},
        ],
        "as": "translations"
    }},
    {"$addFields": {
        "hasApproved": {"$anyElementTrue": {
            "$map": {"input": "$translations", "as": "t", "in": "$$t.isApproved"}
        }},
        "hasAnyTranslation": {"$gt": [{"$size": "$translations"}, 0]}
    }},
    {"$group": {
        "_id": None,
        "total": {"$sum": 1},
        "translated": {"$sum": {"$cond": ["$hasApproved", 1, 0]}},
        "inProgress": {"$sum": {"$cond": [{"$and": ["$hasAnyTranslation", {"$not": "$hasApproved"}]}, 1, 0]}}
    }}
]
```

**Caching:**

- Redis key: `stats:book:{bookId}`
- TTL: 30 seconds
- Cache invalidated on: translation submit, approve, reject

---

### 3.3 GET /api/books/{bookId}/translators/stats

Returns per-translator performance metrics for a book. Editor-only.

**Response (200):**

```json
[
  {
    "userId": "507f1f77bcf86cd799439011",
    "userName": "Kamal Perera",
    "totalAssigned": 30,
    "approvedCount": 25,
    "rejectedCount": 3,
    "pendingCount": 2,
    "approvalRate": 89.3,
    "avgTurnaroundHours": 4.2,
    "lastActiveAt": "2026-07-05T14:30:00Z"
  }
]
```

**Pydantic Schema:**

```python
class TranslatorStatsResponse(BaseModel):
    userId: str
    userName: str
    totalAssigned: int
    approvedCount: int
    rejectedCount: int
    pendingCount: int
    approvalRate: float
    avgTurnaroundHours: float | None = None
    lastActiveAt: str | None = None
```

**Backend Logic:**

- Group translations by `translatorId` where section belongs to the book
- Join with `users` collection for `userName`
- `approvalRate = approved / (approved + rejected) * 100` (null if both are 0)
- `avgTurnaroundHours = avg(translation.createdAt - section.createdAt)` across approved translations
- `lastActiveAt = max(translation.createdAt)` for that translator

**Caching:**

- Redis key: `translators:stats:book:{bookId}`
- TTL: 30 seconds
- Cache invalidated on: translation submit, approve, reject

---

### 3.4 GET /api/translations/history

Returns paginated translation history. Translators see own only; editors see all.

**Query Parameters:**

| Param          | Type   | Required | Notes                                       |
| -------------- | ------ | -------- | ------------------------------------------- |
| `bookId`       | string | Yes      | Scope to book                               |
| `translatorId` | string | No       | Filter by translator (editors only)         |
| `language`     | string | No       | Filter by target language                   |
| `page`         | int    | No       | Filter by page number                       |
| `status`       | string | No       | `submitted`, `approved`, `rejected`         |
| `cursor`       | string | No       | ISO timestamp of last item (for pagination) |
| `limit`        | int    | No       | Page size, default 20, max 50               |

**Response (200):**

```json
{
  "items": [
    {
      "translationId": "507f1f77bcf86cd799439022",
      "sectionId": "507f1f77bcf86cd799439015",
      "pageNumber": 3,
      "sectionOrder": 2,
      "translatorId": "507f1f77bcf86cd799439011",
      "translatorName": "Kamal Perera",
      "translatedText": "මාතාව සියලු දේවතාවුන්ගේ...",
      "action": "APPROVED",
      "performedBy": "507f1f77bcf86cd799439012",
      "performedByName": "Nimal Editor",
      "createdAt": "2026-07-05T14:30:00Z"
    }
  ],
  "nextCursor": "2026-07-04T10:00:00Z",
  "hasMore": true
}
```

**Pydantic Schema:**

```python
class TranslationHistoryItem(BaseModel):
    translationId: str
    sectionId: str
    pageNumber: int
    sectionOrder: int
    translatorId: str
    translatorName: str
    translatedText: str
    action: str  # SUBMITTED, APPROVED, REJECTED
    performedBy: str | None = None
    performedByName: str | None = None
    createdAt: datetime

class TranslationHistoryResponse(BaseModel):
    items: list[TranslationHistoryItem]
    nextCursor: str | None = None
    hasMore: bool
```

**Backend Query Pattern:**

```python
query = {"section.bookId": book_id}  # resolved via section → page → book join

if translator_id:
    query["translator.id"] = translator_id
if status:
    if status == "approved":
        query["isApproved"] = True
    elif status == "rejected":
        query["isApproved"] = False
    # "submitted" = translations not yet approved/rejected

if cursor:
    query["createdAt"] = {"$lt": datetime.fromisoformat(cursor)}

cursor = db.translations.find(query).sort("createdAt", -1).limit(limit + 1)
```

---

### 3.5 POST /api/translations/draft

Upserts a translation draft (auto-save).

**Request Body:**

```json
{
  "sectionId": "507f1f77bcf86cd799439015",
  "translatedText": "මාතාව සියලු දේවතාවුන්ගේ..."
}
```

**Response (200):**

```json
{
  "draftId": "507f1f77bcf86cd799439030",
  "updatedAt": "2026-07-06T12:00:00Z"
}
```

**Pydantic Schema:**

```python
class DraftCreate(BaseModel):
    sectionId: str
    translatedText: str

class DraftResponse(BaseModel):
    draftId: str
    updatedAt: datetime
```

**Backend:**

- Upsert on `{ sectionId: 1, translatorId: 1 }` compound index
- TTL index on `createdAt` (24 hours) auto-expires old drafts
- Returns existing draft ID if upserted

---

### 3.6 GET /api/translations/draft

Fetches a translator's draft for a section.

**Query Parameters:**

| Param       | Type   | Required |
| ----------- | ------ | -------- |
| `sectionId` | string | Yes      |

**Response (200):**

```json
{
  "draftId": "507f1f77bcf86cd799439030",
  "translatedText": "මාතාව සියලු දේවතාවුන්ගේ...",
  "updatedAt": "2026-07-06T12:00:00Z"
}
```

**Response (404):** `{ "detail": "No draft found" }`

---

### 3.7 DELETE /api/translations/draft/{draftId}

Deletes a draft after successful translation submission.

**Response (200):** `{ "status": "deleted" }`

---

## 4. Data Flow Diagrams

### 4.1 Translation Page Mount (Auto-Load)

```
┌──────────────┐     GET /api/sections/next?bookId=X     ┌──────────┐
│  Translator  │ ───────────────────────────────────────→  │ FastAPI  │
│  opens       │ ←───────────────────────────────────────  │          │
│  /translate  │     NextSectionResponse                   └──────────┘
└──────────────┘                                                │
        │                                                        │
        │  GET /api/translations/draft?sectionId=Y              │
        │ ────────────────────────────────────────────────────→  │
        │ ←────────────────────────────────────────────────────  │
        │     DraftResponse (or 404)                             │
        │                                                        │
        │  Renders:                                              │
        │  ┌─ SectionImage ─┐  ┌─ SourceTextPanel ─┐           │
        │  │  (cropped img)  │  │  (originalText)   │           │
        │  └────────────────┘  └───────────────────┘           │
        │  ┌─ TranslationEditor ──────────────────┐             │
        │  │  textarea (prefilled from draft)      │             │
        │  │  auto-saves every 5s → POST /draft    │             │
        │  └──────────────────────────────────────┘             │
```

### 4.2 Stats Tab Data Flow

```
┌──────────────┐     GET /api/books/{id}/stats              ┌──────────┐
│  Editor      │ ─────────────────────────────────────────→  │ FastAPI  │
│  clicks      │ ←─────────────────────────────────────────  │          │
│  Stats tab   │     TranslationStatsResponse                └──────────┘
└──────────────┘                                                │
        │                                                        │
        │  GET /api/books/{id}/translators/stats                │
        │ ────────────────────────────────────────────────────→  │
        │ ←────────────────────────────────────────────────────  │
        │     TranslatorStatsResponse[]                          │
        │                                                        │
        │  React Query refetches every 30s (staleTime)          │
        │  Redis cache on backend (30s TTL)                      │
        │                                                        │
        │  Renders:                                              │
        │  ┌─ TranslationStatsCard ──────────┐                  │
        │  │  Progress bar: ████████░░ 37.5%  │                  │
        │  │  Approved: 45 | Pending: 12      │                  │
        │  │  In Progress: 8 | Total: 120     │                  │
        │  └─────────────────────────────────┘                  │
        │  ┌─ PerPageBreakdown ──────────────┐                  │
        │  │  Page 1: ██████ (100%)           │                  │
        │  │  Page 2: ███   (50%)             │                  │
        │  │  Page 3: ░     (0%)              │                  │
        │  └─────────────────────────────────┘                  │
        │  ┌─ TranslatorStatsTable ──────────┐                  │
        │  │  Name    | Approved | Rate       │                  │
        │  │  Kamal   | 25       | 89.3%      │                  │
        │  │  Priya   | 20       | 83.3%      │                  │
        │  └─────────────────────────────────┘                  │
```

### 4.3 History Tab Data Flow

```
┌──────────────┐     GET /api/translations/history           ┌──────────┐
│  User        │ ─────────────────────────────────────────→  │ FastAPI  │
│  clicks      │ ←─────────────────────────────────────────  │          │
│  History tab │     { items: [...], nextCursor, hasMore }    └──────────┘
└──────────────┘                                                │
        │                                                        │
        │  Scroll to bottom → fetch next page using cursor      │
        │ ────────────────────────────────────────────────────→  │
        │ ←────────────────────────────────────────────────────  │
        │     Append to list                                     │
        │                                                        │
        │  Renders:                                              │
        │  ┌─ HistoryItem ──────────────────────────┐           │
        │  │  [thumb] Page 3, Sec 2                  │           │
        │  │  "මාතාව සියලු දේවතාවුන්ගේ..." (80 chars) │           │
        │  │  ✅ APPROVED — Jul 5, 2:30 PM           │           │
        │  └────────────────────────────────────────┘           │
        │  ┌─ HistoryItem ──────────────────────────┐           │
        │  │  [thumb] Page 1, Sec 4                  │           │
        │  │  "සිංහල භාෂාවෙන්..."                     │           │
        │  │  ⏳ PENDING — Jul 6, 10:00 AM           │           │
        │  └────────────────────────────────────────┘           │
        │  ── Loading more... ──                                 │
```

---

## 5. Frontend Component Architecture

### 5.1 Route Structure

```
/translate                          → TranslateLayout (client component)
  ?tab=translate (default)          → TranslateTab
  ?tab=history                      → HistoryTab
  ?tab=stats                        → StatsTab (editors only)
  &bookId=X&lang=si&page=5&status=pending  → filters (persisted in URL)
/translate?section={sectionId}      → TranslateTab with pre-selected section
```

### 5.2 Component Tree

```
TranslatePage (app/translate/page.tsx) [Client Component]
│
├── TranslateHeader
│   ├── BackNavigation (→ /dashboard or /books)
│   ├── BookSelector (dropdown if translator has multiple books)
│   └── UserInfo (avatar, name)
│
├── TranslateFilters
│   ├── LanguageDropdown (from book.translateLanguages, hidden if single lang)
│   ├── PageFilter (input or dropdown of page numbers)
│   ├── StatusFilter (ALL | PENDING | APPROVED | REJECTED)
│   └── ClearFiltersButton
│
├── TabBar
│   ├── Tab: "Translate" (default)
│   ├── Tab: "History"
│   └── Tab: "Stats" (editors/super-admin only)
│
├── [Tab Content]
│   │
│   ├── TranslateTab
│   │   ├── SectionImageDisplay
│   │   │   ├── CroppedSectionImage (zoomable)
│   │   │   └── ZoomControls
│   │   ├── SourceTextPanel
│   │   │   ├── OriginalText (read-only, labeled "Source Text")
│   │   │   └── EditOriginalTextLink (editors only → /books/{id}/pages/{num})
│   │   ├── TranslationEditor
│   │   │   ├── AutoTranslationDisplay (prefilled, editable)
│   │   │   ├── TranslatedTextArea
│   │   │   ├── ExactLetterInput (optional)
│   │   │   ├── DraftSaveIndicator ("Draft saved ✓")
│   │   │   └── SubmitButton
│   │   ├── PreviousSubmission (if translator has existing sub)
│   │   ├── ApprovedTranslation (if exists)
│   │   ├── PageContextNav (prev/next page thumbnails)
│   │   ├── SkipButton → calls fetchNextSection
│   │   └── CommentSection
│   │
│   ├── HistoryTab
│   │   ├── HistoryFilters (independent state from TranslateTab)
│   │   ├── HistoryList
│   │   │   └── HistoryItem[] (clickable → /translate?section={id})
│   │   └── InfiniteScrollIndicator / EmptyState
│   │
│   └── StatsTab (editor-only)
│       ├── TranslationStatsCard
│       │   ├── ProgressBar (SVG arc or bar)
│       │   └── StatNumbers (approved, pending, in-progress, total)
│       ├── PerPageBreakdown
│       │   └── PageGrid (color-coded cells)
│       ├── PerLanguageBreakdown (if multi-language)
│       │   └── LanguageCards
│       └── TranslatorStatsTable
│           ├── SortableHeader
│           └── TranslatorRow[] (expandable → last 10 submissions)
│
└── LoadingStates / ErrorBoundaries
```

### 5.3 State Management

```typescript
// URL params (read via useSearchParams, written via useRouter)
// ?tab=translate&bookId=X&lang=si&page=5&status=pending

// React Query hooks
useQuery(["nextSection", bookId, filters], fetchNextSection)
useQuery(["translationHistory", bookId, historyFilters, cursor], fetchHistory)
useQuery(["translationStats", bookId], fetchStats, { staleTime: 30000 })
useQuery(["translatorStats", bookId], fetchTranslatorStats, { staleTime: 30000 })
useQuery(["draft", sectionId], fetchDraft)

useMutation(submitTranslation, {
  onSuccess: () => {
    queryClient.invalidateQueries(["nextSection"])
    queryClient.invalidateQueries(["translationHistory"])
    queryClient.invalidateQueries(["translationStats"])
    queryClient.invalidateQueries(["draft", sectionId])
  },
})

useMutation(saveDraft)
useMutation(deleteDraft)

// Local component state
const [translatedText, setTranslatedText] = useState(initialText)
const [exactLetter, setExactLetter] = useState("")
const [isDirty, setIsDirty] = useState(false) // for unsaved changes warning
const [zoom, setZoom] = useState(100)
```

### 5.4 Auto-Save Draft Implementation

```typescript
// Debounced auto-save (5 second inactivity)
const debouncedSaveDraft = useMemo(
  () =>
    debounce((text: string) => {
      if (text.trim() && sectionId) {
        saveDraftMutation.mutate({ sectionId, translatedText: text })
      }
    }, 5000),
  [sectionId],
)

// Effect to save on text change
useEffect(() => {
  if (isDirty) {
    debouncedSaveDraft(translatedText)
  }
  return () => debouncedSaveDraft.cancel()
}, [translatedText, isDirty])

// Before unload warning
useEffect(() => {
  const handler = (e: BeforeUnloadEvent) => {
    if (isDirty) {
      e.preventDefault()
      e.returnValue = ""
    }
  }
  window.addEventListener("beforeunload", handler)
  return () => window.removeEventListener("beforeunload", handler)
}, [isDirty])
```

---

## 6. Caching Strategy

### 6.1 Backend (Redis)

| Key Pattern                        | TTL  | Invalidated By                      | Notes                                                   |
| ---------------------------------- | ---- | ----------------------------------- | ------------------------------------------------------- |
| `stats:book:{bookId}`              | 30s  | Translation submit, approve, reject | Expensive aggregation                                   |
| `translators:stats:book:{bookId}`  | 30s  | Translation submit, approve, reject | Per-translator aggregation                              |
| `draft:{sectionId}:{translatorId}` | None | Explicit DELETE on submit           | Write-through, no TTL needed (TTL index handles expiry) |

### 6.2 Frontend (React Query)

| Query Key                         | staleTime | cacheTime | Refetch Strategy                     |
| --------------------------------- | --------- | --------- | ------------------------------------ |
| `['nextSection', bookId, filters] | 0         | 5min      | Refetch on tab focus, manual skip    |
| `['translationHistory', ...]      | 30s       | 10min     | Refetch on tab focus                 |
| `['translationStats', bookId]     | 30s       | 5min      | Poll every 30s, refetch on tab focus |
| `['translatorStats', bookId]      | 30s       | 5min      | Poll every 30s                       |
| `['draft', sectionId]             | 0         | 5min      | Refetch on section change            |

---

## 7. Database Query Patterns

### 7.1 Stats Aggregation (Simplified)

```python
async def get_book_stats(db: AsyncIOMotorDatabase, book_id: str) -> dict:
    # Check Redis cache first
    cache_key = f"stats:book:{book_id}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # Aggregate sections with their translation status
    pipeline = [
        # Join sections → pages to scope to book
        {"$lookup": {"from": "pages", "localField": "page.id", "foreignField": "_id", "as": "page"}},
        {"$unwind": "$page"},
        {"$match": {"page.book.id": book_id}},

        # Left-join with translations
        {"$lookup": {
            "from": "translations",
            "let": {"sid": {"$toString": "$_id"}},
            "pipeline": [
                {"$match": {"$expr": {"$eq": ["$section.id", "$$sid"]}}},
            ],
            "as": "translations"
        }},

        # Classify each section
        {"$addFields": {
            "status": {
                "$cond": [
                    {"$anyElementTrue": {"$map": {"input": "$translations", "as": "t", "in": "$$t.isApproved"}}},
                    "approved",
                    {"$cond": [
                        {"$gt": [{"$size": "$translations"}, 0]},
                        "in_progress",
                        "pending"
                    ]}
                ]
            }
        }},

        # Group and count
        {"$group": {
            "_id": None,
            "total": {"$sum": 1},
            "translated": {"$sum": {"$cond": [{"$eq": ["$status", "approved"]}, 1, 0]}},
            "inProgress": {"$sum": {"$cond": [{"$eq": ["$status", "in_progress"]}, 1, 0]}},
            "pending": {"$sum": {"$cond": [{"$eq": ["$status", "pending"]}, 1, 0]}}
        }}
    ]

    result = await db.sections.aggregate(pipeline).to_list(1)
    # ... compute byLanguage, byPage breakdowns

    # Cache result
    await redis.setex(cache_key, 30, json.dumps(stats))
    return stats
```

### 7.2 History Query (Cursor-Based)

```python
async def get_translation_history(
    db: AsyncIOMotorDatabase,
    book_id: str,
    translator_id: str | None = None,
    language: str | None = None,
    page_num: int | None = None,
    status: str | None = None,
    cursor: str | None = None,
    limit: int = 20,
) -> list[dict]:
    # Build match stage
    match = {}
    if translator_id:
        match["translator.id"] = translator_id
    if status == "approved":
        match["isApproved"] = True
    elif status == "rejected":
        match["isApproved"] = False
    if cursor:
        match["createdAt"] = {"$lt": datetime.fromisoformat(cursor)}

    pipeline = [
        {"$match": match},
        # Join to sections → pages to scope to book and filter by page/language
        {"$lookup": {"from": "sections", "localField": "section.id", "foreignField": "_id", "as": "section"}},
        {"$unwind": "$section"},
        {"$lookup": {"from": "pages", "localField": "section.page.id", "foreignField": "_id", "as": "page"}},
        {"$unwind": "$page"},
        {"$match": {"page.book.id": book_id}},
        # Apply page filter
        *([{"$match": {"page.pageNumber": page_num}}] if page_num else []),
        # Join translator name
        {"$lookup": {"from": "users", "localField": "translator.id", "foreignField": "_id", "as": "translatorUser"}},
        {"$unwind": {"path": "$translatorUser", "preserveNullAndEmptyArrays": True}},
        # Sort and limit
        {"$sort": {"createdAt": -1}},
        {"$limit": limit + 1},  # fetch one extra to determine hasMore
    ]

    cursor = db.translations.aggregate(pipeline)
    items = await cursor.to_list(length=limit + 1)
    has_more = len(items) > limit
    items = items[:limit]

    return {
        "items": [format_history_item(item) for item in items],
        "nextCursor": str(items[-1]["createdAt"]) if items and has_more else None,
        "hasMore": has_more,
    }
```

---

## 8. New Backend Files

| File                              | Purpose                                                                             |
| --------------------------------- | ----------------------------------------------------------------------------------- |
| `app/api/books_stats.py`          | `GET /api/books/{id}/stats` and `GET /api/books/{id}/translators/stats`             |
| `app/api/translations_history.py` | `GET /api/translations/history`                                                     |
| `app/api/translations_draft.py`   | `POST/GET/DELETE /api/translations/draft`                                           |
| `app/schemas/stats.py`            | `TranslationStatsResponse`, `LanguageStats`, `PageStats`, `TranslatorStatsResponse` |
| `app/schemas/history.py`          | `TranslationHistoryItem`, `TranslationHistoryResponse`                              |
| `app/schemas/draft.py`            | `DraftCreate`, `DraftResponse`                                                      |

### Router Registration

In `app/main.py`:

```python
from app.api.books_stats import router as books_stats_router
from app.api.translations_history import router as translations_history_router
from app.api.translations_draft import router as translations_draft_router

app.include_router(books_stats_router)
app.include_router(translations_history_router)
app.include_router(translations_draft_router)
```

---

## 9. New Frontend Files

| File                                              | Purpose                                            |
| ------------------------------------------------- | -------------------------------------------------- |
| `app/translate/page.tsx`                          | Rewrite: tabbed layout with filters, auto-load     |
| `app/translate/TranslateTab.tsx`                  | Translate tab content (section editor)             |
| `app/translate/HistoryTab.tsx`                    | History tab content (infinite scroll list)         |
| `app/translate/StatsTab.tsx`                      | Stats tab content (editor-only dashboard)          |
| `app/translate/TranslateFilters.tsx`              | Filter bar component                               |
| `app/translate/components/SourceTextPanel.tsx`    | Original text display                              |
| `app/translate/components/DraftSaveIndicator.tsx` | "Draft saved" feedback                             |
| `app/translate/components/HistoryItem.tsx`        | Single history row                                 |
| `app/translate/components/TranslatorStatsRow.tsx` | Expandable translator stats row                    |
| `lib/api/translations.ts`                         | API client functions for all translation endpoints |
| `hooks/useTranslationDraft.ts`                    | Custom hook for auto-save draft logic              |
| `hooks/useTranslationFilters.ts`                  | Custom hook for URL-synced filter state            |

---

## 10. Implementation Order

| Phase       | Stories | Backend                                                                    | Frontend                                                                 | Effort   |
| ----------- | ------- | -------------------------------------------------------------------------- | ------------------------------------------------------------------------ | -------- |
| **Phase 1** | US-TR-5 | None (existing data)                                                       | Rewrite `translate/page.tsx` with side-by-side layout, source text panel | 1 day    |
| **Phase 2** | US-TR-1 | `translations_history.py`, `schemas/history.py`                            | `HistoryTab.tsx`, `HistoryItem.tsx`, infinite scroll                     | 1.5 days |
| **Phase 3** | US-TR-4 | Update `sections.py` (filter params), update `translations_history.py`     | `TranslateFilters.tsx`, URL param sync                                   | 1 day    |
| **Phase 4** | US-TR-2 | `books_stats.py`, `schemas/stats.py`, Redis caching                        | `StatsTab.tsx`, `TranslationStatsCard`, `PerPageBreakdown`               | 1.5 days |
| **Phase 5** | US-TR-3 | Extend `books_stats.py`, `TranslatorStatsResponse`                         | `TranslatorStatsTable.tsx`                                               | 1 day    |
| **Phase 6** | US-TR-6 | `translations_draft.py`, `schemas/draft.py`, `TranslationDraft` collection | `useTranslationDraft.ts`, `DraftSaveIndicator.tsx`                       | 1 day    |

**Total estimated effort: ~7 days**

---

## 11. Testing Strategy

### Backend Tests

| Test File                            | Covers                                                |
| ------------------------------------ | ----------------------------------------------------- |
| `tests/test_books_stats.py`          | Stats aggregation, caching, cache invalidation        |
| `tests/test_translator_stats.py`     | Per-translator metrics, approval rate calculation     |
| `tests/test_translations_history.py` | History query, pagination, filters, role-based access |
| `tests/test_translations_draft.py`   | Draft CRUD, TTL expiry, upsert semantics              |

### Frontend Tests

| Test File                               | Covers                                          |
| --------------------------------------- | ----------------------------------------------- |
| `__tests__/TranslatePage.test.tsx`      | Tab switching, filter state, auto-load          |
| `__tests__/HistoryTab.test.tsx`         | History rendering, infinite scroll, empty state |
| `__tests__/StatsTab.test.tsx`           | Stats card, page breakdown, translator table    |
| `__tests__/TranslateFilters.test.tsx`   | Filter changes, URL sync, clear filters         |
| `__tests__/useTranslationDraft.test.ts` | Auto-save debounce, draft fetch, beforeunload   |

---

## 12. Migration / Rollout Notes

- **No migration needed**: All new endpoints are additive. Existing endpoints remain unchanged.
- **New MongoDB collection**: `translation_drafts` with TTL index — created automatically on first insert or via `db/indexes.py`.
- **Redis cache keys**: New keys only; no conflict with existing keys.
- **Feature flag**: Consider wrapping Stats tab visibility in a feature flag (`ENABLE_TRANSLATION_STATS`) for gradual rollout.
- **Backward compatibility**: The existing `/translate` page behavior is preserved; the redesign replaces the UI but keeps the same API calls.
