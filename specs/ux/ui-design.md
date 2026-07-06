# Maha Pothana — UI/UX Design

## Design Principles

- **Role-aware interface** — UI adapts based on Editor/Translator roles
- **Canvas-first interaction** — Konva.js provides interactive overlay for section editing
- **Progressive disclosure** — Complex features revealed as needed, not all at once
- **Context-rich translation** — Translators always see surrounding page context

## Layout Structure

### Global Layout

```
┌──────────────────────────────────────────────────┐
│  Header                                           │
│  [Logo] [Dashboard] [Books] [Translate] [👤 User] │
├──────────────────────────────────────────────────┤
│                                                    │
│              Main Content Area                     │
│                                                    │
└──────────────────────────────────────────────────┘
```

- Header shows different nav items based on role
- Editor sees: Dashboard, Books (My Books, Upload)
- Translator sees: Dashboard, Translate
- Super Admin sees: Dashboard, Books, Translate, Admin

### Book Console Layout (Editor)

```
┌──────────────────────────────────────────────────┐
│  ← Back to Books  Book Title          [Settings]  │
├──────────────┬───────────────────────────────────┤
│              │                                    │
│  Page List   │     Page Viewer / Editor           │
│  ┌────────┐  │     ┌─────────────────────────┐    │
│  │ p.1 ✅ │  │     │                         │    │
│  │ p.2 ⏳ │  │     │   Page Image with        │    │
│  │ p.3 ✅ │  │     │   Konva Overlay          │    │
│  │ p.4 ✅ │  │     │   (Section Rectangles)   │    │
│  │ p.5 ❌ │  │     │                         │    │
│  │ p.6 ✅ │  │     └─────────────────────────┘    │
│  └────────┘  │                                    │
│              ├───────────────────────────────────┤│
│   Filter:    │  Section Editor (sidebar)          │
│   [All] 🔽  │  Type: [Paragraph 🔽]              │
│   Sort: 🔽   │  Position: x:120 y:45 w:400 h:60  │
│              │  [Delete] [Confirm All]            │
└──────────────┴───────────────────────────────────┘
```

<<<<<<< Updated upstream
### Translation Page Layout
=======
### Page Editor Layout (Detailed)

