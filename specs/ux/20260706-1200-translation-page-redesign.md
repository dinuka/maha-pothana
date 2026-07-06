# Translation Page Redesign — UX/Interaction Spec

**Date:** 2026-07-06 12:00
**Author:** UX Agent
**Epic Reference:** Epic 4 — Translation
**Related BA:** `specs/business-analysis/20260706-1200-translation-page-redesign.md`
**Related Architecture:** `specs/architecture/20260706-1200-translation-page-redesign.md`
**Updated UI Design:** `specs/ux/ui-design.md`

---

## 1. Overview

The translation page transforms from a single-purpose "Next Section" button into a full-featured translation console with three tabs: **Translate**, **History**, and **Stats**. Filters are URL-persisted and independent between tabs. The layout adapts from side-by-side on desktop to stacked on mobile.

---

## 2. Wireframe Layouts

### 2.1 Desktop (>1024px) — Translate Tab

```
┌───────────────────────────────────────────────────────────────────────┐
│  ← Dashboard   Book: "Gaha Ulela"                      [👤 Kamal]   │
├───────────────────────────────────────────────────────────────────────┤
│  🔍 [Language ▼ Sinhala]  [Page ▼ All]  [Status ▼ All]  [✕ Clear]  │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  [■ Translate]  [□ History]  [□ Stats]                               │
│  ─────────────                                                        │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────┬───────────────────────────────┐  │
│  │                                 │                               │  │
│  │  Section Image                  │  📄 Source Text               │  │
│  │  ┌───────────────────────────┐  │  ┌─────────────────────────┐  │  │
│  │  │                           │  │  │ "මාතාව සියලු දේවතාවුන්  │  │  │
│  │  │    [CROPPED SECTION]      │  │  │ ගේ ගුණ ගීතය මෙසේ          │  │  │
│  │  │    (from page image)      │  │  │ දැක්වේ..."                 │  │  │
│  │  │                           │  │  │                            │  │  │
│  │  │                           │  │  │ (read-only, gray bg)      │  │  │
│  │  └───────────────────────────┘  │  └─────────────────────────┘  │  │
│  │                                 │                               │  │
│  │  ┌─────┬────────┬─────┐        │  Your Translation *           │  │
│  │  │  −  │  100%  │  +  │        │  ┌─────────────────────────┐  │  │
│  │  └─────┴────────┴─────┘        │  │ මාතාවගේ සියලු දේවතාවුන්   │  │
│  │                                 │  │ ගේ ගුණ ගීතය මෙසේ          │  │
│  │  Previous Translation:          │  │ දැක්වේ..."                 │  │
│  │  ┌───────────────────────────┐  │  │                             │  │
│  │  │ "මාතාවගේ සියලු..."      │  │  │ (auto-resize textarea)     │  │
│  │  │ ✅ APPROVED               │  │  └─────────────────────────┘  │  │
│  │  │ Reviewed by Nimal Editor  │  │                               │  │
│  │  └───────────────────────────┘  │  Exact Letter (optional)      │  │
│  │                                 │  ┌─────────────────────────┐  │  │
│  │                                 │  │ මාතා → माता              │  │  │
│  │                                 │  └─────────────────────────┘  │  │
│  │                                 │                               │  │
│  │                                 │  💾 Draft saved ✓             │  │
│  │                                 │                               │  │
│  │                                 │  [Skip]  [Submit Translation] │  │
│  │                                 │                               │  │
│  └─────────────────────────────────┴───────────────────────────────┘  │
│                                                                       │
│  Page Context:  [← Prev]   Page 3 of 12 sections   [Next →]         │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### 2.2 Desktop (>1024px) — History Tab

```
┌───────────────────────────────────────────────────────────────────────┐
│  ← Dashboard   Book: "Gaha Ulela"                      [👤 Kamal]   │
├───────────────────────────────────────────────────────────────────────┤
│  🔍 [Language ▼ Sinhala]  [Page ▼ All]  [Status ▼ All]  [✕ Clear]  │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  [□ Translate]  [■ History]  [□ Stats]                               │
│                   ───────────                                         │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Translation History                    Showing: Sinhala, All pages   │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ ┌──────┐  Page 3, Section 2                                   │  │
│  │ │  📷  │  "මාතාව සියලු දේවතාවුන්ගේ ගුණ ගීතය මෙසේ දැක්වේ..." │  │
│  │ │thumb │                                                       │  │
│  │ └──────┘  ✅ APPROVED  ·  Nimal Editor  ·  Jul 5, 2:30 PM     │  │
│  ├─────────────────────────────────────────────────────────────────┤  │
│  │ ┌──────┐  Page 1, Section 4                                   │  │
│  │ │  📷  │  "සිංහල භාෂාවෙන් ලියා ඇති මෙම පාඨය..."              │  │
│  │ │thumb │                                                       │  │
│  │ └──────┘  ⏳ PENDING  ·  Jul 6, 10:00 AM                      │  │
│  ├─────────────────────────────────────────────────────────────────┤  │
│  │ ┌──────┐  Page 5, Section 1                                   │  │
│  │ │  📷  │  "පාඨකයාගේ අදහස් විශ්ලේෂණය මෙසේ..."                │  │
│  │ │thumb │                                                       │  │
│  │ └──────┘  ❌ REJECTED  ·  Nimal Editor  ·  Jul 4, 3:15 PM     │  │
│  ├─────────────────────────────────────────────────────────────────┤  │
│  │ ┌──────┐  Page 2, Section 1                                   │  │
│  │ │  📷  │  "ආරම්භක පාඨය මෙසේ දැක්වේ..."                        │  │
│  │ │thumb │                                                       │  │
│  │ └──────┘  ⏳ PENDING  ·  Jul 3, 9:15 AM                       │  │
│  ├─────────────────────────────────────────────────────────────────┤  │
│  │                    ── Loading more... ──                        │  │
│  │                    (spinner + "Loading")                        │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### 2.3 Desktop (>1024px) — Stats Tab

