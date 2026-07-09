# Source Text Modifications — UX/Interaction Spec

**Date:** 2026-07-06 13:00
**Author:** UX Agent
**Epic Reference:** Epic 1 — Book Upload & Processing, Epic 4 — Translation
**Related BA:** `specs/business-analysis/20260706-1300-source-text-modifications.md`
**Related Architecture:** `specs/architecture/20260706-1300-source-text-modifications.md`
**Updated UI Design:** `specs/ux/ui-design.md`

---

## 1. Overview

This spec redesigns the Translate Tab layout to introduce a two-row, four-panel design. The top row pairs the section image with source text (sharing zoom), and the bottom row pairs exact letter transliteration with the translator's output. Bidirectional sync between source text and transliteration is the core interaction pattern.

---

## 2. Wireframe Layouts

### 2.1 Desktop (>1024px) — Translate Tab (Redesigned)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ← Dashboard   Book: "Gaha Ulela"   Page 3   [👤 Kamal Perera]        │
├─────────────────────────────────────────────────────────────────────────┤
│  🔍 [Language ▼ Sinhala]  [Page ▼ All]  [Status ▼ All]  [✕ Clear]    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  [■ Translate]  [□ History]  [□ Stats]                                 │
│  ─────────────                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─ TOP ROW: Image + Source Text (shared zoom) ──────────────────────┐  │
│  │                                                                     │  │
│  │  ┌───────────────────────────┬──────────────────────────────────┐  │  │
│  │  │                           │                                  │  │  │
│  │  │  Section Image            │  📄 Source Text                  │  │  │
│  │  │  ┌─────────────────────┐  │  ┌────────────────────────────┐  │  │  │
│  │  │  │                     │  │  │ [AI Extracted] 94% ●        │  │  │  │
│  │  │  │  [CROPPED SECTION]  │  │  │                            │  │  │  │
│  │  │  │  (drag to pan)      │  │  │ මාතාව සියලු දේවතාවුන්ගේ   │  │  │  │
│  │  │  │                     │  │  │ ගේ ගුණ ගීතය මෙසේ          │  │  │  │
│  │  │  │                     │  │  │ දැක්වේ..."                 │  │  │  │
│  │  │  │                     │  │  │                            │  │  │  │
│  │  │  │                     │  │  │ (editable textarea,         │  │  │  │
│  │  │  │                     │  │  │  font scales with zoom)    │  │  │  │
│  │  │  └─────────────────────┘  │  │                            │  │  │  │
│  │  │                           │  │ [Extract Text] [Regenerate] │  │  │  │
│  │  │  [−] 100% [+] [⟳]       │  └────────────────────────────┘  │  │  │
│  │  │                           │                                  │  │  │
│  │  └───────────────────────────┴──────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─ BOTTOM ROW: Transliteration + Translation ───────────────────────┐  │
│  │                                                                     │  │
│  │  ┌───────────────────────────┬──────────────────────────────────┐  │  │
│  │  │                           │                                  │  │  │
│  │  │  ✏️ Exact Letter           │  📝 Your Translation *           │  │  │
│  │  │  Transliteration           │                                  │  │  │
│  │  │  ┌─────────────────────┐  │  ┌────────────────────────────┐  │  │  │
│  │  │  │ [AI Generated] ●    │  │  │ මාතාවගේ සියලු දේවතාවුන්   │  │  │  │
│  │  │  │                     │  │  │ ගේ ගුණ ගීතය මෙසේ          │  │  │  │
│  │  │  │ මාතා → माता         │  │  │ දැක්වේ..."                 │  │  │  │
│  │  │  │ සියලු → सर्व         │  │  │                            │  │  │  │
│  │  │  │                     │  │  │ (auto-resize textarea)      │  │  │  │
│  │  │  │ (editable input)    │  │  └────────────────────────────┘  │  │  │
│  │  │  └─────────────────────┘  │                                  │  │  │
│  │  │                           │  💾 Draft saved ✓                │  │  │
│  │  └───────────────────────────┴──────────────────────────────────┘  │  │
│  │                                                                     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  [Skip]  [Submit Translation]            Page 3 of 12 sections         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Desktop — Source Text Panel (AI Extraction States)

**State: AI Extraction Complete**

```
┌────────────────────────────────────────────────────────────┐
│  📄 Source Text                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ [AI Extracted] 94% ●                                 │  │
│  │                                                      │  │
│  │ මාතාව සියලු දේවතාවුන්ගේ ගුණ ගීතය මෙසේ දැක්වේ..."    │  │
│  │                                                      │  │
│  │ (editable — changes sync to transliteration)          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  [🔄 Regenerate]  [View OCR]                               │
│                                                            │
│  (editors only) Edit original text →                       │
└────────────────────────────────────────────────────────────┘
```

**State: AI Extraction In Progress**