```
┌──────────────────────────────────────────────────────────────┐
│  ← Back to Book  Page 5  [🔵 PENDING]                       │
├──────────────────────────────────────────────────────────────┤
│  Toolbar                                                      │
│  ┌──────────┐ ┌──────┐ ┌──────────────┐ ┌────┐ ┌────┐       │
│  │📐 Add    │ │ 🗑   │ │ Type:Paragraph▼│ │ ↩  │ │ ↪  │       │
│  │ Section  │ │Delete│ │               │ │Undo│ │Redo│       │
│  └──────────┘ └──────┘ └──────────────┘ └────┘ └────┘       │
│  ┌──────────┐        ┌──┐ ┌─────┐ ┌──┐ ┌────────────────┐   │
│  │✨ Detect │        │ − │ │100% │ │ + │ │ ✓ Confirm      │   │
│  │ Sections │        └──┘ └─────┘ └──┘ │   Sections      │   │
│  └──────────┘                          └────────────────┘   │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│   ┌────────────────────────────────────────────────┐         │
│   │           Canvas Area                          │         │
│   │                                                │         │
│   │   ┌──────────────────────────────────┐         │         │
│   │   │  Page Image (loaded via presigned │         │         │
│   │   │  URL, scales to fit container)    │         │         │
│   │   │                                  │         │         │
│   │   │  ┌─────┐   ┌──────────┐         │         │         │
│   │   │  │HEADER│   │PARAGRAPH │         │         │         │
│   │   │  └─────┘   └──────────┘         │         │         │
│   │   │            ┌──────────────────┐  │         │         │
│   │   │            │PARAGRAPH         │  │         │         │
│   │   │            └──────────────────┘  │         │         │
│   │   │                         ┌─────┐  │         │         │
│   │   │                         │FOOTN│  │         │         │
│   │   │                         └─────┘  │         │         │
│   │   └──────────────────────────────────┘         │         │
│   │                                                │         │
│   └────────────────────────────────────────────────┘         │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### Translation Page Layout (Redesigned)

The translation page uses a **tabbed layout** with three tabs: Translate, History, and Stats. Filters are persisted in URL query params and are independent between tabs. The Translate Tab uses a **two-row, four-panel design**: top row pairs image + source text (shared zoom), bottom row pairs exact letter transliteration + translation.
>>>>>>> Stashed changes

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ← Dashboard   Book: "Gaha Ulela"   Page 3   [👤 Kamal Perera]        │
├─────────────────────────────────────────────────────────────────────────┤
│  Filters: [Language ▼ Sinhala] [Page ▼ All] [Status ▼ All] [✕]        │
├─────────────────────────────────────────────────────────────────────────┤
│  [ Translate ]  [ History ]  [ Stats* ]                                │
│  * Stats tab visible to editors only                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─ TRANSLATE TAB (default) ─────────────────────────────────────────┐ │
│  │                                                                     │ │
│  │  ┌─ TOP ROW: Image + Source Text (shared zoom) ─────────────────┐ │ │
│  │  │                                                                │ │ │
│  │  │  ┌──────────────────────────┬──────────────────────────────┐  │ │ │
│  │  │  │                          │                              │  │ │ │
│  │  │  │  Section Image           │  📄 Source Text              │  │ │ │
│  │  │  │  ┌────────────────────┐  │  ┌────────────────────────┐  │  │ │ │
│  │  │  │  │                    │  │  │ [AI Extracted] 94% ●    │  │  │ │ │
│  │  │  │  │  [CROPPED SECTION] │  │  │                        │  │  │ │ │
│  │  │  │  │  (drag to pan)     │  │  │ මාතාව සියලු දේවතාවුන්   │  │  │ │ │
│  │  │  │  │                    │  │  │ ගේ ගුණ ගීතය මෙසේ      │  │  │ │ │
│  │  │  │  │                    │  │  │ දැක්වේ..."              │  │  │ │ │
│  │  │  │  │                    │  │  │ (editable, scales w/zoom)│  │  │ │ │
│  │  │  │  └────────────────────┘  │  └────────────────────────┘  │  │ │ │
│  │  │  │                          │  [Extract] [Regenerate]      │  │ │ │
│  │  │  │  [−] 100% [+] [⟳]      │                              │  │ │ │
│  │  │  └──────────────────────────┴──────────────────────────────┘  │ │ │
│  │  └────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                     │ │
│  │  ┌─ BOTTOM ROW: Transliteration + Translation ───────────────────┐ │ │
│  │  │                                                                │ │ │
│  │  │  ┌──────────────────────────┬──────────────────────────────┐  │ │ │
│  │  │  │                          │                              │  │ │ │
│  │  │  │  ✏️ Exact Letter          │  📝 Your Translation *       │  │ │ │
│  │  │  │  Transliteration          │                              │  │ │ │
│  │  │  │  ┌────────────────────┐  │  ┌────────────────────────┐  │  │ │ │
│  │  │  │  │ [AI Generated] ●   │  │  │ මාතාවගේ සියලු දේවතාවුන්│  │  │ │ │
│  │  │  │  │                    │  │  │ ගේ ගුණ ගීතය මෙසේ      │  │  │ │ │
│  │  │  │  │ මාතා → माता        │  │  │ දැක්වේ..."              │  │  │ │ │
│  │  │  │  │ (editable input)   │  │  │ (auto-resize textarea)  │  │  │ │ │
│  │  │  │  └────────────────────┘  │  └────────────────────────┘  │  │ │ │
│  │  │  │  [🔄 Regenerate]         │  💾 Draft saved ✓            │  │ │ │
│  │  │  └──────────────────────────┴──────────────────────────────┘  │ │ │
│  │  └────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                     │ │
│  │  [Skip]  [Submit Translation]            Page 3 of 12 sections     │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─ HISTORY TAB ─────────────────────────────────────────────────┐ │
│  │  Filters: [Language ▼] [Page ▼] [Status ▼] [✕]              │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │ [thumb] Page 3, Sec 2  │  "මාතාව සියලු දේවතාවු..."  │ │ │
│  │  │                         │  ✅ APPROVED — Jul 5, 2:30 PM  │ │ │
│  │  ├─────────────────────────┼────────────────────────────────┤ │ │
│  │  │ [thumb] Page 1, Sec 4  │  "සිංහල භාෂාවෙන්..."          │ │ │
│  │  │                         │  ⏳ PENDING — Jul 6, 10:00 AM  │ │ │
│  │  ├─────────────────────────┼────────────────────────────────┤ │ │
│  │  │ [thumb] Page 5, Sec 1  │  "පාඨකයාගේ අදහස්..."          │ │ │
│  │  │                         │  ❌ REJECTED — Jul 4, 3:15 PM  │ │ │
│  │  ├─────────────────────────┼────────────────────────────────┤ │ │
│  │  │           ── Loading more... ──                          │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─ STATS TAB (editors only) ───────────────────────────────────┐ │
│  │                                                               │ │
│  │  Translation Progress                                        │ │
│  │  ████████████████░░░░░░░░  37.5%  (45/120 sections)         │ │
│  │  ✅ Approved: 45  ⏳ Pending: 12  🔄 In Progress: 8         │ │
│  │                                                               │ │
│  │  Per-Language Breakdown                                      │ │
│  │  ┌────────────┬──────────┬──────────┬─────────┐             │ │
│  │  │ Language   │ Done     │ Total    │ %       │             │ │
│  │  ├────────────┼──────────┼──────────┼─────────┤             │ │
│  │  │ Sinhala    │ 45       │ 120      │ 37.5%   │             │ │
│  │  │ Tamil      │ 20       │ 120      │ 16.7%   │             │ │
│  │  └────────────┴──────────┴──────────┴─────────┘             │ │
│  │                                                               │ │
│  │  Per-Page Breakdown                                          │ │
│  │  ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐         │ │
│  │  │  1  │  2  │  3  │  4  │  5  │  6  │  7  │  8  │ ...     │ │
│  │  │ 🟢  │ 🟡  │ 🟢  │ ⬜  │ 🟡  │ ⬜  │ ⬜  │ ⬜  │         │ │
│  │  │100% │ 50% │100% │ 0%  │ 25% │ 0%  │ 0%  │ 0%  │         │ │
│  │  └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘         │ │
│  │                                                               │ │
│  │  Translator Performance                                     │ │
│  │  ┌──────────┬──────────┬──────────┬──────────┬────────┐     │ │
│  │  │ Name     │ Assigned │ Approved │ Rejected │ Rate   │     │ │
│  │  ├──────────┼──────────┼──────────┼──────────┼────────┤     │ │
│  │  │ Kamal P. │ 30       │ 25       │ 3        │ 89.3%  │     │ │
│  │  │ Priya S. │ 25       │ 20       │ 4        │ 83.3%  │     │ │
│  │  └──────────┴──────────┴──────────┴──────────┴────────┘     │ │
│  └───────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────┘
```

