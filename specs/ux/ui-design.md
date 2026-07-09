# Maha Pothana — UI/UX Design

## Design Principles

- **Role-aware interface** — UI adapts based on Editor/Translator roles
- **Canvas-first interaction** — Konva.js provides interactive overlay for section editing
- **Progressive disclosure** — Complex features revealed as needed, not all at once
- **Context-rich translation** — Translators always see surrounding page context
- **Forgiving input** — Undo/redo, draw cancellation, and confirmation safeguards prevent data loss

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

## Detailed Interaction Patterns

### 1. Section Annotation Editor (Konva.js)

#### Image Loading

| State        | Visual                                                                                                  | Description                                             |
| ------------ | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| **Loading**  | Skeleton placeholder (aspect-ratio matching container) + spinner icon with "Loading page image..."      | While `HTMLImageElement` loads from presigned S3 URL    |
| **Loaded**   | Page image rendered as `<Rect fillPatternImage={imgElement}>` or `<Konva.Image>` covering full stage    | Image element stored in `useState` and passed to canvas |
| **No image** | Centered message: "No page image available" + subtitle "Upload a book and process it to see pages here" | When `pageImageUrl` is null/undefined                   |
| **Error**    | Centered message: "Failed to load page image" + [Retry] button                                          | When `img.onerror` fires                                |

#### Section Operations

| State         | Visual                                                                                                              | Description                           |
| ------------- | ------------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| **Empty**     | Canvas shows just the page image. Bottom overlay hint: "No sections yet. Click 'Detect Sections' or draw manually." | No sections loaded                    |
| **Detected**  | Colored rectangles overlaid on image with type labels                                                               | Sections loaded from API or detection |
| **Selected**  | Rectangle has thicker white border (2px), Transform handles at corners/edges, type selector appears in toolbar      | User clicks a rectangle               |
| **Hover**     | Rectangle opacity increases (fill becomes more opaque), cursor becomes pointer                                      | Mouse hovers over a rectangle         |
| **Drawing**   | Crosshair cursor, dashed preview rectangle follows mouse on drag, "Cancel Draw" button highlighted                  | Toggle draw mode active               |
| **Detecting** | Semi-transparent overlay with spinner + "Detecting sections..." message, all toolbar buttons disabled except zoom   | Detection API in progress             |
| **Saving**    | "Confirm Sections" button shows spinner, all edit buttons disabled                                                  | Save API in progress                  |

#### Section Type Color Scheme

| Type          | Hex Color              | Fill Opacity   | Label           | Description      |
| ------------- | ---------------------- | -------------- | --------------- | ---------------- |
| HEADER        | `#3B82F6` (blue-500)   | 25% (`40` hex) | `HEADER`        | Book/page titles |
| PARAGRAPH     | `#22C55E` (green-500)  | 25%            | `PARAGRAPH`     | Body text        |
| FOOTNOTE      | `#F97316` (orange-500) | 25%            | `FOOTNOTE`      | Footnotes        |
| IMAGE_CAPTION | `#A855F7` (purple-500) | 25%            | `IMAGE_CAPTION` | Image captions   |
| PAGE_NUMBER   | `#6B7280` (gray-500)   | 25%            | `PAGE_NUMBER`   | Page numbers     |
| OTHER         | `#8B5CF6` (violet-500) | 25%            | `OTHER`         | Miscellaneous    |

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

### 4. Translation Interface

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

### 4. Translation Interface

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

#### Tab System

| Tab       | Label       | Visibility                | Default |
| --------- | ----------- | ------------------------- | ------- |
| Translate | "Translate" | All roles                 | Yes     |
| History   | "History"   | All roles                 | No      |
| Stats     | "Stats"     | Editors, Super Admin only | No      |

- Active tab indicated by underline + bold text
- Tab state persisted in URL: `?tab=translate`, `?tab=history`, `?tab=stats`
- Clicking a tab loads its content lazily (first visit triggers fetch)

#### Translate Tab States