```
┌───────────────────────────────────────────────────────────────────────┐
│  ← Dashboard   Book: "Gaha Ulela"                      [👤 Nimal]   │
│  (Editor view)                                                       │
├───────────────────────────────────────────────────────────────────────┤
│  🔍 [Language ▼ All]  [Page ▼ All]  [Status ▼ All]  [✕ Clear]      │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  [□ Translate]  [□ History]  [■ Stats]                               │
│                                   ─────                               │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  Translation Progress                                          │  │
│  │                                                                 │  │
│  │  ████████████████████░░░░░░░░░░░░░░░░  37.5%                   │  │
│  │                                                                 │  │
│  │  ✅ Approved: 45   ⏳ Pending: 12   🔄 In Progress: 8   📊 Total: 120 │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌─ Per-Language Breakdown ────────────────────────────────────────┐  │
│  │                                                                 │  │
│  │  ┌──────────────────────────┐  ┌──────────────────────────┐    │  │
│  │  │  Sinhala (si)            │  │  Tamil (ta)              │    │  │
│  │  │  ████████████████░░░░░░  │  │  ██████░░░░░░░░░░░░░░░░  │    │  │
│  │  │  37.5%  (45/120)         │  │  16.7%  (20/120)         │    │  │
│  │  └──────────────────────────┘  └──────────────────────────┘    │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌─ Per-Page Breakdown ────────────────────────────────────────────┐  │
│  │                                                                 │  │
│  │  Page:   1     2     3     4     5     6     7     8    ...   │  │
│  │         🟢    🟡    🟢    ⬜    🟡    ⬜    ⬜    ⬜           │  │
│  │        100%   50%  100%   0%   25%   0%    0%    0%           │  │
│  │                                                                 │  │
│  │  Legend: 🟢 Complete  🟡 Partial  ⬜ Not started               │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌─ Translator Performance ────────────────────────────────────────┐  │
│  │                                                                 │  │
│  │  ┌──────────────┬──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │  │ Name     ↓   │ Assigned │ Approved │ Rejected │ Rate ↓   │ Avg Time │  │
│  │  ├──────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤  │
│  │  │ Kamal P.     │ 30       │ 25       │ 3        │ 89.3%    │ 4.2h     │  │
│  │  │ Priya S.     │ 25       │ 20       │ 4        │ 83.3%    │ 3.8h     │  │
│  │  │ Ravi M.      │ 10       │ —        │ —        │ —        │ —        │  │
│  │  └──────────────┴──────────┴──────────┴──────────┴──────────┴──────────┘  │
│  │                                                                 │  │
│  │  Click row to expand → shows last 10 submissions               │  │
│  │  ┌─────────────────────────────────────────────────────────┐    │  │
│  │  │ Kamal P. — Recent Activity                              │    │  │
│  │  │ ───────────────────────────────────────────────────────  │    │  │
│  │  │ ✅ Page 3, Sec 2  — "මාතාව..." — Jul 5, 2:30 PM       │    │  │
│  │  │ ✅ Page 1, Sec 1  — "ආරම්භක..." — Jul 4, 11:00 AM     │    │  │
│  │  │ ⏳ Page 7, Sec 3  — "අවසාන..." — Jul 3, 4:45 PM       │    │  │
│  │  └─────────────────────────────────────────────────────────┘    │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### 2.4 Mobile (<768px) — Translate Tab

```
┌───────────────────────────────┐
│  ← Dashboard   [👤 Kamal]    │
├───────────────────────────────┤
│  [▼ Filters]  (tap to expand)│
├───────────────────────────────┤
│  [Translate] [History] [Stats]│
├───────────────────────────────┤
│                               │
│  Section Image               │
│  ┌─────────────────────────┐ │
│  │                         │ │
│  │   [CROPPED SECTION]     │ │
│  │                         │ │
│  │                         │ │
│  └─────────────────────────┘ │
│  [−] 100% [+]                │
│                               │
│  📄 Source Text               │
│  ┌─────────────────────────┐ │
│  │ "මාතාව සියලු දේවතාවුන්  │ │
│  │ ගේ ගුණ ගීතය..."        │ │
│  └─────────────────────────┘ │
│                               │
│  Your Translation *           │
│  ┌─────────────────────────┐ │
│  │ මාතාවගේ සියලු දේවතාවුන් │ │
│  │ ගේ ගුණ ගීතය..."        │ │
│  │                         │ │
│  └─────────────────────────┘ │
│                               │
│  Exact Letter (optional)      │
│  ┌─────────────────────────┐ │
│  │ මාතා → माता              │ │
│  └─────────────────────────┘ │
│                               │
│  💾 Draft saved ✓             │
│                               │
│  [Skip]  [Submit Translation] │
│                               │
│  [← Prev]  Page 3/12  [Next →]│
│                               │
└───────────────────────────────┘
```

### 2.5 Mobile (<768px) — History Tab

```
┌───────────────────────────────┐
│  ← Dashboard   [👤 Kamal]    │
├───────────────────────────────┤
│  [▼ Filters]  (tap to expand)│
├───────────────────────────────┤
│  [Translate] [History] [Stats]│
├───────────────────────────────┤
│                               │
│  Translation History          │
│                               │
│  ┌─────────────────────────┐ │
│  │ 📷  Page 3, Sec 2       │ │
│  │     "මාතාව සියලු..."    │ │
│  │     ✅ APPROVED          │ │
│  │     Jul 5, 2:30 PM      │ │
│  └─────────────────────────┘ │
│                               │
│  ┌─────────────────────────┐ │
│  │ 📷  Page 1, Sec 4       │ │
│  │     "සිංහල භාෂාවෙන්..." │ │
│  │     ⏳ PENDING           │ │
│  │     Jul 6, 10:00 AM     │ │
│  └─────────────────────────┘ │
│                               │
│  ┌─────────────────────────┐ │
│  │ 📷  Page 5, Sec 1       │ │
│  │     "පාඨකයාගේ..."       │ │
│  │     ❌ REJECTED          │ │
│  │     Jul 4, 3:15 PM      │ │
│  └─────────────────────────┘ │
│                               │
│  ── Loading more... ──        │
│                               │
└───────────────────────────────┘
```

### 2.6 Mobile (<768px) — Stats Tab

```
┌───────────────────────────────┐
│  ← Dashboard   [👤 Nimal]    │
├───────────────────────────────┤
│  [▼ Filters]  (tap to expand)│
├───────────────────────────────┤
│  [Translate] [History] [Stats]│
├───────────────────────────────┤
│                               │
│  Translation Progress         │
│  ████████████░░░░░  37.5%     │
│  ✅ 45  ⏳ 12  🔄 8  📊 120  │
│                               │
│  Per-Language                 │
│  ┌─────────────────────────┐ │
│  │ Sinhala  ████████░░ 37% │ │
│  │ Tamil    ███░░░░░░░ 17% │ │
│  └─────────────────────────┘ │
│                               │
│  Per-Page                     │
│  ┌──┬──┬──┬──┬──┬──┬──┬──┐  │
│  │🟢│🟡│🟢│⬜│🟡│⬜│⬜│⬜│  │
│  │ 1│ 2│ 3│ 4│ 5│ 6│ 7│ 8│  │
│  └──┴──┴──┴──┴──┴──┴──┴──┘  │
│  (tap cell to view page)     │
│                               │
│  Translator Performance       │
│  ┌─────────────────────────┐ │
│  │ Kamal P.                │ │
│  │ 30 assigned · 89.3%     │ │
│  │ Tap to expand →          │ │
│  ├─────────────────────────┤ │
│  │ Priya S.                │ │
│  │ 25 assigned · 83.3%     │ │
│  │ Tap to expand →          │ │
│  └─────────────────────────┘ │
│                               │
└───────────────────────────────┘
```

### 2.7 Filter Drawer (Mobile)

```
┌───────────────────────────────┐
│  Filters                  [✕] │
├───────────────────────────────┤
│                               │
│  Language                      │
│  ┌─────────────────────────┐ │
│  │ Sinhala              ▼  │ │
│  └─────────────────────────┘ │
│                               │
│  Page                         │
│  ┌─────────────────────────┐ │
│  │ All pages            ▼  │ │
│  └─────────────────────────┘ │
│                               │
│  Status                       │
│  ┌─────────────────────────┐ │
│  │ All                 ▼   │ │
│  └─────────────────────────┘ │
│                               │
│  [Clear All Filters]          │
│                               │
│  [Apply Filters]              │
│                               │
└───────────────────────────────┘
```

---

## 3. Component Interaction Patterns

### 3.1 Translate Tab — Section Loading Flow

```
User opens /translate
        │
        ▼