## Key Interactions

### 1. Section Annotation Editor (Konva.js)

**States:**

- **Loading** — Skeleton placeholder while page image loads
- **Detecting** — Spinner overlay with "Detecting sections..." text
- **Edit mode** — Colored rectangles overlaid on page image:
  - Header = blue
  - Paragraph = green
  - Footnote = orange
  - Page Number = gray
  - Other = purple
- **Selected state** — Selected rectangle has thicker border + resize handles at corners/edges
- **Hover state** — Rectangle highlights with slight opacity change + tooltip showing type
- **Empty state** — "No sections detected. Draw rectangles manually or retry detection."
- **Error state** — "Detection failed. [Retry]" button

**Interactions:**

- Click rectangle → select it (show properties in sidebar)
- Drag rectangle → move it
- Drag corner handle → resize
- Delete key / trash icon → remove selected rectangle
- Click empty area → deselect current
- Draw new: click "Add Section" button, then click-drag on canvas
- Double-click rectangle → edit type selector
- Scroll wheel → zoom in/out of canvas
- Pan: spacebar + drag to pan around zoomed canvas

**Responses:**

- Rectangle changes color briefly on successful action
- Snap-to-grid when resizing (optional, toggleable)
- Undo/Redo support via Ctrl+Z / Ctrl+Shift+Z

<<<<<<< Updated upstream
### 2. Translation Interface
=======
- Stroke color matches fill color
- Stroke width: 1px (unselected), 2px white (selected)
- Type label text: 11px bold, same color as fill, positioned at top-left of rectangle with 4px offset

#### Toolbar Icons & Controls

| #   | Control          | Type           | Icon/Text                              | Behavior                                                              |
| --- | ---------------- | -------------- | -------------------------------------- | --------------------------------------------------------------------- |
| 1   | Add Section      | Toggle button  | `[📐 Add Section]` / `[✕ Cancel Draw]` | Toggles draw mode. Active state: primary color background             |
| 2   | Delete           | Action button  | `[🗑 Delete]`                          | Deletes selected section. Disabled when no selection                  |
| 3   | Type Selector    | Dropdown       | `[Type: PARAGRAPH ▼]`                  | Only visible when section selected. Changes section type              |
| 4   | Undo             | Action button  | `[↩]`                                  | Reverses last action. Disabled when undo stack empty                  |
| 5   | Redo             | Action button  | `[↪]`                                  | Reapplies last undone action. Disabled when redo stack empty          |
| 6   | Detect Sections  | Action button  | `[✨ Detect Sections]`                 | Triggers ML-based section detection. Disabled during detection/saving |
| 7   | Zoom Out         | Action button  | `[−]`                                  | Decreases zoom by 10% (min 50%)                                       |
| 8   | Zoom Level       | Label          | `100%`                                 | Displays current zoom percentage                                      |
| 9   | Zoom In          | Action button  | `[+]`                                  | Increases zoom by 10% (max 300%)                                      |
| 10  | Confirm Sections | Primary action | `[✓ Confirm Sections]`                 | Saves all sections to API. Shows spinner while saving                 |

#### Keyboard Shortcuts

| Key                       | Context        | Action                                      |
| ------------------------- | -------------- | ------------------------------------------- |
| `Delete` / `Backspace`    | Canvas focused | Delete selected section                     |
| `Ctrl+Z`                  | Anywhere       | Undo                                        |
| `Ctrl+Shift+Z` / `Ctrl+Y` | Anywhere       | Redo                                        |
| `Escape`                  | Canvas focused | Deselect current section / Cancel draw mode |
| `+` / `=`                 | Canvas focused | Zoom in                                     |
| `-`                       | Canvas focused | Zoom out                                    |
| `Ctrl+S`                  | Anywhere       | Save/confirm sections                       |
| `D`                       | Canvas focused | Toggle draw mode                            |

- Keyboard shortcuts only fire when the canvas area is focused or no text input is active
- Tooltips on toolbar buttons show the associated shortcut (e.g., "Delete (Delete)")
- A small `[?]` help button in the toolbar can toggle a keyboard shortcut cheat sheet overlay