| State                           | Visual                                                                                                       | Description                                  |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------ | -------------------------------------------- |
| **Idle**                        | Empty state with "Select a section to translate" message + auto-loads first section on mount                 | No section loaded yet                        |
| **Loading**                     | Skeleton placeholder for all four panels (image, source text, transliteration, translation), spinner overlay | Section data loading                         |
| **Ready**                       | Two-row layout: image + source text top, transliteration + translation bottom                                | Section loaded, all panels ready             |
| **Ready (AI text)**             | Source text panel shows AI-extracted text with green confidence badge (≥0.9)                                 | AI extraction available                      |
| **Ready (OCR text)**            | Source text panel shows OCR text with gray "OCR" badge                                                       | No AI extraction, using fallback             |
| **Extracting**                  | Source text panel shows "Extracting..." with OCR text as fallback, spinner                                   | AI extraction in progress                    |
| **Extraction failed**           | Source text panel shows OCR text with red "Extraction failed" badge + "Retry" button                         | AI extraction failed                         |
| **Has draft**                   | Translation editor prefilled with saved draft text, "Draft saved ✓" indicator                                | Existing draft loaded from backend           |
| **Has transliteration**         | Exact letter panel shows AI-generated transliteration with green badge                                       | Transliteration cached                       |
| **Generating transliteration**  | Exact letter panel shows "Generating..." spinner                                                             | Transliteration in progress                  |
| **Transliteration unavailable** | Exact letter panel shows "Transliteration unavailable — enter manually"                                      | Transliteration failed                       |
| **Has previous submission**     | "My previous submission" panel below editor with pending text + "Edit" button                                | Translator already submitted, pending review |
| **Has approved translation**    | "Approved Translation" panel shows the approved text (read-only)                                             | Section already has an approved translation  |
| **Saving**                      | Spinner on Submit button, all inputs disabled                                                                | Translation being saved                      |
| **Saved**                       | Green toast "Translation saved!" + auto-loads next section                                                   | Save succeeded                               |
| **Complete**                    | Centered "All sections translated!" with checkmark icon                                                      | Queue empty for current filters              |
| **Error**                       | Error message + [Retry] button                                                                               | API call failed                              |
| **No sections**                 | "No sections match your filters. Try adjusting the filters."                                                 | Filters return empty results                 |

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

| Badge                   | Color              | Meaning                                  |
| ----------------------- | ------------------ | ---------------------------------------- |
| `[AI Extracted] 94% ●`  | Green (`#16A34A`)  | AI extraction complete, confidence ≥ 0.9 |
| `[AI Extracted] 78% ●`  | Yellow (`#F59E0B`) | AI extraction complete, confidence ≥ 0.7 |
| `[AI Extracted] 45% ●`  | Red (`#DC2626`)    | AI extraction complete, confidence < 0.7 |
| `[OCR] ●`               | Gray (`#94A3B8`)   | No AI extraction, using OCR fallback     |
| `[Extracting...] ●○○`   | Blue animated      | AI extraction in progress                |
| `[Extraction failed] ✕` | Red (`#DC2626`)    | AI extraction failed                     |

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

| State            | Visual                                                                             | Description                            |
| ---------------- | ---------------------------------------------------------------------------------- | -------------------------------------- |
| **AI Generated** | Green badge "[AI Generated] ●" + pre-filled text                                   | Transliteration from AI, cached        |
| **Generating**   | Blue spinner "[Generating...] ●○○" + "Generating transliteration..."               | Transliteration in progress            |
| **Unavailable**  | Red badge "[Unavailable] ✕" + empty field                                          | Transliteration failed, enter manually |
| **Manual**       | Gray badge "[Manual] ●" + user-typed text                                          | Translator entered manually            |
| **Stale**        | Yellow badge "[Regenerate needed] ●" + previous text + pulsing "Regenerate" button | Cache invalidated by source text edit  |

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

| State            | Visual                                                                | Description                        |
| ---------------- | --------------------------------------------------------------------- | ---------------------------------- |
| **Loading**      | Skeleton list (6 placeholder rows)                                    | Initial fetch in progress          |
| **Empty**        | "No translations yet — start translating!" with link to Translate tab | No history entries match filters   |
| **Has entries**  | Scrollable list of history items                                      | Data loaded                        |
| **Loading more** | Spinner at bottom of list                                             | Infinite scroll fetching next page |
| **Error**        | "Failed to load history. [Retry]"                                     | API call failed                    |

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

| State        | Visual                                                                       | Description              |
| ------------ | ---------------------------------------------------------------------------- | ------------------------ |
| **Loading**  | Skeleton cards (progress bar placeholder, grid placeholders)                 | Initial fetch            |
| **Empty**    | "No translation data yet. Sections need to be translated first."             | Book has no translations |
| **Has data** | Dashboard with progress bar, language breakdown, page grid, translator table | Data loaded              |
| **Error**    | "Failed to load statistics. [Retry]"                                         | API call failed          |

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

### 5. Book Upload

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