```
┌────────────────────────────────────────────────────────────┐
│  📄 Source Text                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ [Extracting...] ● ○                                  │  │
│  │                                                      │  │
│  │ (showing OCR text as fallback while AI processes)    │  │
│  │ මාතාව සියලු දේවතාවුන්ගේ ගුණ ගීතය මෙසේ දැක්වේ..."    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ⏳ AI extraction in progress...                           │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**State: AI Extraction Failed**

```
┌────────────────────────────────────────────────────────────┐
│  📄 Source Text                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ [Extraction failed] ✕                                │  │
│  │                                                      │  │
│  │ මාතාව සියලු දේවතාවුන්ගේ ගුණ ගීතය මෙසේ දැක්වේ..."    │  │
│  │ (OCR text — fallback)                                │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ⚠️ Extraction failed — using OCR text                     │
│  [🔄 Retry Extraction]                                     │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**State: No Extraction (OCR Only)**

```
┌────────────────────────────────────────────────────────────┐
│  📄 Source Text                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ [OCR] ●                                              │  │
│  │                                                      │  │
│  │ මාතාව සියලු දේවතාවුන්ගේ ගුණ ගීතය මෙසේ දැක්වේ..."    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  [✨ Extract Text]  (editors only)                         │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 2.3 Desktop — Exact Letter Transliteration Panel (States)

**State: AI Transliteration Available**

```
┌────────────────────────────────────────────────────────────┐
│  ✏️ Exact Letter Transliteration                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ [AI Generated] ●                                     │  │
│  │                                                      │  │
│  │ මාතා → माता                                         │  │
│  │ සියලු → सर्व                                         │  │
│  │ දේවතාවුන් → देवतावुन्                                  │  │
│  │                                                      │  │
│  │ (editable — changes sync to source text)              │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  [🔄 Regenerate]                                           │
└────────────────────────────────────────────────────────────┘
```

**State: Transliteration In Progress**

```
┌────────────────────────────────────────────────────────────┐
│  ✏️ Exact Letter Transliteration                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ [Generating...] ● ○                                  │  │
│  │                                                      │  │
│  │ ◠ Generating transliteration...                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ⏳ Please wait...                                         │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**State: Transliteration Failed**

```
┌────────────────────────────────────────────────────────────┐
│  ✏️ Exact Letter Transliteration                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ [Unavailable] ✕                                      │  │
│  │                                                      │  │
│  │ (empty — enter manually)                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ⚠️ Transliteration unavailable — enter manually           │
│  [🔄 Retry]                                                │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**State: Manual Entry**

```
┌────────────────────────────────────────────────────────────┐
│  ✏️ Exact Letter Transliteration                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ [Manual] ●                                           │  │
│  │                                                      │  │
│  │ මාතා → माता                                         │  │
│  │ (typed by translator)                                │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  [🔄 Generate with AI]                                     │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 2.4 Desktop — Confidence Badge Component

```
┌────────────────────┐
│ [AI Extracted] 94% │  ← green badge (≥ 0.9)
└────────────────────┘

┌────────────────────┐
│ [AI Extracted] 78% │  ← yellow badge (≥ 0.7)
└────────────────────┘

┌────────────────────┐
│ [AI Extracted] 45% │  ← red badge (< 0.7)
└────────────────────┘

┌──────────────┐
│ [OCR]        │  ← gray badge (no AI extraction)
└──────────────┘
```

Badge colors:

- Green (`#16A34A`): confidence ≥ 0.9
- Yellow (`#F59E0B`): confidence ≥ 0.7
- Red (`#DC2626`): confidence < 0.7
- Gray (`#94A3B8`): OCR fallback (no confidence)

### 2.5 Mobile (<768px) — Translate Tab (Redesigned)

```
┌───────────────────────────────────┐
│  ← Dashboard   [👤 Kamal]        │
├───────────────────────────────────┤
│  [▼ Filters]  (tap to expand)    │
├───────────────────────────────────┤
│  [Translate] [History] [Stats]   │
├───────────────────────────────────┤
│                                   │
│  TOP ROW (stacked on mobile)     │
│                                   │
│  Section Image                   │
│  ┌─────────────────────────────┐ │
│  │  [CROPPED SECTION]          │ │
│  │  (drag to pan)              │ │
│  └─────────────────────────────┘ │
│  [−] 100% [+] [⟳]              │
│                                   │
│  📄 Source Text [AI Extracted]    │
│  ┌─────────────────────────────┐ │
│  │ මාතාව සියලු දේවතාවුන්ගේ      │ │
│  │ ගේ ගුණ ගීතය..."            │ │
│  └─────────────────────────────┘ │
│  [✨ Extract] [🔄 Regenerate]    │
│                                   │
│  BOTTOM ROW (stacked)            │
│                                   │
│  ✏️ Exact Letter [AI Generated]  │
│  ┌─────────────────────────────┐ │
│  │ මාතා → मातা                 │ │
│  │ සියලු → सर्व                 │ │
│  └─────────────────────────────┘ │
│  [🔄 Regenerate]                 │
│                                   │
│  📝 Your Translation *           │
│  ┌─────────────────────────────┐ │
│  │ මාතාවගේ සියලු දේවතාවුන්      │ │
│  │ ගේ ගුණ ගීතය..."            │ │
│  └─────────────────────────────┘ │
│                                   │
│  💾 Draft saved ✓                │
│                                   │
│  [Skip]  [Submit Translation]    │
│                                   │
│  [← Prev]  Page 3/12  [Next →]  │
│                                   │
└───────────────────────────────────┘
```