#### Undo/Redo System

- Internal history stack (array of section snapshots) kept in component state
- Each undoable action (add, delete, move, resize, type change) pushes current state to undo stack
- Redo stack accumulates undone states; cleared when a new action is performed
- Stacks are cleared when sections are confirmed/saved to API
- Maximum stack depth: 50 actions (to prevent memory issues)

#### Draw Mode

1. User clicks "Add Section" button → button highlights, cursor changes to crosshair
2. User clicks and drags on canvas → dashed preview rectangle follows cursor
3. On mouseup, if rectangle area > 10x10px, new section is created with type PARAGRAPH
4. New section is auto-selected with Transform handles
5. Draw mode automatically exits after successful draw
6. User can press Escape or click "Cancel Draw" to exit without drawing

### 2. Confirmation Flow

1. User modifies sections (add, delete, move, resize, change type)
2. User clicks "Confirm Sections" (or presses Ctrl+S)
3. Button shows spinner, all edit controls disabled
4. Frontend sends raw array of sections `[{ id, sectionOrder, type, x, y, width, height }]` via `PUT /api/pages/{pageId}/sections`
5. **On success**: Toast "Sections confirmed!" → Canvas enters read-only confirmation state → "Re-detect Sections" button appears
6. **On failure**: Error toast "Failed to save sections" + [Retry] button

### 3. Section Detection Flow

1. User clicks "Detect Sections" (or detection auto-runs on page load)
2. Loading overlay appears: "Detecting sections..." with spinner
3. Backend runs ML detection (LayoutParser) asynchronously via Celery
4. On completion, frontend refetches page data → sections appear as colored rectangles
5. **On failure**: Error state "Detection failed" + [Retry Detection] button. Page status `DETECTION_FAILED`
6. After initial confirmation, "Re-detect Sections" button is available for re-running detection

### 4. Translation Interface (Redesigned)
>>>>>>> Stashed changes

#### Tab System

| Tab | Label | Visibility | Default |
| --- | --- | --- | --- |
| Translate | "Translate" | All roles | Yes |
| History | "History" | All roles | No |
| Stats | "Stats" | Editors, Super Admin only | No |

- Active tab indicated by underline + bold text
- Tab state persisted in URL: `?tab=translate`, `?tab=history`, `?tab=stats`
- Clicking a tab loads its content lazily (first visit triggers fetch)

#### Translate Tab States

| State | Visual | Description |
| --- | --- | --- |
| **Idle** | Empty state with "Select a section to translate" message + auto-loads first section on mount | No section loaded yet |
| **Loading** | Skeleton placeholder for all four panels (image, source text, transliteration, translation), spinner overlay | Section data loading |
| **Ready** | Two-row layout: image + source text top, transliteration + translation bottom | Section loaded, all panels ready |
| **Ready (AI text)** | Source text panel shows AI-extracted text with green confidence badge (≥0.9) | AI extraction available |
| **Ready (OCR text)** | Source text panel shows OCR text with gray "OCR" badge | No AI extraction, using fallback |
| **Extracting** | Source text panel shows "Extracting..." with OCR text as fallback, spinner | AI extraction in progress |
| **Extraction failed** | Source text panel shows OCR text with red "Extraction failed" badge + "Retry" button | AI extraction failed |
| **Has draft** | Translation editor prefilled with saved draft text, "Draft saved ✓" indicator | Existing draft loaded from backend |
| **Has transliteration** | Exact letter panel shows AI-generated transliteration with green badge | Transliteration cached |
| **Generating transliteration** | Exact letter panel shows "Generating..." spinner | Transliteration in progress |
| **Transliteration unavailable** | Exact letter panel shows "Transliteration unavailable — enter manually" | Transliteration failed |
| **Has previous submission** | "My previous submission" panel below editor with pending text + "Edit" button | Translator already submitted, pending review |
| **Has approved translation** | "Approved Translation" panel shows the approved text (read-only) | Section already has an approved translation |
| **Saving** | Spinner on Submit button, all inputs disabled | Translation being saved |
| **Saved** | Green toast "Translation saved!" + auto-loads next section | Save succeeded |
| **Complete** | Centered "All sections translated!" with checkmark icon | Queue empty for current filters |
| **Error** | Error message + [Retry] button | API call failed |
| **No sections** | "No sections match your filters. Try adjusting the filters." | Filters return empty results |

#### Translate Tab Interactions