### 6. Book Console Layout (Updated — Epic 5)

The book console is updated with a richer sidebar that includes page reordering, progress tracking, filter/sort capabilities, and new panels for translation review, book building, and version history.

### 7. Page Reorder Interaction

| State        | Visual                                                                                                                                                                                                                                                   | Description                                    |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| **Idle**     | Page list items show drag handle icons (⋮⋮) on the left of each item. Items display thumbnail, page number, progress bar, and section count.                                                                                                             | Default state — pages sorted by `order` field. |
| **Hover**    | Cursor changes to `grab` on the drag handle area. Minor background highlight (150ms transition).                                                                                                                                                         | User hovers over drag handle zone.             |
| **Dragging** | Dragged item lifts with box shadow (elevation 4), reduced opacity (0.85). A horizontal drop indicator line (2px primary blue, 16px inset) appears at the target position between items. Other items shift apart with 200ms ease animation to make space. | User grabs handle and drags vertically.        |
| **Dropped**  | Item animates to new position (200ms ease-out). Toast appears: "Page order updated" with Undo button.                                                                                                                                                    | Drop completes successfully.                   |
| **Conflict** | Optimistic reorder is reverted. Toast: "Page order was modified by another editor — refresh to see latest" with [Refresh] button.                                                                                                                        | Backend returns 409 Conflict.                  |

**Interaction Details:**

- **Drag threshold**: 8px vertical movement before drag starts (prevents accidental drag on click)
- **Drag sensitivity**: Items auto-scroll the list when dragged near the top/bottom edge (scroll zone: 40px from edge, scroll speed: 1 item per 150ms)
- **Add Page between**: An "Add Page" button (40px tall, dashed border, "+" icon) appears between any two pages. Clicking inserts a blank page at that position. The button is only visible on hover of the gap area.
- **Delete Page**: Each page item has a delete icon (trash) visible on hover or in a context menu (three-dot menu on each item). Clicking shows a confirmation dialog with page number and section count before deletion. Delete disabled if only one page remains (tooltip "A book must have at least one page").
- **Undo reorder**: After a reorder, a toast with "Undo" button appears for 5 seconds. Clicking restores the previous order via a single API call with the old order array.
- **Keyboard reorder**: Alt+↑ moves the selected page up one position; Alt+↓ moves it down one position. Focus on the page list item is required.

### 8. Filter & Sort Bar

**Layout (sticky at top of page list):**

**Filter States:**

| Chip         | Color           | Icon | Behavior                                                              |
| ------------ | --------------- | ---- | --------------------------------------------------------------------- |
| All          | Neutral         | —    | Clears all filters, shows all pages                                   |
| Not Started  | Gray `#6B7280`  | ⬜   | Pages with 0 approved sections                                        |
| In Progress  | Blue `#2563EB`  | 🔵   | Pages with 1–99% approved sections                                    |
| Completed    | Green `#16A34A` | 🟢   | Pages with 100% approved sections                                     |
| Needs Review | Amber `#F59E0B` | 🟠   | Pages where all sections have submitted translations pending approval |

**Sort Options:**

| Option               | Icon            | Behavior                                   |
| -------------------- | --------------- | ------------------------------------------ |
| Page Order (default) | `Order ↑` / `↓` | Sorts by `order` field. Default ascending. |
| Translation % ↑      | `% ↑`           | Least completed first                      |
| Translation % ↓      | `% ↓`           | Most completed first                       |
| Page Order ↓         | `Order ↓`       | Reverse order                              |

**Interaction Details:**

- Filter chips are single-select (clicking one deselects the previous, clicking the active one returns to "All")
- Filter state persists in URL: `?filter=in_progress&sort=translation_percent&order=desc`
- Clicking the active filter again clears it (shows All)
- Sort direction toggles on second click of same sort option
- Summary stats bar shows near-real-time counts (polled every 10s or via WebSocket)
- Empty filter state: "No pages match the selected filter" with [Clear Filter] button
- Pre-detection state: "Process pages first to see translation progress"

**Progress Bar (per page item):**

| Percent | Color                               | Width        |
| ------- | ----------------------------------- | ------------ |
| 0%      | Gray `#CBD5E1`                      | Empty bar    |
| 1–99%   | Blue gradient `#60A5FA` → `#2563EB` | Proportional |
| 100%    | Green `#22C55E`                     | Full width   |

- Progress bar shows `approvedSections / totalSections` with percentage label on the right
- Bar fill animates with 600ms ease-out when progress changes
- Compact design: 8px height, rounded corners (4px radius), full width of page item