### 2.6 Tablet (768–1024px) — Translate Tab (Redesigned)

```
┌───────────────────────────────────────────────────────┐
│  ← Dashboard   Book: "Gaha Ulela"   [👤 Kamal]       │
├───────────────────────────────────────────────────────┤
│  [Translate] [History] [Stats]                       │
├───────────────────────────────────────────────────────┤
│                                                       │
│  ┌──────────────────────┬──────────────────────────┐ │
│  │                      │                           │ │
│  │  Section Image       │  📄 Source Text           │ │
│  │  (collapsible)       │  (scrollable)             │ │
│  │                      │                           │ │
│  └──────────────────────┴──────────────────────────┘ │
│  [−] 100% [+] [⟳]                                    │
│                                                       │
│  ┌──────────────────────┬──────────────────────────┐ │
│  │                      │                           │ │
│  │  ✏️ Exact Letter      │  📝 Your Translation      │ │
│  │  Transliteration     │                           │ │
│  │                      │                           │ │
│  └──────────────────────┴──────────────────────────┘ │
│                                                       │
│  [Skip]  [Submit Translation]         Page 3/12      │
│                                                       │
└───────────────────────────────────────────────────────┘
```

---

## 3. Component Interaction Patterns

### 3.1 Bidirectional Sync — Source Text ↔ Transliteration