┌─ useEffect (mount) ─────────────────────────┐
│  Read URL params: bookId, lang, page, status │
│  Build query: /api/sections/next?bookId=X    │
│                &language=si&page=5&status=   │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
        ┌─ API Response? ──┐
        │                   │
     200 OK              404 Empty
        │                   │
        ▼                   ▼
  Load section        Show "No sections
  into state          match filters"
        │
        ▼
  ┌─ Parallel fetches ──────────────────────┐
  │  GET /api/translations/draft?sectionId=Y │
  │  GET /api/sections/{id}/my-translation   │
  └──────────────────┬──────────────────────┘
                     │
                     ▼
        ┌─ Draft exists? ──┐
        │                    │
       Yes                  No
        │                    │
        ▼                    ▼
  Prefill textarea    Use autoTranslatedText
  Show "Draft saved"  as starting text
        │                    │
        └────────┬───────────┘
                 │
                 ▼
        ┌─ My translation exists? ─┐
        │                           │
       Yes (pending)              No
        │                           │
        ▼                           ▼
  Show "My previous             (no panel)
  submission" panel
  with "Edit" button
                 │
                 ▼
           READY STATE
```

### 3.2 Translate Tab — Auto-Save Draft Flow

```
User types in textarea
        │
        ▼
  setIsDirty(true)
  setTranslatedText(value)
        │
        ▼
  debouncedSaveDraft(text) ──→ 5s debounce
        │
        ▼ (after 5s inactivity)
  ┌─ text.trim() non-empty? ─┐
  │                            │
 Yes                          No
  │                            │
  ▼                            ▼