### 9. Translation Review Panel

The review panel is accessible from the Book Console's "Review" tab or by clicking a section with submitted translations from the page list.

**Layout:**

**Translation Card States:**

| State               | Visual                                                                                                                                                              | Action                                       |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| **Pending**         | White background, neutral border. Approve/Reject buttons enabled.                                                                                                   | Awaiting editor decision.                    |
| **Approved**        | Green border (2px), green ✓ APPROVED badge top-right. Background tint green `#F0FDF4`. Approve button disabled. Reject still available.                             | Card elevated with subtle green glow.        |
| **Rejected**        | Dimmed opacity (0.6), strikethrough text, red ✕ REJECTED badge, red border. Expandable rejection reason. Reject disabled. Approve still available as "re-override". | Translator notified via in-app notification. |
| **Editor's Choice** | Purple border (2px), purple star badge ⭐ EDITOR'S CHOICE. No action buttons (auto-approved).                                                                       | Created by editor override.                  |

**Reject Interaction:**

1. Click "Reject" → card shows inline expandable text area: "Reason for rejection (optional)"
2. Type reason (max 500 chars, shown with character counter)
3. Press Enter to submit, Escape to cancel
4. On submit → card transitions to Rejected state with 300ms dimming animation
5. Translator receives in-app notification with rejection reason

**Editor Override Interaction:**

- "Copy from [Translator Name]" buttons copy that translator's text to the editor textarea
- Textarea is a standard auto-resize textarea (min 4 rows, max 20 rows)
- "Submit as Editor's Choice" creates an auto-approved translation labeled "Editor's Choice"
- The override is stored as a regular Translation with `translatorId` = editor's ID

**Navigation:**

- "Previous Section" / "Next Section" buttons navigate through sections on the same page
- Navigation wraps: last section on page navigates to first section of next page
- Section counter: "Section 2 of 12 (Page 3)"

### 10. Build Panel

The build panel is accessible from the Book Console's "Build" tab and from a build button at the bottom of the sidebar.

**Layout:**

**Build States & Transitions:**

| State         | Trigger                                                        | Visual                                                   | Actions                                                              |
| ------------- | -------------------------------------------------------------- | -------------------------------------------------------- | -------------------------------------------------------------------- |
| **Idle**      | Panel loaded, no build running                                 | Summary counts, Build button                             | Click "Build" → confirmation dialog → enter Building                 |
| **Disabled**  | Pre-conditions not met (no sections, no approved translations) | Button grayed out, tooltip explains why                  | Hover tooltip: "No approved translations — review and approve first" |
| **Building**  | POST /api/books/{bookId}/build triggered                       | Progress bar with percentage + "Building page X of Y..." | Cancel Build                                                         |
| **Completed** | Celery task finishes successfully                              | Green checkmark, duration, version number                | Download PDF, Copy Link                                              |
| **Failed**    | Celery task errors                                             | Red X, error message                                     | Retry Build, Dismiss                                                 |

**Confirmation Dialog (before build):**

**Build Progress Details:**

- Progress bar height: 8px, rounded corners, gradient fill (primary blue)
- Percentage label centered below bar: "64%"
- Text below: "Building page 23 of 45..." (with animated dots)
- ETA: "Estimated time: ~44 seconds" (computed from avg time per page × remaining pages)
- Polling: `GET /api/books/{bookId}/builds/latest` every 3s (initial), backing off to 5s after 30s, 10s after 2min, 15s after 5min
- Cancel: sends `DELETE /api/books/{bookId}/builds/latest`, shows "Cancelling..." then returns to Idle

**Download Details:**

- "Download PDF" triggers `GET /api/books/{bookId}/versions/{versionNumber}/download` returning a presigned S3 URL with 1-hour expiry
- If URL expires, show toast "Download link expired — generate new link" and auto-regenerate
- "Copy Link" copies presigned URL to clipboard, shows brief "Link copied!" toast
- Filename: `{book-title}-v{versionNumber}.pdf`
- Download available to all roles (including TRANSLATOR)

### 11. Version History Panel

The version history panel is accessible from a sidebar tab or button in the Book Console.

**Version Item States:**

| State                       | Visual                                          | Actions                    |
| --------------------------- | ----------------------------------------------- | -------------------------- |
| **FINALIZED** (current)     | Green left border, ✅ badge, "⭐ Current" label | Download, View details     |
| **FINALIZED** (not current) | Neutral background                              | Download, Set as Current   |
| **FAILED**                  | Red left border, ❌ badge, error message        | Retry, Dismiss             |
| **DRAFT**                   | Blue left border, draft label                   | (no download — no PDF yet) |

