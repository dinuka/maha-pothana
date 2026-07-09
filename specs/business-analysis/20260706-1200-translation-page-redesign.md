# Translation Page Redesign — User Stories

**Date:** 2026-07-06 12:00
**Author:** Business Analysis Agent
**Epic Reference:** Epic 4 — Translation, Epic 5 — Book Organization & Publishing

---

## Context

The current translation UI (`/translate` and `/translate/[sectionId]`) is minimal: a translator clicks "Next" to get a random section, translates it, and submits. There is no translation history, no progress visibility, no performance tracking, and no way for translators to see their own past work. This redesign adds a full-featured translation console with history, statistics, and filtering.

---

## User Stories

### US-TR-1: View Translation History

**As a** translator
**I want to** see a chronological list of my past translations
**So that** I can review what I've submitted, track approved/rejected work, and revisit sections I've already translated.

**Acceptance Criteria:**

- The `/translate` page shows a "History" tab alongside the "Translate" tab
- History list displays each past translation with: section thumbnail, page number, translated text snippet (first 80 chars), status badge (APPROVED / REJECTED / PENDING), and timestamp
- Translations are sorted by most recent first
- Clicking a history item navigates to `/translate/[sectionId]` with the translation pre-loaded
- Translators see only their own translations; editors see all translations for the book
- Pagination or infinite scroll loads more history entries as the user scrolls
- Empty state shows "No translations yet — start translating!" with a link to the translate tab
- History entries reflect real-time status changes (e.g., when an editor approves a translation, the badge updates)

**API:**

- `GET /api/translations/history?bookId={bookId}&translatorId={translatorId}&page={page}&limit={20}`
- Returns `TranslationHistoryItem[]` (defined in `data-model.md`)

**Backend:**

- Query `Translation` collection joined with `Section` and `User` collections
- Filter by `translatorId` (for translators) or all (for editors)
- Sort by `createdAt` descending
- Support pagination via `skip`/`limit`

---

### US-TR-2: View Book Translation Statistics Dashboard

**As an** editor
**I want to** see a statistics dashboard for a book's translation progress
**So that** I can understand overall progress, identify bottlenecks, and make informed decisions about translator assignments.

**Acceptance Criteria:**

- The `/books/[bookId]` page shows a "Translation Stats" section in the console view
- Stats include: total sections, translated (approved), pending review, not started, and translation percentage
- A progress bar visually represents translation completion (0%–100%)
- A per-page breakdown shows translation status per page (completed pages in green, partial in yellow, untouched in gray)
- Stats update in real-time (poll every 30s or use WebSocket)
- Editors can see per-language stats if the book has multiple target languages
- The stats section collapses/expands to save screen space
- Translators do NOT see this dashboard (stats are editor-only)

**API:**

- `GET /api/books/{bookId}/stats`
- Returns `TranslationStats` (defined in `data-model.md`)

**Backend:**

- Aggregate `Translation` collection grouped by `sectionId` with `isApproved = true`
- Cross-reference with `Section` collection to count total sections
- Group by `translateLanguages` for per-language breakdown
- Group by `Page.pageNumber` for per-page breakdown
- Cache stats with 30s TTL to avoid expensive aggregation on every request

---

### US-TR-3: View Translator Performance Stats

**As an** editor
**I want to** see performance metrics for each translator assigned to a book
**So that** I can identify top performers, spot struggling translators, and rebalance workloads.

**Acceptance Criteria:**

- The book settings page shows a "Translators" tab with performance metrics per translator
- Metrics displayed per translator: total sections worked on, approved count, rejected count, pending count, approval rate (%), average turnaround time, last active date
- Translators are sorted by approval rate (descending) by default; sortable by any column
- Clicking a translator's name expands to show their recent translation activity (last 10 submissions)
- Editors can see stats for all translators; translators cannot see other translators' stats
- Average turnaround time is calculated as the time between section availability and translation submission
- If a translator has zero submissions, display "No activity" instead of N/A or 0%
- Stats are scoped to the selected book (not global across all books)

**API:**

- `GET /api/books/{bookId}/translators/stats`
- Returns `TranslatorStats[]` (defined in `data-model.md`)

**Backend:**

- Query `Translation` collection grouped by `translatorId`
- Join with `User` collection for `userName`
- Calculate `approvalRate = approved / (approved + rejected) * 100`
- Calculate `avgTurnaroundHours` from `Translation.createdAt` minus section creation time
- Sort by `approvalRate` descending

---

### US-TR-4: Filter Translations by Language and Page

**As a** translator or editor
**I want to** filter the translation queue and history by target language and page number
**So that** I can focus on specific work — e.g., translate only Sinhala sections, or review all translations for page 5.

**Acceptance Criteria:**

- The `/translate` page shows filter controls above the section queue: language dropdown, page number input/dropdown, and status filter (ALL, PENDING, APPROVED, REJECTED)
- Filters apply immediately on selection (no "Apply" button needed)
- The "Next" button fetches the next random untranslated section matching the active filters
- History tab respects the same filters
- Filters are persisted in URL query params (`?lang=si&page=5&status=pending`) so the view is shareable and survives page reload
- Clear filters button resets all filters to defaults
- If the book has only one target language, the language filter is hidden
- Filter state is independent between the Translate and History tabs