POST /api/translations/draft  (skip)
  { sectionId, translatedText }
        │
        ▼
  Show "Draft saved ✓" indicator
  (auto-dismiss after 2s)
```

### 3.3 Translate Tab — Submit Flow

```
User clicks "Submit Translation"
        │
        ▼
  Validate: translatedText.trim() non-empty
        │
     Invalid              Valid
        │                   │
        ▼                   ▼
  Show error           setSaving(true)
  "Translation              │
   required"                ▼
                     POST /api/sections/{id}/translate
                       { translatedText, exactLetterTranslation }
                            │
                       Success              Error
                            │                 │
                            ▼                 ▼
                     DELETE /api/translations/draft/{draftId}  Show error toast
                            │
                            ▼
                     Invalidate queries:
                       - nextSection
                       - translationHistory
                       - translationStats
                       - draft
                            │
                            ▼
                     setSaving(false)
                     setShowSuccess(true)
                            │
                            ▼
                     Auto-load next section
                     (useEffect triggers fetchNextSection)
```

### 3.4 History Tab — Infinite Scroll Flow

```
User clicks "History" tab
        │
        ▼
  useEffect triggers initial fetch:
  GET /api/translations/history?bookId=X&limit=20
        │
        ▼
  Render HistoryItem[] list
        │
        ▼
  User scrolls near bottom
        │
        ▼
  IntersectionObserver fires
        │
        ▼
  ┌─ hasMore? ──┐
  │              │
 Yes            No
  │              │
  ▼              ▼
Fetch next   Show "End of history"
page using   (no more items)
cursor
  │
  ▼
GET /api/translations/history?cursor={lastCreatedAt}&limit=20
  │
  ▼
Append items to list
Update cursor for next fetch
```

### 3.5 Stats Tab — Data Refresh Flow

```
User clicks "Stats" tab
        │
        ▼
  useQuery fires:
    GET /api/books/{bookId}/stats
    GET /api/books/{bookId}/translators/stats
        │
        ▼
  Render dashboard
        │
        ▼
  React Query refetchInterval: 30000ms
        │
        ▼ (every 30s)
  Background refetch (stale-while-revalidate)
        │
        ▼
  If data changed → smooth progress bar update
  If data unchanged → no re-render (React Query dedup)
```

---

## 4. State Diagrams

### 4.1 Translate Tab — Overall State Machine

```
                    ┌──────────────┐
                    │   MOUNTED    │
                    └──────┬───────┘
                           │ useEffect
                           ▼
                    ┌──────────────┐
                    │   LOADING    │ ←── Skip/Next button
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
           200 OK       404 Empty    Error
              │            │            │
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  READY   │ │  EMPTY   │ │  ERROR   │
        └────┬─────┘ └──────────┘ └──────────┘
             │
    ┌────────┼────────────────┐
    │        │                │
 Draft    No draft        Has previous
 exists                     submission
    │        │                │
    ▼        ▼                ▼
 ┌───────┐ ┌──────────┐ ┌──────────┐
 │DRAFTED│ │  TYPING  │ │ REVIEWING│
 └───┬───┘ └────┬─────┘ └──────────┘
     │          │
     │  5s idle │
     ▼          ▼
 ┌──────────────┐
 │  AUTO_SAVING │
 └──────┬───────┘
        │
   Success
        │
        ▼
 ┌──────────────┐
 │  SAVED       │ ──→ back to TYPING
 └──────────────┘

 Submit button:
 ┌──────────────┐
 │  SUBMITTING  │
 └──────┬───────┘
        │
   Success
        │
        ▼
 ┌──────────────┐
 │  SUBMITTED   │ ──→ loads next section → LOADING
 └──────────────┘