- **Auto-load**: On mount, fetches `GET /api/sections/next` with current filters and loads the section
- **Skip**: Calls `GET /api/sections/next` again, skipping current section
- **Submit**: POSTs translation, deletes draft, invalidates queries, loads next section
- **Zoom**: `+`/`-` buttons adjust zoom (50%–300%), displayed as percentage. **Image and source text share the same zoom level.** Source text font scales proportionally: `fontSize: 14 * (zoom / 100)`
- **Reset zoom**: ⟳ button returns to 100%. Keyboard shortcut: `0` when image area focused
- **Drag-to-pan**: Click and drag on image to pan at any zoom level (existing behavior preserved)
- **Source text editing**: Source text panel is editable (textarea). Changes auto-sync with a 500ms debounce via `PUT /api/sections/{id}/source-text`
- **Bidirectional sync**: Editing source text invalidates cached transliterations (shows "Regenerate" on transliteration panel). Editing transliteration marks it as "manual" (does not modify source text)
- **AI extraction**: Editors see "Extract Text" button when no AI extraction exists. Clicking triggers `POST /api/sections/{id}/extract`. Status polls every 2s until complete
- **Regenerate**: "Regenerate" button re-runs extraction or transliteration. Shows confirmation dialog before proceeding
- **Auto-save**: Text input debounced 5s, saves draft via `POST /api/translations/draft`
- **Draft indicator**: Brief "Draft saved ✓" toast after each auto-save
- **Beforeunload**: If `isDirty` is true, browser shows native "unsaved changes" warning
- **Keyboard**: `Ctrl+Enter` submits, `Escape` skips, `+`/`-` zoom, `0` reset zoom
- **Page context**: Prev/Next buttons show page number, click loads sections from adjacent pages

#### AI Extraction Status Indicators

| Badge | Color | Meaning |
| --- | --- | --- |
| `[AI Extracted] 94% ●` | Green (`#16A34A`) | AI extraction complete, confidence ≥ 0.9 |
| `[AI Extracted] 78% ●` | Yellow (`#F59E0B`) | AI extraction complete, confidence ≥ 0.7 |
| `[AI Extracted] 45% ●` | Red (`#DC2626`) | AI extraction complete, confidence < 0.7 |
| `[OCR] ●` | Gray (`#94A3B8`) | No AI extraction, using OCR fallback |
| `[Extracting...] ●○○` | Blue animated | AI extraction in progress |
| `[Extraction failed] ✕` | Red (`#DC2626`) | AI extraction failed |

**Confidence threshold** is configurable by admin (default 0.7). Badge color is derived from the threshold setting.

#### Bidirectional Sync — Source Text ↔ Transliteration

```
Source Text Panel                          Transliteration Panel
┌────────────────────────────┐             ┌────────────────────────────┐
│ "මාතාව සියලු දේවතාවුන්ගේ"  │  ──edit──→  │ (cache invalidated)        │
│         ↑                  │             │ "Regenerate" button pulses │
│         │                  │             └────────────────────────────┘
│    (no sync from           │
│     transliteration)       │
└────────────────────────────┘

Rules:
1. Editing source text → invalidates cached transliterations
2. Editing transliteration → marks as "manual", does NOT modify source text
3. Source text is the source of truth; transliteration is derived
4. Manual transliteration overrides AI-generated result
```

#### Transliteration Panel States

| State | Visual | Description |
| --- | --- | --- |
| **AI Generated** | Green badge "[AI Generated] ●" + pre-filled text | Transliteration from AI, cached |
| **Generating** | Blue spinner "[Generating...] ●○○" + "Generating transliteration..." | Transliteration in progress |
| **Unavailable** | Red badge "[Unavailable] ✕" + empty field | Transliteration failed, enter manually |
| **Manual** | Gray badge "[Manual] ●" + user-typed text | Translator entered manually |
| **Stale** | Yellow badge "[Regenerate needed] ●" + previous text + pulsing "Regenerate" button | Cache invalidated by source text edit |

#### AI Extraction Flow (Editor)

1. Section loads → check `aiExtractedText`
2. If present → show with confidence badge
3. If absent → show OCR text with "Extract Text" button (editors only)
4. Editor clicks "Extract Text" → `POST /api/sections/{id}/extract`
5. Status indicator changes to "Extracting..." with polling
6. On success → update panel with AI text + confidence badge
7. On failure → show "Extraction failed" + "Retry" button
8. "Regenerate" button available after successful extraction (re-runs)

#### Transliteration Flow (Translator)

1. Section loads with AI extracted text → check for cached transliteration
2. If cached → pre-fill exact letter field with AI result
3. If not cached → show "Generate with AI" button
4. Translator clicks "Generate" → `POST /api/sections/{id}/transliterate`
5. Status changes to "Generating..." with spinner
6. On success → pre-fill field, mark as "AI Generated"
7. On failure → show "Transliteration unavailable — enter manually"
8. Translator can edit pre-filled result or type manually
9. Manual edits mark source as "manual" in `Translation.transliterationSource`

#### History Tab States

| State | Visual | Description |
| --- | --- | --- |
| **Loading** | Skeleton list (6 placeholder rows) | Initial fetch in progress |
| **Empty** | "No translations yet — start translating!" with link to Translate tab | No history entries match filters |
| **Has entries** | Scrollable list of history items | Data loaded |
| **Loading more** | Spinner at bottom of list | Infinite scroll fetching next page |
| **Error** | "Failed to load history. [Retry]" | API call failed |

#### History Tab Interactions