**API:**

- `GET /api/sections/next?bookId={bookId}&language={lang}&page={pageNum}&status={status}`
- `GET /api/translations/history?bookId={bookId}&translatorId={translatorId}&language={lang}&page={pageNum}&status={status}&page={page}&limit={20}`

**Backend:**

- `sections/next` applies language/page filters before selecting a random section
- `translations/history` applies language/page/status filters via MongoDB query operators
- Language filter matches against `Translation.translatedText` target language or `Book.translateLanguages`

---

### US-TR-5: View Translation Context with Original Text Side-by-Side

**As a** translator
**I want to** see the original (source language) text alongside my translation input
**So that** I can produce more accurate translations by referring to the source content.

**Acceptance Criteria:**

- The translation editor (`/translate/[sectionId]`) shows two columns: left = original section image + OCR text, right = translation input
- The original text (from `Section.originalText`) is displayed above or below the section image
- The original text is read-only and clearly labeled "Source Text"
- If `originalText` is empty or missing, display "Original text not available — use the image above" with the section image still visible
- The auto-translated text (from LibreTranslate) pre-fills the translation input as a starting point
- The translator can freely edit the pre-filled translation
- The side-by-side layout collapses to stacked on narrow viewports (mobile responsive)
- An "Edit original text" link is available for editors (navigates to the page editor)

**No API changes required** — `Section.originalText` is already returned by the existing sections API.

---

### US-TR-6: Auto-save Translation Drafts

**As a** translator
**I want to** my translation input to be auto-saved as I type
**So that** I don't lose work if I accidentally close the tab or navigate away.

**Acceptance Criteria:**

- Translation input is debounced and auto-saved every 5 seconds of inactivity
- Draft is saved to a `TranslationDraft` temporary collection (or localStorage as fallback)
- On page load, if a draft exists, it pre-fills the translation input
- A "Draft saved" indicator appears briefly after each auto-save
- When the translator clicks "Submit", the draft is deleted and a real Translation is created
- If the translator navigates away with unsaved changes (not yet auto-saved), show a confirmation dialog: "You have unsaved changes. Leave anyway?"
- Drafts expire after 24 hours (TTL index on the draft collection)
- Drafts are per-translator per-section (no collision between translators)
- If the section is already translated by this translator, the draft is not created (redirect to history)

**API (new):**

- `POST /api/translations/draft` — upsert draft `{ sectionId, translatorId, translatedText }`
- `GET /api/translations/draft?sectionId={sectionId}&translatorId={translatorId}` — fetch draft
- `DELETE /api/translations/draft/{draftId}` — delete draft after submission

**Backend:**

- New `TranslationDraft` collection with TTL index on `createdAt` (24 hours)
- Unique compound index on `{ sectionId: 1, translatorId: 1 }` for upsert semantics
- Draft is lightweight: only `sectionId`, `translatorId`, `translatedText`, `createdAt`

---

## Implementation Priority

| Priority | Story                                                           | Effort | Impact                                                  |
| -------- | --------------------------------------------------------------- | ------ | ------------------------------------------------------- |
| P0       | US-TR-5: View translation context with source text side-by-side | Small  | Critical — translators lack source text reference today |
| P0       | US-TR-1: View translation history                               | Medium | High — translators have no visibility into past work    |
| P1       | US-TR-2: Book translation statistics dashboard                  | Medium | High — editors lack progress visibility                 |
| P1       | US-TR-4: Filter translations by language and page               | Medium | High — no way to focus on specific work                 |
| P2       | US-TR-3: Translator performance stats                           | Medium | Medium — useful for editor decision-making              |
| P2       | US-TR-6: Auto-save translation drafts                           | Medium | Medium — prevents data loss, quality of life            |

---

## Key Insights

1. **Source text is already in the Section document** — `Section.originalText` is populated during OCR/detection. US-TR-5 requires only a UI layout change, no new backend work.

2. **Translation history is a simple query** — the `Translation` collection already has all the data needed. US-TR-1 needs only a new API endpoint and history UI tab.

3. **Statistics require aggregation** — US-TR-2 and US-TR-3 need MongoDB aggregation pipelines. Caching with a 30s TTL is essential to avoid expensive queries on every page load.

4. **Filtering should compose** — all filter parameters (language, page, status) should be composable via query params so they work across both the translate queue and history views.

5. **Draft auto-save can use localStorage as fallback** — if the backend draft API is not yet implemented, a localStorage-based auto-save provides immediate value with zero backend changes.

6. **These stories are independent** — each story can be implemented and shipped separately. US-TR-5 is the quickest win (pure UI), followed by US-TR-1 (simple API + UI), then the statistics and filtering stories.

---

## Related Files

- `specs/business-analysis/actors.md` — updated permissions matrix (4 new permissions)
- `specs/business-analysis/data-model.md` — updated with TranslationStats, TranslatorStats, TranslationHistoryItem, TranslationDraft entities
- `specs/business-analysis/user-stories.md` — existing user stories (Epic 4: Translation)