```

### 4.2 History Tab — State Machine

```
                    ┌──────────────┐
                    │   MOUNTED    │
                    └──────┬───────┘
                           │ useEffect
                           ▼
                    ┌──────────────┐
                    │   LOADING    │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
           200 OK       200 Empty    Error
              │            │            │
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  LOADED  │ │  EMPTY   │ │  ERROR   │
        └────┬─────┘ └──────────┘ └──────────┘
             │
             │ User scrolls
             ▼
        ┌──────────┐
        │ LOADING  │ ←── IntersectionObserver
        │  MORE    │
        └────┬─────┘
             │
        ┌────┼────┐
     hasMore   !hasMore
        │        │
        ▼        ▼
   Append    END_REACHED
   items
```

### 4.3 Stats Tab — State Machine

```
                    ┌──────────────┐
                    │   MOUNTED    │
                    └──────┬───────┘
                           │ useQuery
                           ▼
                    ┌──────────────┐
                    │   LOADING    │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
           200 OK       Empty data    Error
              │            │            │
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  LOADED  │ │  EMPTY   │ │  ERROR   │
        └────┬─────┘ └──────────┘ └──────────┘
             │
             │ 30s timer
             ▼
        ┌──────────────┐
        │  REFETCHING  │ (stale-while-revalidate)
        └──────┬───────┘
               │
               ▼
           LOADED (updated)
```

---

## 5. Responsive Behavior

### 5.1 Breakpoint Strategy

| Breakpoint | Width | Behavior |
| --- | --- | --- |
| Mobile | < 768px | Stacked layout, filter drawer, compact tabs |
| Tablet | 768–1024px | Collapsible side-by-side, two-row filters |
| Desktop | > 1024px | Full side-by-side layout, inline filters |

### 5.2 Layout Adaptation Rules

**Translate Tab:**

| Element | Desktop | Tablet | Mobile |
| --- | --- | --- | --- |
| Section image | 50% width, scrollable | 40% width, collapsible | Full width, 240px height |
| Source text | Right column, above editor | Right column, scrollable | Below image, before editor |
| Translation editor | Right column, auto-resize | Right column, fixed height | Full width, 120px min |
| Zoom controls | Below image, inline | Below image, inline | Overlay on image |
| Page context | Horizontal bar below editor | Horizontal bar below editor | "Page X of Y" with swipe |

**History Tab:**

| Element | Desktop | Tablet | Mobile |
| --- | --- | --- | --- |
| History items | Full-width rows, side-by-side | Full-width rows, stacked info | Stacked cards |
| Thumbnail | 48×48px inline | 48×48px inline | 64×64px top of card |
| Status badge | Inline with text | Inline with text | Separate row |

**Stats Tab:**

| Element | Desktop | Tablet | Mobile |
| --- | --- | --- | --- |
| Progress bar | Full width | Full width | Full width |
| Language cards | Horizontal row | 2-column grid | Single column stack |
| Page grid | Horizontal scroll, fixed cells | Horizontal scroll, smaller | Wrap to rows |
| Translator table | Full table | Table, some columns hidden | Card per translator |

### 5.3 Touch Interactions (Mobile/Tablet)

- **Filter drawer**: Swipe up to open, swipe down or tap overlay to close
- **History items**: Tap to navigate, long-press for context menu
- **Page grid cells**: Tap to filter history to that page
- **Translator cards**: Tap to expand/collapse
- **Zoom**: Pinch-to-zoom on section image (in addition to +/- buttons)
- **Textarea**: Native resize handle, auto-grow on input

---

## 6. Accessibility

### 6.1 Keyboard Navigation

| Key | Context | Action |
| --- | --- | --- |
| `Tab` | Anywhere | Move focus through interactive elements |
| `Shift+Tab` | Anywhere | Move focus backwards |
| `Enter` / `Space` | Tab bar | Activate focused tab |
| `Enter` / `Space` | History item | Navigate to section |
| `Enter` / `Space` | Translator row | Expand/collapse |
| `Escape` | Filter drawer | Close drawer |
| `Escape` | Translation editor | Blur textarea |
| `Ctrl+Enter` | Translation editor | Submit translation |
| `+` / `-` | Section image area | Zoom in/out |
| `?` | Anywhere | Toggle keyboard shortcuts help |

### 6.2 ARIA Attributes

```html
<!-- Tab bar -->
<div role="tablist" aria-label="Translation console tabs">
  <button role="tab" aria-selected="true" aria-controls="panel-translate" id="tab-translate">
    Translate
  </button>
  <button role="tab" aria-selected="false" aria-controls="panel-history" id="tab-history">
    History
  </button>
  <button role="tab" aria-selected="false" aria-controls="panel-stats" id="tab-stats">
    Stats
  </button>
</div>

<div role="tabpanel" id="panel-translate" aria-labelledby="tab-translate">
  <!-- translate content -->
</div>

<!-- Progress bar -->
<div role="progressbar" aria-valuenow="37.5" aria-valuemin="0" aria-valuemax="100"
     aria-label="Translation progress: 37.5%">
  <!-- visual bar -->
</div>

<!-- Auto-save indicator -->
<div aria-live="polite" aria-atomic="true">
  Draft saved
</div>

<!-- Status badges -->
<span aria-label="Approved">✅ APPROVED</span>
<span aria-label="Pending review">⏳ PENDING</span>
<span aria-label="Rejected">❌ REJECTED</span>