**Interaction Details:**

- "Create Version" button opens a modal: Label (e.g., "Proofread v2"), Description (optional changelog)
- "Set as Current" marks a version as canonical. Checkmark icon and "⭐ Current" label move to the selected version
- "Download" triggers same download flow as Build panel with presigned URL
- Clicking a version row expands it to show more details (sections at build time, per-page breakdown)
- Past failed builds remain in the list; dismissing removes from view (audit log retains record)
- Empty state: "No versions built yet. Use the Build panel to create your first version."

### 12. Filter/Sort Bar — Detailed Interaction

**Sticky Behavior:**

- Filter bar and summary stats bar are sticky within the sidebar container
- They remain visible while scrolling through the page list
- On mobile, they collapse into a compact bar with a "Show Filters" toggle button

**Chip Animation:**

- Activating a filter chip: 150ms scale-up to 1.05, then back to 1.0, background color transition (200ms)
- Deactivating: background color fades to neutral over 200ms
- Chip count badge bounces briefly on count update

**Summary Stats Bar States:**
| State | Visual |
|---|---|
| **Data loaded** | Row of stat items with icons and numbers |
| **Zero values** | Stats show "0" — always shows structure |
| **Loading** | Skeleton placeholders for each stat number |
| **Updated** | Numbers animate up/down with 300ms transition |

### 13. Translation Cards — Expandable Reject Reason

A rejected translation card can expand to show the rejection reason:

- Rejection reason area collapsed by default, expandable via chevron toggle
- Animation: 200ms expand/collapse with height transition
- Even after rejection, Approve button remains as "✓ Approve (re-override)" — allows reversing

### 14. Build Progress — Polling & Progress Bar Animation

**Polling Schedule:**

**Progress Bar Animation:**

- Width animates via CSS `transition: width 600ms ease-out`
- Label updates with each poll response
- ETA fades in/out when value changes (200ms opacity)
- On completion: bar fills 100% with brief green flash (400ms pulse)

**Cancel Interaction:**

1. Click "Cancel Build"
2. Confirmation: "Are you sure? Partial artifacts will be discarded."
3. On confirm: sends DELETE, shows "Cancelling..." spinner
4. On success: returns to Idle with toast "Build cancelled"
5. On failure: toast "Failed to cancel build"

### 15. Download Button — Presigned URL Expiry

| Time Remaining | Visual                               | Behavior                             |
| -------------- | ------------------------------------ | ------------------------------------ |
| > 30 min       | Normal button                        | Click triggers download              |
| 5–30 min       | "Link expires in {N} minutes"        | Subtle warning below button          |
| < 5 min        | "Link expiring soon"                 | Yellow warning, auto-refresh URL     |
| Expired        | "Link expired — click to regenerate" | Red badge, click regenerates via API |

- Each click calls API to generate fresh presigned URL
- "Copy Link" copies current URL to clipboard
- URL auto-refreshes after 30 min if user stays on page

### 16. Page List — Summary Stats Bar Elements

| Stat               | Display                   | Example                  |
| ------------------ | ------------------------- | ------------------------ |
| Total pages        | `{n} pages`               | "45 pages"               |
| Total sections     | `{n} sections`            | "320 sections"           |
| Overall completion | `{n}%`                    | "90.6%"                  |
| Pending review     | `{n} pending`             | "15 pending"             |
| Warning            | ⚠️ `{n} without approval` | "⚠️ 30 without approval" |

- Stats refresh every 10s (polling)
- Each stat highlights briefly on change (300ms yellow background flash)
- All-complete state: green stats bar with brief sparkle celebration animation

## Color Palette

```
Primary:    #2563EB (blue-600)
Success:    #16A34A (green-600)
Warning:    #F59E0B (amber-500)
Error:      #DC2626 (red-600)
Neutral:    #F8FAFC, #E2E8F0, #94A3B8, #475569, #0F172A

Section Types:
  Header:        #3B82F6 (blue-500)
  Paragraph:     #22C55E (green-500)
  Footnote:      #F97316 (orange-500)
  Image Caption: #A855F7 (purple-500)
  Page Number:   #6B7280 (gray-500)
  Other:         #8B5CF6 (violet-500)
```

## Typography