```
┌─────────────────────────────────────────────────────────────────┐
│  BIDIRECTIONAL SYNC FLOW                                        │
│                                                                 │
│  User edits Source Text panel                                   │
│         │                                                       │
│         ▼                                                       │
│  ┌─ 500ms debounce ──────────────────────────────────────────┐  │
│  │                                                            │  │
│  │  1. Save updated source text via                           │  │
│  │     PUT /api/sections/{id}/source-text                     │  │
│  │                                                            │  │
│  │  2. Backend invalidates cached transliterations            │  │
│  │                                                            │  │
│  │  3. Frontend shows "Regenerate" button on                  │  │
│  │     transliteration panel (cached result now stale)        │  │
│  │                                                            │  │
│  │  4. Auto-translation re-triggered on next submit           │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                 │
│  User edits Exact Letter Transliteration panel                  │
│         │                                                       │
│         ▼                                                       │
│  ┌─ 500ms debounce ──────────────────────────────────────────┐  │
│  │                                                            │  │
│  │  1. Save updated transliteration locally                   │  │
│  │     (no API call — it's the translator's manual input)     │  │
│  │                                                            │  │
│  │  2. Update Translation.transliterationSource = "manual"    │  │
│  │                                                            │  │
│  │  3. Source text panel remains unchanged                    │  │
│  │     (transliteration does NOT modify source text)          │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Key rule: Source text → Transliteration (one-way sync)         │
│  Transliteration edits are independent (manual override)        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Shared Zoom Interaction

```
┌─────────────────────────────────────────────────────────────────┐
│  SHARED ZOOM FLOW                                               │
│                                                                 │
│  User clicks + / − / 0 on zoom controls                         │
│         │                                                       │
│         ▼                                                       │
│  setZoom(newLevel)                                              │
│         │                                                       │
│         ├──────────────────────────────────┐                    │
│         ▼                                  ▼                    │
│  Section Image                    Source Text Panel             │
│  ┌────────────────────┐           ┌──────────────────────┐     │
│  │ width: zoom%       │           │ fontSize: 14 *        │     │
│  │ (CSS transform     │           │   (zoom / 100)        │     │
│  │  scale)            │           │ (proportional font    │     │
│  │                    │           │  scaling)             │     │
│  │ drag-to-pan:       │           │                       │     │
│  │ works at any zoom  │           │ scrollable at         │     │
│  │                    │           │ any zoom              │     │
│  └────────────────────┘           └──────────────────────┘     │
│                                                                 │
│  Zoom controls: [−] {zoom}% [+] [⟳ Reset]                     │
│  - Min: 50%, Max: 300%, Step: 10%                              │
│  - Reset button (⟳) returns to 100%                            │
│  - Keyboard: + / − when image area focused                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 AI Extraction Status Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  AI EXTRACTION STATUS FLOW                                      │
│                                                                 │
│  Section loads                                                  │
│         │                                                       │
│         ▼                                                       │
│  Check section.aiExtractedText                                  │
│         │                                                       │
│    ┌────┴────────────────────┐                                  │
│    │                         │                                  │
│  Has AI text            No AI text                              │
│    │                         │                                  │
│    ▼                         ▼                                  │
│  Show AI text            Check extractionStatus                 │
│  with confidence              │                                 │
│  badge                       ┌┴──────────────┐                  │
│    │                         │               │                  │
│    │                     "pending"      "failed"/null           │
│    │                         │               │                  │
│    │                         ▼               ▼                  │
│    │                    Show OCR text   Show OCR text           │
│    │                    + "Extracting   + "Extract Text"        │
│    │                   ..." indicator    button (editors)       │
│    │                         │               │                  │
│    └─────────────────────────┴───────────────┘                  │
│                      │                                          │
│                      ▼                                          │
│              Ready state                                        │
│                                                                 │
│  Editor clicks "Extract Text"                                   │
│         │                                                       │
│         ▼                                                       │
│  POST /api/sections/{id}/extract                                │
│         │                                                       │
│    ┌────┴────────────────────┐                                  │
│    │                         │                                  │
│  202 Queued              409 Already extracted                  │
│    │                         │                                  │
│    ▼                         ▼                                  │
│  Show "Extracting..."     Show existing result                  │
│  polling indicator         with confidence badge                │
│    │                                                       │
│    │ Poll GET /api/sections/{id}/extraction                │
│    │ (every 2s, max 30 attempts)                           │
│    │                                                       │
│    ├────────────┬──────────────┐                            │
│    │            │              │                            │
│  200 OK      Still 404      Error                           │
│    │         (not done)        │                            │
│    ▼            │              ▼                            │
│  Update panel  │           Show "Failed"                    │
│  with AI text  │           + "Retry" button                 │
│  + confidence     (continue polling)                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.4 Transliteration Generation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  TRANSLITERATION GENERATION FLOW                                 │
│                                                                 │
│  Section loads with AI extracted text                           │
│         │                                                       │
│         ▼                                                       │
│  Check for cached transliteration                               │
│  GET /api/sections/{id}/transliterations                        │
│         │                                                       │
│    ┌────┴────────────┐                                          │
│    │                 │                                          │
│  Cached           Not cached                                    │
│    │                 │                                          │
│    ▼                 ▼                                          │
│  Pre-fill          Show "Generate with AI"                     │
│  exactLetter       button on transliteration panel              │
│  field                                                  │     │
│    │                  │                                         │
│    │            User clicks                                     │
│    │            "Generate with AI"                              │
│    │                  │                                         │
│    │                  ▼                                         │
│    │            POST /api/sections/{id}/transliterate           │
│    │            ?targetScript=sinhala                           │
│    │                  │                                         │
│    │             ┌────┴────────────┐                            │
│    │             │                 │                            │
│    │          200 Cached        202 Queued                     │
│    │             │                 │                            │
│    │             ▼                 ▼                            │
│    │          Pre-fill field    Show "Generating..."            │
│    │                            spinner                         │
│    │                                  │                         │
│    │                            Poll result                     │
│    │                                  │                         │
│    │                           ┌──────┴──────┐                 │
│    │                           │             │                 │
│    │                         200 OK        Error               │
│    │                           │             │                 │
│    │                           ▼             ▼                 │
│    │                      Pre-fill       "Transliteration      │
│    │                      field          unavailable"          │
│    │                                     + empty field         │
│    │                                                           │
│    └───────────────────────────────────────────────────────────┘
│                                                                 │
│  User edits transliteration field                               │
│         │                                                       │
│         ▼                                                       │
│  Mark transliterationSource = "manual"                          │
│  (no API call for manual edits)                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.5 "Regenerate" Button Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  REGENERATE FLOW                                                │
│                                                                 │
│  "Regenerate" appears when:                                     │
│  1. Source text was edited (cache invalidated)                  │
│  2. Previous extraction failed and user wants retry             │
│  3. User wants to re-run AI extraction                         │
│                                                                 │
│  User clicks "Regenerate"                                       │
│         │                                                       │
│         ▼                                                       │
│  Confirm dialog:                                                │
│  "Re-extract text from this section image?                       │
│   This will replace the current AI text."                       │
│         │                                                       │
│    ┌────┴────────┐                                              │
│    │             │                                              │
│  Cancel       Confirm                                           │
│    │             │                                              │
│  (noop)          ▼                                              │
│              POST /api/sections/{id}/extract                    │
│              (same flow as initial extraction)                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. State Diagrams

### 4.1 Translate Tab — Updated State Machine