<!-- Page grid cells -->
<button aria-label="Page 1: 100% complete" data-page="1">🟢</button>
<button aria-label="Page 2: 50% complete" data-page="2">🟡</button>
<button aria-label="Page 4: not started" data-page="4">⬜</button>

<!-- History items -->
<a href="/translate?section={id}" aria-label="Page 3, Section 2: Approved translation">
  <!-- content -->
</a>

<!-- Filter controls -->
<label for="lang-filter">Language</label>
<select id="lang-filter" aria-describedby="lang-filter-desc">
  <option value="si">Sinhala</option>
</select>
<span id="lang-filter-desc" class="sr-only">
  Filter translations by target language
</span>
```

### 6.3 Screen Reader Announcements

| Event | Announcement |
| --- | --- |
| Section loaded | "Section loaded: Page 3, Section 2" |
| Draft saved | "Draft saved" (aria-live polite) |
| Translation submitted | "Translation submitted successfully" |
| History loaded | "History loaded: 15 translations" |
| Stats loaded | "Statistics loaded: 37.5% complete" |
| Error occurred | "Error: Failed to load section. Press Retry to try again." |
| No results | "No sections match your filters" |
| Tab switched | "History tab selected" (via tab activation) |

### 6.4 Color and Contrast

- All text meets WCAG AA contrast ratio (4.5:1 for normal text, 3:1 for large text)
- Status badges use icon + text + color (not color alone)
- Progress bar has text label alongside visual bar
- Page grid cells have text labels (not just colored squares)
- Focus indicators visible on all interactive elements (2px outline)
- Dark mode support via CSS custom properties

### 6.5 Focus Management

- On tab switch, focus moves to the new tab panel
- On section load, focus moves to the translation textarea
- On error, focus moves to the error message/retry button
- On submit success, focus moves to the next section's textarea
- Filter changes announce results via aria-live region

---

## 7. Empty, Loading, and Error States

### 7.1 Translate Tab

**Empty State (no sections match filters):**
```
┌─────────────────────────────────────────────────┐
│                                                 │
│           🔍                                    │
│                                                 │
│    No sections match your filters               │
│                                                 │
│    Try adjusting the language, page,            │
│    or status filters.                           │
│                                                 │
│    [Clear Filters]                              │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Empty State (all sections translated):**
```
┌─────────────────────────────────────────────────┐
│                                                 │
│           ✅                                    │
│                                                 │
│    All sections translated!                     │
│                                                 │
│    Great work! You've translated all            │
│    available sections for this book.            │
│                                                 │
│    [View History]                               │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Loading State:**
```
┌─────────────────────────────────────────────────┐
│                                                 │
│  ┌──────────────────────┬────────────────────┐  │
│  │  [Skeleton placeholder│  [Skeleton        │  │
│  │   matching image      │   placeholder     │  │
│  │   aspect ratio]       │   matching text   │  │
│  │                       │   areas]          │  │
│  │                       │                   │  │
│  └──────────────────────┴────────────────────┘  │
│                                                 │
│  Loading section...  ◠                          │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Error State:**
```
┌─────────────────────────────────────────────────┐
│                                                 │
│           ⚠️                                    │
│                                                 │
│    Failed to load section                       │
│                                                 │
│    Error: Network request failed                │
│                                                 │
│    [Retry]  [Skip to next section]              │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 7.2 History Tab

**Empty State:**
```
┌─────────────────────────────────────────────────┐
│                                                 │
│           📝                                    │
│                                                 │
│    No translations yet                          │
│                                                 │
│    Start translating to see your                │
│    submission history here.                     │
│                                                 │
│    [Start Translating]                          │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Loading State (initial):**
```
┌─────────────────────────────────────────────────┐
│                                                 │
│  ┌─ Skeleton Row ─────────────────────────────┐ │
│  │ [□□□□]  □□□□□□□□□□□□□□□□□□□□□□□□□         │ │
│  │         □□□□□□□□□□□□                       │ │
│  ├─ Skeleton Row ─────────────────────────────┤ │
│  │ [□□□□]  □□□□□□□□□□□□□□□□□□□□□□□□         │ │
│  │         □□□□□□□□□□□□                       │ │
│  ├─ Skeleton Row ─────────────────────────────┤ │
│  │ [□□□□]  □□□□□□□□□□□□□□□□□□□□□□□□         │ │
│  │         □□□□□□□□□□□□                       │ │
│  ├─ Skeleton Row ─────────────────────────────┤ │
│  │ [□□□□]  □□□□□□□□□□□□□□□□□□□□□□□□         │ │
│  │         □□□□□□□□□□□□                       │ │
│  └────────────────────────────────────────────┘ │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Loading More (infinite scroll):**
```
┌─────────────────────────────────────────────────┐
│  ... existing history items ...                 │
│                                                 │
│           ◠  Loading more translations...       │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Error State:**
```
┌─────────────────────────────────────────────────┐
│                                                 │
│           ⚠️                                    │
│                                                 │
│    Failed to load translation history           │
│                                                 │
│    [Retry]                                      │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 7.3 Stats Tab

**Empty State:**
```
┌─────────────────────────────────────────────────┐
│                                                 │
│           📊                                    │
│                                                 │
│    No translation data yet                      │
│                                                 │
│    Sections need to be translated               │
│    before statistics appear here.               │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Loading State:**
```
┌─────────────────────────────────────────────────┐
│                                                 │
│  ┌─ Skeleton Card ────────────────────────────┐ │
│  │  □□□□□□□□□□□□□□□□□□                       │ │
│  │  [████████████░░░░░░░░░░░░]                │ │
│  │  □□□  □□□□  □□□□  □□□□□                   │ │
│  └────────────────────────────────────────────┘ │
│                                                 │
│  ┌─ Skeleton Grid ────────────────────────────┐ │
│  │  [□□□□□□] [□□□□□□]                        │ │
│  │  [□□□□□□] [□□□□□□]                        │ │
│  └────────────────────────────────────────────┘ │
│                                                 │
│  Loading statistics...  ◠                       │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Error State:**
```
┌─────────────────────────────────────────────────┐
│                                                 │
│           ⚠️                                    │
│                                                 │
│    Failed to load statistics                    │
│                                                 │
│    [Retry]                                      │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 8. Micro-interactions and Transitions