- **Infinite scroll**: Uses cursor-based pagination, fetches next page when scrolling near bottom
- **Click item**: Navigates to `/translate?section={sectionId}` (loads that section in Translate tab)
- **Filters**: Independent from Translate tab filters. Language, page, status filters applied on API call
- **Real-time updates**: Status badges update when editor approves/rejects (React Query refetch on focus)
- **Role-based**: Translators see only own translations; editors see all

#### History Item Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ ┌────────┐  Page 3, Section 2                                  │
│ │  📷    │  "මාතාව සියලු දේවතාවුන්ගේ ගුණ ගීතය..."           │
│ │  thumb │                                                     │
│ └────────┘  ✅ APPROVED  ·  Reviewed by Nimal Editor           │
│             Jul 5, 2026 at 2:30 PM                             │
└─────────────────────────────────────────────────────────────────┘
```

- Thumbnail: 48×48px cropped section image
- Status badge: colored pill (green=APPROVED, red=REJECTED, amber=PENDING)
- Truncated text: max 80 characters with ellipsis

#### Stats Tab States

| State | Visual | Description |
| --- | --- | --- |
| **Loading** | Skeleton cards (progress bar placeholder, grid placeholders) | Initial fetch |
| **Empty** | "No translation data yet. Sections need to be translated first." | Book has no translations |
| **Has data** | Dashboard with progress bar, language breakdown, page grid, translator table | Data loaded |
| **Error** | "Failed to load statistics. [Retry]" | API call failed |

#### Stats Tab Interactions

- **Auto-refresh**: React Query polls every 30s (aligned with Redis cache TTL)
- **Progress bar**: Animated fill on load, shows percentage + section counts
- **Page grid**: Color-coded cells (green=100%, yellow=partial, gray=0%), click a cell to filter history to that page
- **Language cards**: Click a language card to filter translate/history tabs to that language
- **Translator table**: Sortable columns (click header to sort), expandable rows show last 10 submissions
- **Collapse/expand**: Stats section can be collapsed to save space (remembered in localStorage)

#### Stats Tab Components

**Progress Bar:**
```
Translation Progress
████████████████░░░░░░░░░  37.5%
Approved: 45  ·  Pending: 12  ·  In Progress: 8  ·  Total: 120
```

**Per-Language Cards:**
```
┌──────────────────────┐  ┌──────────────────────┐
│  Sinhala (si)        │  │  Tamil (ta)          │
│  ████████░░  37.5%   │  │  ███░░░░░░░  16.7%   │
│  45 / 120 sections   │  │  20 / 120 sections   │
└──────────────────────┘  └──────────────────────┘
```

**Per-Page Grid:**
```
Page:  1    2    3    4    5    6    7    8    ...
       🟢   🟡   🟢   ⬜   🟡   ⬜   ⬜   ⬜
      100%  50% 100%  0%  25%  0%   0%   0%
```

**Translator Performance Table:**
```
┌──────────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
│ Name         │ Assigned │ Approved │ Rejected │ Rate     │ Avg Time │
├──────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ Kamal P.     │ 30       │ 25       │ 3        │ 89.3%    │ 4.2h     │
│ Priya S.     │ 25       │ 20       │ 4        │ 83.3%    │ 3.8h     │
│ Ravi M.      │ 10       │ —        │ —        │ —        │ —        │
└──────────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
```

- "—" displayed instead of 0% or N/A for zero-submission translators
- Click row to expand and show last 10 translation submissions
- Sortable by any column (click header, default: approval rate descending)

### 3. Book Upload

**States:**

- **Empty** — Drag-and-drop zone with dashed border + "Upload PDF" button
- **Dragging** — Zone highlights green
- **Uploading** — Progress bar with percentage + filename
- **Processing** — "Splitting pages..." with indeterminate progress
- **Complete** — Green checkmark + "Redirecting to console..." then auto-redirect
- **Error** — Duplicate: "This book already exists" + link to existing book
- **Error** — Invalid file: "Please upload a valid PDF"
- **Error** — Network: "Upload failed. [Retry]"

**Form fields:**

- Book Title (required)
- Author (required)
- Source Language (dropdown, required)
- Target Languages (multi-select, required — one or more languages to translate into)
- Description (optional, textarea)

### 4. Book Organization

- Drag-to-reorder pages in sidebar list
- Status badges: ✅ Completed, ⏳ In Progress, ❌ Not Started, 🔄 Processing
- Progress bar per book (compact): green/yellow/red fill
- Filter buttons: All | Completed | In Progress | Not Started
- Sort: Page Number | Progress %

### 5. Translation Review (Editor)

- Side-by-side comparison of all submitted translations per section
- Each translation card shows: translator name, timestamp, translated text, exact letter text (if provided)
- **Approve** button on each card (green) — editor can approve **multiple** translations if they convey the same meaning
- **Reject** button on each card (red) — editor can reject specific translations
- **Reject All** button — if all are rejected, section re-enters the translation pool for translators to retry
- **"Write your own"** text area for editor's version, using submitted translations as reference
- **Approved** translation marked with star badge
- **Rejected** translation marked with strikethrough and "Rejected" badge
- If all translations rejected, show: "All translations rejected. Translators will need to resubmit."
- Visual diff between original and approved translation

## Color Palette

```
Primary:    #2563EB (blue-600)
Success:    #16A34A (green-600)
Warning:    #F59E0B (amber-500)
Error:      #DC2626 (red-600)
Neutral:    #F8FAFC, #E2E8F0, #94A3B8, #475569, #0F172A