```
                      ┌──────────────┐
                      │   MOUNTED    │
                      └──────┬───────┘
                             │ useEffect
                             ▼
                      ┌──────────────┐
                      │   LOADING    │ ←── Skip/Next/Regenerate
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
      ┌────────┼──────────────────────┐
      │        │                      │
   AI text   No AI text            AI extracting
   exists                        (pending status)
      │        │                      │
      ▼        ▼                      ▼
  ┌────────┐ ┌────────┐         ┌──────────┐
  │ AI_SRC │ │OCR_SRC │         │ EXTRACTING│
  └───┬────┘ └───┬────┘         └─────┬────┘
      │          │                     │
      │    ┌─────┴──────┐              │ Poll result
      │    │            │              │
      │  Editor?    Translator?    ┌───┴───┐
      │    │            │          │       │
      │    ▼            ▼        Done   Failed
      │  Extract     (no button)  │       │
      │  button                   ▼       ▼
      │    │              AI_SRC  OCR_SRC
      │    │              (retry)
      │
      │  Transliteration check
      │         │
      │    ┌────┴────────────┐
      │    │                 │
      │  Cached          Not cached
      │    │                 │
      │    ▼                 ▼
      │  ┌──────────┐  ┌──────────┐
      │  │TRANS_LIT │  │TRANS_AVAIL│
      │  └────┬─────┘  └─────┬────┘
      │       │              │
      │       │         User clicks
      │       │         "Generate"
      │       │              │
      │       │              ▼
      │       │         ┌──────────┐
      │       │         │GENERATING│
      │       │         └────┬─────┘
      │       │              │
      │       │         ┌────┴───┐
      │       │         │        │
      │       │       Done    Failed
      │       │         │        │
      │       │         ▼        ▼
      │       │    TRANS_LIT  TRANS_UNAVAIL
      │       │
      └───────┴──── EDITING state
                      │
                      │ User types
                      ▼
                ┌──────────┐
                │  TYPING  │
                └────┬─────┘
                     │ 5s idle
                     ▼
                ┌──────────┐
                │AUTO_SAVING│
                └────┬─────┘
                     │
                ┌────┴───┐
             Success   Error
                │        │
                ▼        ▼
           ┌───────┐ ┌───────┐
           │ SAVED │ │ ERROR │
           └───────┘ └───────┘

  Submit:
  ┌──────────┐
  │SUBMITTING│
  └────┬─────┘
       │ Success
       ▼
  ┌──────────┐
  │SUBMITTED │ → loads next section
  └──────────┘
```

---

## 5. Responsive Behavior

### 5.1 Breakpoint Strategy

| Breakpoint | Width      | Top Row                   | Bottom Row         | Zoom Controls    |
| ---------- | ---------- | ------------------------- | ------------------ | ---------------- |
| Mobile     | < 768px    | Stacked vertically        | Stacked vertically | Overlay on image |
| Tablet     | 768–1024px | Side-by-side, collapsible | Side-by-side       | Below image      |
| Desktop    | > 1024px   | Full side-by-side         | Full side-by-side  | Below image      |

### 5.2 Layout Adaptation — Translate Tab

| Element            | Desktop (>1024px)       | Tablet (768–1024px)    | Mobile (<768px)         |
| ------------------ | ----------------------- | ---------------------- | ----------------------- |
| Section image      | 50% top row             | 40% collapsible        | Full width, 240px       |
| Source text        | 50% top row, scrollable | 60% scrollable         | Full width, below image |
| Source text font   | Scales with zoom        | Scales with zoom       | Fixed 14px              |
| Exact letter       | 50% bottom row          | 50% bottom row         | Full width              |
| Translation editor | 50% bottom row          | 50% bottom row         | Full width              |
| Zoom controls      | Below image, inline     | Below image, inline    | Overlay on image        |
| Extract button     | Below source text       | Below source text      | Below source text       |
| Regenerate button  | Below panel             | Below panel            | Below panel             |
| Confidence badge   | Inline in panel header  | Inline in panel header | Inline in panel header  |

### 5.3 Touch Interactions (Mobile/Tablet)

- **Image drag-to-pan**: Touch-and-drag on image to pan (existing behavior preserved)
- **Pinch-to-zoom**: Pinch gesture on image to zoom (in addition to +/- buttons)
- **Textarea**: Native resize handle, auto-grow on input
- **Panel collapse**: Swipe up to collapse top row on tablet, tap header to toggle

---

## 6. Loading States

### 6.1 Section Loading Skeleton