### 8.1 Timing Guidelines

| Interaction | Duration | Easing |
| --- | --- | --- |
| Tab content fade-in | 200ms | ease-out |
| Tab content slide-up | 200ms | ease-out |
| Draft saved indicator | 2s auto-dismiss | ease-in |
| Draft saved slide-in | 200ms | ease-out |
| History item hover | 150ms | ease |
| History item press | 100ms | ease-in |
| Progress bar fill | 600ms | ease-out |
| Page grid cell hover | 150ms | ease |
| Translator row expand | 300ms | ease-in-out |
| Toast slide-in | 200ms | ease-out |
| Toast auto-dismiss | 3s | ease-in |
| Filter flash | 150ms | ease |
| Skip button spin | 400ms | ease-in-out |
| Submit loading dots | 1.5s cycle | linear |
| Empty state float | 3s infinite | ease-in-out |
| Status badge pulse | 600ms | ease-in-out |
| Skeleton shimmer | 1.5s infinite | linear |
| Error shake | 400ms | ease |
| Zoom smooth | 150ms | ease |

### 8.2 CSS Transition Classes

```css
/* Tab content */
.tab-content-enter {
  opacity: 0;
  transform: translateY(8px);
}
.tab-content-active {
  opacity: 1;
  transform: translateY(0);
  transition: opacity 200ms ease-out, transform 200ms ease-out;
}

/* Draft indicator */
.draft-indicator-enter {
  opacity: 0;
  transform: translateX(16px);
}
.draft-indicator-active {
  opacity: 1;
  transform: translateX(0);
  transition: opacity 200ms ease-out, transform 200ms ease-out;
}
.draft-indicator-exit {
  opacity: 0;
  transition: opacity 300ms ease-in;
}

/* History item */
.history-item {
  transition: background-color 150ms ease, border-color 150ms ease;
}
.history-item:active {
  transform: scale(0.98);
  transition: transform 100ms ease-in;
}

/* Progress bar */
.progress-bar-fill {
  transition: width 600ms ease-out;
}

/* Page grid cell */
.page-grid-cell {
  transition: transform 150ms ease, box-shadow 150ms ease;
}
.page-grid-cell:hover {
  transform: scale(1.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

/* Translator row expand */
.translator-row-content {
  overflow: hidden;
  transition: max-height 300ms ease-in-out, opacity 300ms ease-in-out;
}

/* Skeleton shimmer */
@keyframes shimmer {
  0% { background-position: -200px 0; }
  100% { background-position: calc(200px + 100%) 0; }
}
.skeleton {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200px 100%;
  animation: shimmer 1.5s infinite;
}

/* Error shake */
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-4px); }
  75% { transform: translateX(4px); }
}
.error-shake {
  animation: shake 400ms ease;
}

/* Empty state float */
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}
.empty-state-icon {
  animation: float 3s ease-in-out infinite;
}

/* Status badge pulse */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
.status-change {
  animation: pulse 600ms ease-in-out;
}
```

### 8.3 Toast Notification System

```
┌─────────────────────────────────────────────────┐
│  Toast Container (fixed, top-right)             │
│                                                 │
│  ┌─────────────────────────────────────────┐    │
│  │ ✅ Translation saved!                    │    │
│  │ ████████████████████░░░░░░ (progress)   │    │
│  └─────────────────────────────────────────┘    │
│                                                 │
│  ┌─────────────────────────────────────────┐    │
│  │ ⚠️ Failed to save draft                 │    │
│  │ ████████████████████░░░░░░ (progress)   │    │
│  └─────────────────────────────────────────┘    │
│                                                 │
└─────────────────────────────────────────────────┘
```

- Position: fixed, top-right, 16px from edges
- Max 3 toasts visible at once (oldest dismissed)
- Auto-dismiss after 3s (success) or 5s (error)
- Progress bar shows remaining time
- Click to dismiss early
- Stack with 8px gap between toasts