Section Types:
  Header:     #3B82F6 (blue-500)
  Paragraph:  #22C55E (green-500)
  Footnote:   #F97316 (orange-500)
  Page Number: #6B7280 (gray-500)
  Other:      #A855F7 (purple-500)
```

## Typography

- Font: Inter (system font stack fallback)
- Headings: 700 weight
- Body: 400 weight
- Code/monospace: JetBrains Mono (for text comparison)

## Responsive Breakpoints

<<<<<<< Updated upstream
- Mobile: < 768px — Stack layout, bottom sheet for sidebar
- Tablet: 768-1024px — Collapsible sidebar
- Desktop: > 1024px — Full layout as designed
=======
- **Mobile** (< 768px): Stack layout, bottom sheet for sidebar, simplified toolbar (icons only, labels hidden)
- **Tablet** (768–1024px): Collapsible sidebar, toolbar with icon+label for important actions
- **Desktop** (> 1024px): Full layout as designed

## Responsive Behavior — Page Editor

| Element            | Desktop (>1024px)               | Tablet (768–1024px)             | Mobile (<768px)                         |
| ------------------ | ------------------------------- | ------------------------------- | --------------------------------------- |
| Toolbar            | Full horizontal bar with labels | Two-row toolbar, labels visible | Single row, icons only, overflow scroll |
| Canvas             | Full width available            | Full width, slightly smaller    | Full width, min-height 300px            |
| Zoom controls      | Always visible                  | Always visible                  | Collapsed into expandable panel         |
| Type selector      | Inline in toolbar               | Inline in toolbar               | Modal/dropdown overlay on tap           |
| Sidebar properties | Right sidebar (if applicable)   | Bottom sheet                    | Bottom sheet                            |

## Responsive Behavior — Translation Page

| Element            | Desktop (>1024px)                           | Tablet (768–1024px)                       | Mobile (<768px)                             |
| ------------------ | ------------------------------------------- | ----------------------------------------- | ------------------------------------------- |
| Tab bar            | Horizontal tabs with labels                 | Horizontal tabs with labels               | Horizontal tabs, compact (icons + short labels) |
| Filters            | Inline horizontal row above tabs            | Collapsible row (tap to expand)           | Stacked vertically in a drawer             |
| Translate layout   | Two-row: image+source top, trans+edit bottom | Two-row, collapsible image panel     | Stacked: all four panels vertically        |
| Top row            | Side-by-side: image 50%, source text 50%    | Side-by-side, collapsible image           | Stacked: image on top, source text below   |
| Bottom row         | Side-by-side: exact letter 50%, translation 50% | Side-by-side, fixed height          | Stacked: exact letter above translation    |
| Section image      | 50% width top row, scrollable               | 40% width, collapsible                    | Full width, fixed height 240px             |
| Source text panel  | 50% top row, editable, font scales with zoom | 60% top row, scrollable                  | Full width, below image, fixed font        |
| Confidence badge   | Inline in panel header                      | Inline in panel header                    | Inline in panel header                     |
| Extract button     | Below source text panel                     | Below source text panel                   | Below source text panel                    |
| Exact letter panel | 50% bottom row, editable                    | 50% bottom row, fixed height              | Full width, above translation editor       |
| Translation editor | 50% bottom row, auto-resize textarea        | 50% bottom row, fixed height textarea     | Full width, min-height 120px               |
| Zoom controls      | Below image, always visible                 | Below image, always visible               | Inside image, overlay controls             |
| Page context       | Horizontal bar below editor                 | Horizontal bar below editor               | Compact: "Page X of Y" with swipe          |
| History list       | Full-width rows, side-by-side info          | Full-width rows, stacked info             | Stacked cards, full-width                  |
| Stats dashboard    | Full grid layout                            | 2-column grid                             | Single-column stack                        |
| Page grid          | Horizontal scroll with fixed cell size      | Horizontal scroll, smaller cells          | Wrap to multiple rows, tap to expand       |
| Translator table   | Full-width table with all columns           | Table with some columns hidden            | Card layout per translator                 |

## Accessibility

### Keyboard Navigation

- All canvas operations accessible via keyboard shortcuts
- Toolbar buttons focusable via Tab key
- Escape returns focus from canvas to toolbar
- Ctrl+S for save follows platform conventions

### Screen Reader Support

- Canvas is `role="application"` with `aria-label="Page section editor"`
- Each section rectangle has `aria-label` with type and position
- Status updates (detecting, saving, loading) announced via `aria-live="polite"` region
- Images use `alt` text describing page number

### Color Contrast

- Section type colors meet WCAG AA contrast against white backgrounds
- Type labels use bold font for readability
- Transform handles have white stroke for visibility on all section colors
- Error/success states use both color AND icon/text (not color alone)

### Translation Page Accessibility

- Tab bar uses `role="tablist"`, each tab uses `role="tab"` with `aria-selected`
- Tab panels use `role="tabpanel"` with `aria-labelledby` pointing to the tab
- Status badges use `aria-label` for screen readers (e.g., `aria-label="Approved"`)
- Progress bar uses `role="progressbar"` with `aria-valuenow`, `aria-valuemin`, `aria-valuemax`
- History items are focusable via Tab key, activated with Enter
- Filter dropdowns use native `<select>` for maximum screen reader compatibility
- Auto-save indicator uses `aria-live="polite"` to announce without interrupting
- Page grid cells have `aria-label` describing page number and completion percentage
- Translator table rows are expandable via Enter/Space key
- All images (section thumbnails, cropped images) have descriptive `alt` text
- Keyboard shortcuts documented in a help overlay (`?` key to toggle)
- Source text panel uses `role="region"` with `aria-label="Source text panel"`
- Source text textarea has `aria-describedby` pointing to extraction status text
- Extraction status announcements use `aria-live="polite"` (e.g., "AI extraction complete. Confidence: 94%")
- Transliteration panel uses `role="region"` with `aria-label="Exact letter transliteration panel"`
- Transliteration status announcements use `aria-live="polite"` (e.g., "AI transliteration generated")
- Confidence badge has `role="status"` with descriptive `aria-label` (e.g., "Confidence: 94 percent, high quality")
- Zoom controls use `role="group"` with `aria-label="Zoom controls"`
- Zoom level announcement uses `aria-live="polite"` (e.g., "Zoom: 120 percent")
- Extract button has `aria-label="Extract text from section image"`
- Regenerate button has `aria-label="Regenerate AI extraction for this section"`

### Translation Page Keyboard Shortcuts

| Key | Context | Action |
| --- | --- | --- |
| `Ctrl+Enter` | Translation editor | Submit translation |
| `Escape` | Translation editor / Source text | Blur input / Skip section |
| `+` / `=` | Image area focused | Zoom in (shared zoom) |
| `-` | Image area focused | Zoom out (shared zoom) |
| `0` | Image area focused | Reset zoom to 100% |
| `1` | Anywhere | Switch to Translate tab |
| `2` | Anywhere | Switch to History tab |
| `3` | Anywhere | Switch to Stats tab (editors only) |
| `?` | Anywhere | Toggle keyboard shortcuts help |

- Keyboard shortcuts only fire when no text input is focused or when the image area is focused
- Tooltips on zoom buttons show the associated shortcut (e.g., "Zoom in (+)")
- A small `[?]` help button in the toolbar can toggle a keyboard shortcut cheat sheet overlay

## Micro-interactions

- **Rectangle selection**: 150ms border width transition, snap
- **Draw preview**: Dashed outline follows cursor in real-time
- **Zoom**: Smooth scale transition (CSS `transform` on the Stage container)
- **Save success**: Brief green flash on the confirm button before showing checkmark
- **Error**: Subtle shake animation on the error element
- **Hover**: 150ms opacity transition on rectangle fill
- **Tab switching**: 200ms fade-in for tab content, subtle slide-up animation
- **Draft saved indicator**: Slide-in from right, 2s auto-dismiss with fade-out
- **History item hover**: 150ms background color transition, slight left border highlight
- **History item click**: Brief scale-down (0.98) press feedback before navigation
- **Progress bar fill**: 600ms ease-out animation on initial load and updates
- **Page grid cell hover**: 150ms scale-up to 1.1 with shadow, cursor pointer
- **Translator row expand**: 300ms height animation with content fade-in
- **Filter apply**: 150ms background flash on filter change confirmation
- **Skip button**: Subtle rotation animation on click (360° spin)
- **Submit button**: Progress dots animation during save ("Saving..." → ".  ." → ".. " → "...")
- **Empty state illustration**: Subtle floating animation (3s infinite ease-in-out)
- **Status badge**: Subtle pulse animation on status change (e.g., PENDING → APPROVED)
- **Infinite scroll loader**: Three-dot bouncing animation
- **Toast notifications**: Slide-in from top-right, 3s auto-dismiss with progress bar
- **Shared zoom**: 150ms smooth scale transition on image and source text font size simultaneously
- **Source text font scale**: 150ms transition when zoom changes, proportional to image zoom
- **Confidence badge appear**: 200ms scale-up from 0.8 to 1.0 with opacity fade-in
- **Extraction status transition**: 300ms color transition when status changes (pending → extracted → failed)
- **Regenerate button pulse**: 600ms ease-in-out box-shadow pulse when cache is invalidated
- **Transliteration loading dots**: 1.5s cycling animation ("Generating" → "Generating." → "Generating..")
- **Sync indicator flash**: 200ms blue background flash when source text syncs
- **Panel collapse/expand**: 300ms max-height animation with content fade-in
- **Bidirectional sync indicator**: Brief 200ms highlight on the panel that receives synced data
- **Extraction polling spinner**: Continuous rotation while polling extraction status
- **AI text reveal**: 300ms fade-in when OCR text transitions to AI text after extraction completes
>>>>>>> Stashed changes