```
┌─────────────────────────────────────────────────────────────────┐
│  Loading section...  ◠                                          │
│                                                                 │
│  ┌─ TOP ROW ───────────────────────────────────────────────┐   │
│  │  ┌──────────────────────┬──────────────────────────────┐ │   │
│  │  │  [Skeleton image     │  [Skeleton text area]         │ │   │
│  │  │   placeholder]       │  □□□□□□□□□□□□□□□□□□           │ │   │
│  │  │                      │  □□□□□□□□□□□□□□               │ │   │
│  │  │                      │  □□□□□□□□□□□□□□□□□□           │ │   │
│  │  │                      │  □□□□□□□□□□                   │ │   │
│  │  └──────────────────────┴──────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─ BOTTOM ROW ────────────────────────────────────────────┐   │
│  │  ┌──────────────────────┬──────────────────────────────┐ │   │
│  │  │  □□□□□□□□□□           │  □□□□□□□□□□                   │ │   │
│  │  │  □□□□□□□□□□□□□□□□    │  □□□□□□□□□□□□□□□□□□           │ │   │
│  │  │  □□□□□□□□□□□□□□      │  □□□□□□□□□□□□□□               │ │   │
│  │  └──────────────────────┴──────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 AI Extraction Loading (Within Source Text Panel)

```
┌──────────────────────────────────────────────────────────┐
│  📄 Source Text                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ [Extracting...] ●○○                                │  │
│  │                                                    │  │
│  │ (OCR text shown as fallback)                       │  │
│  │ මාතාව සියලු දේවතාවුන්ගේ..."                         │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ⏳ AI extraction in progress — this may take a few seconds │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 6.3 Transliteration Loading (Within Transliteration Panel)

```
┌──────────────────────────────────────────────────────────┐
│  ✏️ Exact Letter Transliteration                         │
│  ┌────────────────────────────────────────────────────┐  │
│  │ [Generating...] ●○○                                │  │
│  │                                                    │  │
│  │ ◠ Generating transliteration...                    │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ⏳ Please wait — generating letter-for-letter conversion │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 7. Error States and Fallbacks

### 7.1 AI Extraction Failed — Source Text Panel

```
┌──────────────────────────────────────────────────────────┐
│  📄 Source Text                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ [Extraction failed] ✕                              │  │
│  │                                                    │  │
│  │ (OCR text displayed as fallback)                   │  │
│  │ මාතාව සියලු දේවතාවුන්ගේ ගුණ ගීතය මෙසේ දැක්වේ..."  │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ⚠️ AI extraction failed — using OCR text                │
│  [🔄 Retry Extraction]                                   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 7.2 Transliteration Failed — Transliteration Panel

```
┌──────────────────────────────────────────────────────────┐
│  ✏️ Exact Letter Transliteration                         │
│  ┌────────────────────────────────────────────────────┐  │
│  │ [Unavailable] ✕                                    │  │
│  │                                                    │  │
│  │                                                    │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ⚠️ Transliteration unavailable — enter manually         │
│  [🔄 Retry]                                              │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 7.3 Network Error — Section Load

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│           ⚠️                                                │
│                                                             │
│    Failed to load section                                   │
│                                                             │
│    Error: Network request failed                            │
│                                                             │
│    [Retry]  [Skip to next section]                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 7.4 Source Text Update Failed

```
┌─────────────────────────────────────────────────────────────┐
│  Toast notification (top-right):                            │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ⚠️ Failed to save source text changes                │   │
│  │ ████████████████████░░░░░░ (progress bar)            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Auto-dismiss after 5s                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Micro-interactions

### 8.1 New Timing Guidelines

| Interaction                      | Duration      | Easing      |
| -------------------------------- | ------------- | ----------- |
| Shared zoom smooth scale         | 150ms         | ease        |
| Source text font scale with zoom | 150ms         | ease        |
| Confidence badge appear          | 200ms         | ease-out    |
| Extraction status transition     | 300ms         | ease-in-out |
| Regenerate button pulse          | 600ms         | ease-in-out |
| Transliteration loading dots     | 1.5s cycle    | linear      |
| Bidirectional sync indicator     | 200ms         | ease-out    |
| Panel collapse/expand            | 300ms         | ease-in-out |
| Skeleton shimmer                 | 1.5s infinite | linear      |

### 8.2 CSS Transition Classes

```css
/* Source text font scaling with zoom */
.source-text-content {
  transition: font-size 150ms ease;
}

/* Confidence badge appearance */
.confidence-badge-enter {
  opacity: 0;
  transform: scale(0.8);
}
.confidence-badge-active {
  opacity: 1;
  transform: scale(1);
  transition:
    opacity 200ms ease-out,
    transform 200ms ease-out;
}

/* Extraction status indicator */
.extraction-status {
  transition:
    color 300ms ease-in-out,
    background-color 300ms ease-in-out;
}

/* Regenerate button pulse */
@keyframes regenerate-pulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(37, 99, 235, 0.4);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(37, 99, 235, 0);
  }
}
.regenerate-btn-stale {
  animation: regenerate-pulse 600ms ease-in-out;
}

/* Transliteration loading dots */
@keyframes loading-dots {
  0%,
  20% {
    content: ".";
  }
  40% {
    content: "..";
  }
  60%,
  100% {
    content: "...";
  }
}

/* Panel collapse/expand */
.panel-content {
  overflow: hidden;
  transition:
    max-height 300ms ease-in-out,
    opacity 300ms ease-in-out;
}

/* Sync indicator flash */
@keyframes sync-flash {
  0% {
    background-color: transparent;
  }
  50% {
    background-color: rgba(37, 99, 235, 0.1);
  }
  100% {
    background-color: transparent;
  }
}
.sync-indicator {
  animation: sync-flash 200ms ease-out;
}
```