---

## 9. URL State Management

### 9.1 URL Param Schema

```
/translate?tab=translate&bookId={id}&lang=si&page=5&status=pending
/translate?tab=history&bookId={id}&lang=si&page=5&status=approved
/translate?tab=stats&bookId={id}
```

### 9.2 Param Rules

| Param | Values | Default | Notes |
| --- | --- | --- | --- |
| `tab` | `translate`, `history`, `stats` | `translate` | Active tab |
| `bookId` | ObjectId string | (required) | Selected book |
| `lang` | ISO 639-1 code | (all) | Language filter, hidden if single lang |
| `page` | integer | (all) | Page number filter |
| `status` | `pending`, `approved`, `rejected` | (all) | Status filter |
| `section` | ObjectId string | (none) | Pre-select section in translate tab |

### 9.3 Filter Independence

- Translate tab filters: `lang`, `page`, `status` (affect section queue)
- History tab filters: `lang`, `page`, `status` (affect history query)
- Stats tab: no filters (always shows full book stats)
- Changing filters in one tab does NOT affect the other tab's filters
- Both tabs share the same URL params, but interpret them independently
- Filter state is read from URL on mount and on tab switch

### 9.4 URL Update Behavior

```typescript
// When user changes a filter
const updateFilter = (key: string, value: string | null) => {
  const params = new URLSearchParams(searchParams)
  if (value === null) {
    params.delete(key)
  } else {
    params.set(key, value)
  }
  router.push(`/translate?${params.toString()}`, { scroll: false })
}
```

- Filters update URL immediately on selection (no "Apply" button)
- `scroll: false` prevents page jump
- Browser back/forward restores previous filter state
- Filters are shareable via URL copy

---

## 10. Keyboard Shortcuts Reference

Accessible via `?` key or help button in the toolbar.

```
┌─────────────────────────────────────────────────┐
│  Keyboard Shortcuts                          [✕] │
├─────────────────────────────────────────────────┤
│                                                 │
│  Translation Editor                             │
│  ─────────────────                              │
│  Ctrl+Enter      Submit translation             │
│  Escape          Blur textarea / skip section   │
│                                                 │
│  Navigation                                     │
│  ──────────                                     │
│  1               Switch to Translate tab        │
│  2               Switch to History tab          │
│  3               Switch to Stats tab (editors)  │
│                                                 │
│  Section Image                                  │
│  ──────────────                                 │
│  + / =           Zoom in                        │
│  -               Zoom out                       │
│  0               Reset zoom to 100%             │
│                                                 │
│  General                                        │
│  ────────                                       │
│  ?               Toggle this help panel         │
│  /               Focus filter search            │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 11. Implementation Notes

### 11.1 Component File Structure

```
apps/web/app/translate/
├── page.tsx                    # Main translate page (Client Component)
├── TranslateTab.tsx            # Translate tab content
├── HistoryTab.tsx              # History tab content
├── StatsTab.tsx                # Stats tab content
├── TranslateFilters.tsx        # Filter bar component
├── components/
│   ├── SourceTextPanel.tsx     # Original text display
│   ├── TranslationEditor.tsx  # Textarea + exact letter input
│   ├── DraftSaveIndicator.tsx  # "Draft saved" feedback
│   ├── SectionImageDisplay.tsx # Zoomable section image
│   ├── PreviousSubmission.tsx  # My previous submission panel
│   ├── ApprovedTranslation.tsx # Approved translation display
│   ├── HistoryItem.tsx         # Single history row
│   ├── TranslatorStatsRow.tsx # Expandable translator stats row
│   ├── PageGrid.tsx            # Per-page breakdown grid
│   ├── LanguageCards.tsx       # Per-language breakdown cards
│   └── ProgressBar.tsx         # Animated progress bar
```

### 11.2 Custom Hooks

```
apps/web/hooks/
├── useTranslationFilters.ts   # URL-synced filter state
├── useTranslationDraft.ts     # Auto-save draft logic
├── useInfiniteScroll.ts       # IntersectionObserver for infinite scroll
└── useTabState.ts             # Tab switching with URL persistence
```

### 11.3 Performance Considerations

- **Lazy loading**: Tab content loaded only when tab is active (first visit)
- **Image lazy loading**: Section images use `loading="lazy"` attribute
- **Virtual scrolling**: Consider for history lists > 100 items (future optimization)
- **React Query**: Background refetch on tab focus, stale-while-revalidate
- **Debounced auto-save**: 5s debounce prevents excessive API calls
- **Cursor-based pagination**: Avoids skip/limit performance issues
- **Redis caching**: 30s TTL for expensive stats aggregations
- **Skeleton screens**: Perceived performance improvement for loading states

---

## 12. Related Files

- `specs/business-analysis/20260706-1200-translation-page-redesign.md` — User stories
- `specs/business-analysis/data-model.md` — Data model with computed entities
- `specs/architecture/20260706-1200-translation-page-redesign.md` — Technical architecture
- `specs/architecture/architecture.md` — Existing architecture
- `specs/ux/ui-design.md` — Updated UI/UX design (Translation Interface section)