- Font: Inter (system font stack fallback)
- Headings: 700 weight
- Body: 400 weight
- Code/monospace: JetBrains Mono (for text comparison)
- Section type labels on canvas: 11px bold, same color as section fill

## Responsive Breakpoints

- Mobile: < 768px — Stack layout, bottom sheet for sidebar
- Tablet: 768-1024px — Collapsible sidebar
- Desktop: > 1024px — Full layout as designed

- **Mobile** (< 768px): Stack layout, bottom sheet for sidebar, simplified toolbar (icons only, labels hidden)
- **Tablet** (768–1024px): Collapsible sidebar, toolbar with icon+label for important actions
- **Desktop** (> 1024px): Full layout as designed

## Responsive Behavior — Translation Page

| Element            | Desktop (>1024px)                               | Tablet (768–1024px)                   | Mobile (<768px)                                 |
| ------------------ | ----------------------------------------------- | ------------------------------------- | ----------------------------------------------- |
| Tab bar            | Horizontal tabs with labels                     | Horizontal tabs with labels           | Horizontal tabs, compact (icons + short labels) |
| Filters            | Inline horizontal row above tabs                | Collapsible row (tap to expand)       | Stacked vertically in a drawer                  |
| Translate layout   | Two-row: image+source top, trans+edit bottom    | Two-row, collapsible image panel      | Stacked: all four panels vertically             |
| Top row            | Side-by-side: image 50%, source text 50%        | Side-by-side, collapsible image       | Stacked: image on top, source text below        |
| Bottom row         | Side-by-side: exact letter 50%, translation 50% | Side-by-side, fixed height            | Stacked: exact letter above translation         |
| Section image      | 50% width top row, scrollable                   | 40% width, collapsible                | Full width, fixed height 240px                  |
| Source text panel  | 50% top row, editable, font scales with zoom    | 60% top row, scrollable               | Full width, below image, fixed font             |
| Confidence badge   | Inline in panel header                          | Inline in panel header                | Inline in panel header                          |
| Extract button     | Below source text panel                         | Below source text panel               | Below source text panel                         |
| Exact letter panel | 50% bottom row, editable                        | 50% bottom row, fixed height          | Full width, above translation editor            |
| Translation editor | 50% bottom row, auto-resize textarea            | 50% bottom row, fixed height textarea | Full width, min-height 120px                    |
| Zoom controls      | Below image, always visible                     | Below image, always visible           | Inside image, overlay controls                  |
| Page context       | Horizontal bar below editor                     | Horizontal bar below editor           | Compact: "Page X of Y" with swipe               |
| History list       | Full-width rows, side-by-side info              | Full-width rows, stacked info         | Stacked cards, full-width                       |
| Stats dashboard    | Full grid layout                                | 2-column grid                         | Single-column stack                             |
| Page grid          | Horizontal scroll with fixed cell size          | Horizontal scroll, smaller cells      | Wrap to multiple rows, tap to expand            |
| Translator table   | Full-width table with all columns               | Table with some columns hidden        | Card layout per translator                      |

## Responsive Behavior — Epic 5

| Element                           | Desktop (>1024px)                                      | Tablet (768–1024px)                                              | Mobile (<768px)                                                             |
| --------------------------------- | ------------------------------------------------------ | ---------------------------------------------------------------- | --------------------------------------------------------------------------- |
| Page list with drag reorder       | Full drag handles, mouse drag, keyboard Alt+Arrow      | Touch drag with long-press activation, visible grab handles      | Long press to initiate drag (haptic), compact items with smaller handles    |
| Page list items                   | Thumbnail (48x48), progress bar, section count, labels | Thumbnail (40x40), condensed progress bar                        | Thumbnail (32x32), no progress bar (shown on tap), compact text             |
| Filter/sort bar                   | Sticky horizontal bar, all chips visible               | Sticky, chips wrap to 2 rows, compact                            | Collapsible bar with "Show Filters" toggle, chips in drawer                 |
| Summary stats bar                 | Full row: pages, sections, %, pending                  | Compact: pages, %, pending only                                  | Hidden by default, shown in stats drawer                                    |
| Review panel (side-by-side cards) | Two cards side-by-side (or N-up for N translators)     | Cards in 1.5-column: primary card full, secondary card 50% width | Stacked vertically: one card full width, second below                       |
| Review panel — section image      | 50% width at top, side-by-side                         | 40% width, collapsible                                           | Full width, fixed 200px height                                              |
| Review — editor override          | Sidebar section below cards, full width                | Below cards, full width                                          | Bottom of scroll: compact textarea, "Copy" buttons stacked                  |
| Build panel                       | Full panel with summary, progress bar, download        | Full panel, narrower summary text                                | Compact: collapsible summary, progress bar only, download button full-width |
| Build progress                    | Full progress bar with ETA text                        | Progress bar, ETA on separate line                               | Thin progress bar (4px), compact label: "23/45 pages"                       |
| Version history                   | Full list with all metadata                            | List with truncated metadata, tap to expand                      | Compact list: version number + status only, tap for details                 |

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