---

## 9. Accessibility

### 9.1 Keyboard Navigation

| Key               | Context              | Action                                  |
| ----------------- | -------------------- | --------------------------------------- |
| `Tab`             | Anywhere             | Move focus through interactive elements |
| `Shift+Tab`       | Anywhere             | Move focus backwards                    |
| `Enter` / `Space` | Extract button       | Trigger AI extraction                   |
| `Enter` / `Space` | Regenerate button    | Trigger regeneration                    |
| `Enter` / `Space` | Source text textarea | Edit source text                        |
| `Escape`          | Source text textarea | Blur, discard changes                   |
| `Ctrl+Enter`      | Translation editor   | Submit translation                      |
| `+` / `-`         | Image area           | Zoom in/out                             |
| `0`               | Image area           | Reset zoom to 100%                      |
| `?`               | Anywhere             | Toggle keyboard shortcuts help          |

### 9.2 ARIA Attributes

```html
<!-- Source text panel -->
<div role="region" aria-label="Source text panel">
  <div aria-live="polite" aria-atomic="true">
    <!-- Extraction status announcements -->
    <span>AI extraction complete. Confidence: 94%</span>
    <span>AI extraction failed. Using OCR text.</span>
    <span>AI extraction in progress...</span>
  </div>
  <label for="source-text-input">Source text</label>
  <textarea id="source-text-input" aria-describedby="source-text-status">
    <!-- editable source text -->
  </textarea>
  <span id="source-text-status" class="sr-only"> AI extracted text, confidence 94% </span>
</div>

<!-- Transliteration panel -->
<div role="region" aria-label="Exact letter transliteration panel">
  <div aria-live="polite" aria-atomic="true">
    <!-- Transliteration status announcements -->
    <span>AI transliteration generated</span>
    <span>Transliteration unavailable. Enter manually.</span>
    <span>Generating transliteration...</span>
  </div>
  <label for="exact-letter-input">Exact letter transliteration</label>
  <input id="exact-letter-input" aria-describedby="exact-letter-status" />
  <span id="exact-letter-status" class="sr-only"> AI generated transliteration </span>
</div>

<!-- Confidence badge -->
<span role="status" aria-label="Confidence: 94 percent, high quality">
  <span aria-hidden="true">94%</span>
  <span class="sr-only">94 percent confidence, high quality</span>
</span>

<!-- Extraction status indicator -->
<div role="status" aria-label="Extraction complete">
  <span aria-hidden="true">●</span>
</div>

<!-- Regenerate button -->
<button aria-label="Regenerate AI extraction for this section">Regenerate</button>

<!-- Zoom controls -->
<div role="group" aria-label="Zoom controls">
  <button aria-label="Zoom out" aria-describedby="zoom-level">−</button>
  <span id="zoom-level" aria-live="polite">100%</span>
  <button aria-label="Zoom in">+</button>
  <button aria-label="Reset zoom to 100%">⟳</button>
</div>
```

### 9.3 Screen Reader Announcements

| Event                     | Announcement                                      |
| ------------------------- | ------------------------------------------------- |
| Section loaded            | "Section loaded: Page 3, Section 2"               |
| AI extraction complete    | "AI extraction complete. Confidence: 94 percent." |
| AI extraction failed      | "AI extraction failed. Using OCR text."           |
| AI extraction started     | "AI extraction in progress..."                    |
| Transliteration generated | "AI transliteration generated"                    |
| Transliteration failed    | "Transliteration unavailable. Enter manually."    |
| Source text updated       | "Source text updated"                             |
| Zoom changed              | "Zoom: 120 percent"                               |
| Regenerate clicked        | "Regenerating extraction..."                      |

---

## 10. Implementation Notes

### 10.1 Component File Structure (Updated)

```
apps/web/app/translate/
├── page.tsx                    # Main translate page (Client Component)
├── TranslateTab.tsx            # Translate tab content (UPDATED)
├── HistoryTab.tsx              # History tab content
├── StatsTab.tsx                # Stats tab content
├── TranslateFilters.tsx        # Filter bar component
├── components/
│   ├── SourceTextPanel.tsx     # Source text (UPDATED — AI/OCR toggle, zoom, editable)
│   ├── TransliteratePanel.tsx  # NEW — Exact letter transliteration panel
│   ├── ExtractionStatusBadge.tsx # NEW — Confidence badge (green/yellow/red)
│   ├── TranslationEditor.tsx  # Textarea + submit
│   ├── DraftSaveIndicator.tsx  # "Draft saved" feedback
│   ├── SectionImageDisplay.tsx # Zoomable section image (UPDATED — shared zoom)
│   ├── PreviousSubmission.tsx  # My previous submission panel
│   ├── ApprovedTranslation.tsx # Approved translation display
│   ├── HistoryItem.tsx         # Single history row
│   ├── TranslatorStatsRow.tsx # Expandable translator stats row
│   ├── PageGrid.tsx            # Per-page breakdown grid
│   ├── LanguageCards.tsx       # Per-language breakdown cards
│   └── ProgressBar.tsx         # Animated progress bar
```

### 10.2 Custom Hooks (Updated)

```
apps/web/hooks/
├── useTranslationFilters.ts   # URL-synced filter state
├── useTranslationDraft.ts     # Auto-save draft logic
├── useInfiniteScroll.ts       # IntersectionObserver for infinite scroll
├── useTabState.ts             # Tab switching with URL persistence
├── useExtraction.ts           # NEW — AI extraction status polling
├── useTransliteration.ts      # NEW — Transliteration generation + cache
└── useSourceTextSync.ts       # NEW — Bidirectional sync logic
```

### 10.3 Updated TranslateTab.tsx Structure

```typescript
// State lifted to TranslateTab
const [zoom, setZoom] = useState(100)
const [sourceText, setSourceText] = useState("")
const [exactLetter, setExactLetter] = useState("")
const [extractionStatus, setExtractionStatus] = useState<"extracted" | "pending" | "failed" | null>(null)
const [confidence, setConfidence] = useState<number | null>(null)

// Layout: two-row grid
<div style={styles.body}>
  {/* Top row: Image + Source Text */}
  <div style={styles.topRow}>
    <SectionImageDisplay zoom={zoom} onZoomChange={setZoom} />
    <SourceTextPanel
      originalText={section.originalText}
      aiExtractedText={section.aiExtractedText}
      extractionStatus={extractionStatus}
      confidence={confidence}
      zoom={zoom}
      onSourceTextChange={handleSourceTextChange}
      isEditor={isEditor}
      onExtract={handleExtract}
    />
  </div>

  {/* Bottom row: Transliteration + Translation */}
  <div style={styles.bottomRow}>
    <TransliteratePanel
      sourceText={sourceText}
      exactLetter={exactLetter}
      onExactLetterChange={setExactLetter}
      sectionId={section.id}
      targetScript={section.book.targetLanguage}
    />
    <TranslationEditor
      translatedText={translatedText}
      onTranslatedTextChange={updateText}
    />
  </div>
</div>
```

### 10.4 Updated SourceTextPanel.tsx Interface

```typescript
interface SourceTextPanelProps {
  originalText: string | null
  aiExtractedText: string | null
  extractionStatus: "extracted" | "pending" | "failed" | null
  confidence: number | null
  zoom: number
  onSourceTextChange?: (text: string) => void // bidirectional sync
  isEditor?: boolean
  bookId?: string
  pageNumber?: number
  onExtract?: () => void // editor-only
}
```

### 10.5 New TransliteratePanel.tsx Interface

```typescript
interface TransliteratePanelProps {
  sourceText: string
  exactLetter: string
  onExactLetterChange: (text: string) => void
  sectionId: string
  targetScript: string
}
```

### 10.6 Shared Zoom State

```typescript
// In TranslateTab.tsx
const [zoom, setZoom] = useState(100)

// Both components receive zoom as prop
<SectionImageDisplay zoom={zoom} onZoomChange={setZoom} />
<SourceTextPanel zoom={zoom} ... />

// Source text font scales proportionally
const fontSize = 14 * (zoom / 100)
```

### 10.7 Performance Considerations

- **Lazy loading**: Tab content loaded only when tab is active (first visit)
- **Image lazy loading**: Section images use `loading="lazy"` attribute
- **Debounced source text sync**: 500ms debounce prevents excessive API calls on source text edits
- **React Query**: Background refetch on tab focus, stale-while-revalidate
- **Debounced auto-save**: 5s debounce prevents excessive draft API calls
- **Cursor-based pagination**: Avoids skip/limit performance issues
- **Redis caching**: 30s TTL for expensive stats aggregations
- **Skeleton screens**: Perceived performance improvement for loading states
- **Extraction polling**: Exponential backoff (2s, 4s, 8s) to avoid hammering API
- **Transliteration cache**: React Query staleTime: 60s for transliterations

---

## 11. Related Files

- `specs/business-analysis/20260706-1300-source-text-modifications.md` — User stories (US-ST-1 through US-ST-6)
- `specs/architecture/20260706-1300-source-text-modifications.md` — Technical architecture
- `specs/architecture/20260706-1200-translation-page-redesign.md` — Previous architecture spec
- `specs/ux/ui-design.md` — Updated UI/UX design (Translation Interface section)
- `specs/ux/20260706-1200-translation-page-redesign.md` — Previous UX spec