### Book Console — Epic 5 Accessibility

#### Keyboard Navigation

- Page list items are focusable via Tab key, drag handles also focusable
- Alt+Arrow keyboard reorder (Alt+↑ move up, Alt+↓ move down)
- Filter chips focusable, activated via Enter/Space
- Sort dropdown focusable, activated via Enter
- Translation cards in review panel: Tab through cards, Enter/Space on Approve/Reject buttons
- Build Cancel button focusable and activatable via keyboard
- Version history items focusable, Enter to expand, Tab through actions

#### Screen Reader Support

- **Page list**: `role="list"` with `aria-label="Book pages"`
- **Page items**: `role="listitem"` with `aria-label="Page {number}, {progress percent} complete, {N} sections"`
- **Drag handles**: `role="button"` with `aria-label="Drag to reorder page {number}"`, `aria-grabbed="false/true"`
- **Reorder drop zone**: `aria-dropeffect="move"` on the page list container
- **Filter chips**: `role="radio"` within `role="radiogroup"`, `aria-pressed` for active state
- **Summary stats**: `role="region"` with `aria-label="Translation summary statistics"`, live region for updates
- **Translation cards**: `role="region"` with `aria-label="Translation by {translator name}, {status}"`
- **Approve button**: `aria-label="Approve translation by {name}"`, `aria-disabled` when already approved
- **Reject button**: `aria-label="Reject translation by {name}"`, expands textarea on activation
- **Rejection reason**: `aria-label="Reason for rejection"`, `aria-required="false"`
- **Editor override textarea**: `aria-label="Editor's translation"`, `aria-describedby` with status
- **Build progress**: `role="progressbar"` with `aria-valuenow`, `aria-valuemin="0"`, `aria-valuemax="100"`, descriptive `aria-label="Building book page {current} of {total}"`
- **Build cancel**: `aria-label="Cancel build"`
- **Download button**: `aria-label="Download version {versionNumber}"`
- **Copy Link**: `aria-label="Copy download link"`
- **Version history**: `role="list"` with `aria-label="Version history"`
- **Version items**: `role="listitem"` with `aria-label="Version {number}, {status}, built on {date}"`
- **Set as Current**: `aria-label="Set version {number} as current version"`
- **Add Page button**: `aria-label="Add blank page here"`
- **Delete Page button**: `aria-label="Delete page {number}"` with confirmation dialog announcing page details
- **Toast notifications**: `role="status"` with `aria-live="polite"`
- **Conflict toast**: `role="alert"` with `aria-live="assertive"` (important, immediate announcement)

#### Color Contrast

- Filter chips use both color AND text labels (not color alone)
- Progress bar has percentage label for screen readers
- Translation card states (Approved/Rejected) use borders + badges + icons, not color alone
- Build status (COMPLETED/FAILED) uses checkmark/red X + text
- Version history status badges use icons and text
- Drag handle icons are visible (not just functional) — `⋮⋮` pattern ensures visibility

#### Focus Management

- Opening Review panel: focus moves to the first translation card
- After approving: focus stays on the next unactioned card (or moves to next section)
- After rejecting: focus moves to the rejection reason textarea
- After submitting editor override: focus moves to "Next Section" button
- Clicking "Build": focus moves to the Build panel
- Build complete: focus moves to Download button
- Version history open: focus moves to the first version item
- Filter/sort change: announce result count via aria-live region
- Keyboard reorder: announce new position via aria-live region

### Translation Page Keyboard Shortcuts

| Key          | Context                          | Action                             |
| ------------ | -------------------------------- | ---------------------------------- |
| `Ctrl+Enter` | Translation editor               | Submit translation                 |
| `Escape`     | Translation editor / Source text | Blur input / Skip section          |
| `+` / `=`    | Image area focused               | Zoom in (shared zoom)              |
| `-`          | Image area focused               | Zoom out (shared zoom)             |
| `0`          | Image area focused               | Reset zoom to 100%                 |
| `1`          | Anywhere                         | Switch to Translate tab            |
| `2`          | Anywhere                         | Switch to History tab              |
| `3`          | Anywhere                         | Switch to Stats tab (editors only) |
| `?`          | Anywhere                         | Toggle keyboard shortcuts help     |

- Keyboard shortcuts only fire when no text input is focused or when the image area is focused
- Tooltips on zoom buttons show the associated shortcut (e.g., "Zoom in (+)")
- A small `[?]` help button in the toolbar can toggle a keyboard shortcut cheat sheet overlay

### Book Console — Epic 5 Keyboard Shortcuts

| Key      | Context                                | Action                                                          |
| -------- | -------------------------------------- | --------------------------------------------------------------- |
| `Ctrl+F` | Page list focused                      | Focus filter/sort bar                                           |
| `A`      | Review panel, translation card focused | Approve the selected translation                                |
| `R`      | Review panel, translation card focused | Reject the selected translation (shows reason textarea)         |
| `B`      | Book Console (any panel)               | Trigger build (opens confirmation dialog if pre-conditions met) |
| `Alt+↑`  | Page list item focused                 | Move page up one position                                       |
| `Alt+↓`  | Page list item focused                 | Move page down one position                                     |
| `Ctrl+Z` | After reorder                          | Undo last reorder action                                        |
| `Escape` | Reject reason textarea                 | Cancel rejection, close textarea                                |
| `Enter`  | Reject reason textarea                 | Submit rejection with reason                                    |

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
- **Submit button**: Progress dots animation during save ("Saving..." → ". ." → ".. " → "...")
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

- **Drag reorder start**: 100ms lift animation, item elevates with shadow, slight scale (0.98) press feedback before drag starts
- **Drop indicator**: 200ms fade-in of blue indicator line at target position
- **Reorder other items shift**: 200ms ease-out translateY animation for adjacent items making space
- **Drop complete**: 200ms ease-out settle animation as item drops into new position
- **Reorder undo toast**: Slide-in from top-right, 5s display with progress bar, "Undo" button
- **Reorder conflict revert**: 200ms items snap back to original positions, red flash on reverted items
- **Filter chip select**: 150ms scale-up to 1.05 then back to 1.0, 200ms background color transition
- **Filter chip count update**: Brief bounce (1.2→1.0 scale, 200ms) on count badge
- **Summary stat update**: 300ms number animate (count-up animation), brief yellow background flash (200ms)
- **Progress bar change**: 600ms ease-out width transition on the fill bar
- **Translation approve**: Card border color transitions from neutral to green over 200ms, background fades to green tint (300ms), green badge scales in (200ms scale 0.8→1.0)
- **Translation reject (dim)**: 300ms opacity transition from 1.0 to 0.6, strikethrough text animates in (200ms)
- **Rejection reason expand**: 200ms max-height animation with smooth content reveal
- **Editor override copy**: Brief highlight (200ms blue glow) on the copied-from card
- **Editor override submit**: Flash on button (checkmark appears), 300ms, then card appears with purple border
- **Build progress bar fill**: 600ms ease-out width transition, same as other progress bars
- **Build page counter**: Number updates with 200ms fade in/out as new page count arrives from poll
- **Build ETA update**: 200ms opacity fade when ETA value changes
- **Build complete transition**: Progress bar fills to 100% with 400ms green flash pulse, then download button appears with 200ms fade-in
- **Build cancel**: Button shows spinner for 200ms, then transitions back to Idle state
- **Download button appear**: 300ms fade-in with slight scale-up from 0.95 to 1.0
- **Copy Link feedback**: 200ms "Link copied!" toast slides in, 2s auto-dismiss
- **Download link expiry warning**: 300ms fade-in of warning text below button
- **Version history expand**: 200ms content height animation, slight background highlight
- **Set as Current**: 300ms checkmark animation, "⭐ Current" label slides in from right
- **Version create modal**: 200ms backdrop fade, modal scales in (0.95→1.0, 200ms)
- **Add Page button**: 150ms hover highlight, button appears on gap hover with fade-in (200ms)
- **Page delete confirmation**: Dialog slides in from center (200ms), destructive "Delete" button has brief pulse
- **Skeleton placeholders in stats bar**: Pulsing shimmer animation (1.5s infinite, linear gradient sweep)
- **Toast notifications (Epic 5)**: Slide-in from top-right, 3s display (success) / 5s (error/conflict), progress bar counts down
