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

### Translation Page Layout

```
┌───────────────────────────────────────────────────────┐
│  ← Back to Queue   Translate                          │
├──────────────────────────┬───────────────────────────┤
│                          │                            │
│   Section Image          │  Translation Panel          │
│   (cropped from page)    │  ┌─────────────────────┐   │
│   ┌──────────────────┐   │  │ Auto-translated:    │   │
│   │                  │   │  │ "Lorem ipsum..."    │   │
│   │   [ZOOMABLE]     │   │  └─────────────────────┘   │
│   │                  │   │  ┌─────────────────────┐   │
│   └──────────────────┘   │  │ Your translation:   │   │
│                          │  │ [Text area]         │   │
│   Page Context           │  │                     │   │
│   [Page i] [Page 42]     │  ├─────────────────────┤   │
│   [Page 43]              │  │ Exact letters:      │   │
│                          │  │ [optional]          │   │
│                          │  └─────────────────────┘   │
│                          │  [Save] [Skip]             │
│                          │                            │
│                          │  ┌─────────────────────┐   │
│                          │  │ My previous submit  │   │
│                          │  │ (visible before     │   │
│                          │  │  approval/rejection)│   │
│                          │  └─────────────────────┘   │
│                          │                            │
│                          │  Comments                  │
│                          │  ┌─────────────────────┐   │
│                          │  │ User: good text     │   │
│                          │  └─────────────────────┘   │
└──────────────────────────┴───────────────────────────┘
```

## Detailed Interaction Patterns

### 1. Section Annotation Editor (Konva.js)

#### Image Loading

| State | Visual | Description |
|-------|--------|-------------|
| **Loading** | Skeleton placeholder (aspect-ratio matching container) + spinner icon with "Loading page image..." | While `HTMLImageElement` loads from presigned S3 URL |
| **Loaded** | Page image rendered as `<Rect fillPatternImage={imgElement}>` or `<Konva.Image>` covering full stage | Image element stored in `useState` and passed to canvas |
| **No image** | Centered message: "No page image available" + subtitle "Upload a book and process it to see pages here" | When `pageImageUrl` is null/undefined |
| **Error** | Centered message: "Failed to load page image" + [Retry] button | When `img.onerror` fires |

#### Section Operations

| State | Visual | Description |
|-------|--------|-------------|
| **Empty** | Canvas shows just the page image. Bottom overlay hint: "No sections yet. Click 'Detect Sections' or draw manually." | No sections loaded |
| **Detected** | Colored rectangles overlaid on image with type labels | Sections loaded from API or detection |
| **Selected** | Rectangle has thicker white border (2px), Transform handles at corners/edges, type selector appears in toolbar | User clicks a rectangle |
| **Hover** | Rectangle opacity increases (fill becomes more opaque), cursor becomes pointer | Mouse hovers over a rectangle |
| **Drawing** | Crosshair cursor, dashed preview rectangle follows mouse on drag, "Cancel Draw" button highlighted | Toggle draw mode active |
| **Detecting** | Semi-transparent overlay with spinner + "Detecting sections..." message, all toolbar buttons disabled except zoom | Detection API in progress |
| **Saving** | "Confirm Sections" button shows spinner, all edit buttons disabled | Save API in progress |

#### Section Type Color Scheme

| Type | Hex Color | Fill Opacity | Label | Description |
|------|-----------|-------------|-------|-------------|
| HEADER | `#3B82F6` (blue-500) | 25% (`40` hex) | `HEADER` | Book/page titles |
| PARAGRAPH | `#22C55E` (green-500) | 25% | `PARAGRAPH` | Body text |
| FOOTNOTE | `#F97316` (orange-500) | 25% | `FOOTNOTE` | Footnotes |
| IMAGE_CAPTION | `#A855F7` (purple-500) | 25% | `IMAGE_CAPTION` | Image captions |
| PAGE_NUMBER | `#6B7280` (gray-500) | 25% | `PAGE_NUMBER` | Page numbers |
| OTHER | `#8B5CF6` (violet-500) | 25% | `OTHER` | Miscellaneous |

- Stroke color matches fill color
- Stroke width: 1px (unselected), 2px white (selected)
- Type label text: 11px bold, same color as fill, positioned at top-left of rectangle with 4px offset

#### Toolbar Icons & Controls

| # | Control | Type | Icon/Text | Behavior |
|---|---------|------|-----------|----------|
| 1 | Add Section | Toggle button | `[📐 Add Section]` / `[✕ Cancel Draw]` | Toggles draw mode. Active state: primary color background |
| 2 | Delete | Action button | `[🗑 Delete]` | Deletes selected section. Disabled when no selection |
| 3 | Type Selector | Dropdown | `[Type: PARAGRAPH ▼]` | Only visible when section selected. Changes section type |
| 4 | Undo | Action button | `[↩]` | Reverses last action. Disabled when undo stack empty |
| 5 | Redo | Action button | `[↪]` | Reapplies last undone action. Disabled when redo stack empty |
| 6 | Detect Sections | Action button | `[✨ Detect Sections]` | Triggers ML-based section detection. Disabled during detection/saving |
| 7 | Zoom Out | Action button | `[−]` | Decreases zoom by 10% (min 50%) |
| 8 | Zoom Level | Label | `100%` | Displays current zoom percentage |
| 9 | Zoom In | Action button | `[+]` | Increases zoom by 10% (max 300%) |
| 10 | Confirm Sections | Primary action | `[✓ Confirm Sections]` | Saves all sections to API. Shows spinner while saving |

#### Keyboard Shortcuts

| Key | Context | Action |
|-----|---------|--------|
| `Delete` / `Backspace` | Canvas focused | Delete selected section |
| `Ctrl+Z` | Anywhere | Undo |
| `Ctrl+Shift+Z` / `Ctrl+Y` | Anywhere | Redo |
| `Escape` | Canvas focused | Deselect current section / Cancel draw mode |
| `+` / `=` | Canvas focused | Zoom in |
| `-` | Canvas focused | Zoom out |
| `Ctrl+S` | Anywhere | Save/confirm sections |
| `D` | Canvas focused | Toggle draw mode |

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

**States:**

- **Idle** — Waiting for user to click "Next Section"
- **Loading** — Section image (from cropped S3 key) and auto-translation loading
- **Ready** — Section loaded, auto-translate shown, editor ready
- **Already submitted** — Shows "My previous submission" panel with the translator's own pending text (before approval)
- **Saving** — Spinner on Save button
- **Saved** — Green checkmark + "Translation saved" toast
- **Complete** — "All sections translated!" when queue empty
- **Error** — "Failed to load section. [Retry]"

**Interactions:**

- Zoom slider +/— buttons and percentage display
- Click "Next" → load next random section
- Click "Prev/Next Page" → show adjacent page thumbnails (showing `originalPageNumber` labels)
- Click thumbnail → navigate to that page's sections
- Text area auto-sizes as user types
- Ctrl+Enter shortcut to save
- **Exact letter field** — Optional text input below the main translation for letter-for-letter transliteration (e.g., devanagari → Sinhala script)
- **My previous submission panel** — If the translator has already submitted, shows their pending translation with an "Edit" button to resubmit

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

### 6. Book Organization

- Drag-to-reorder pages in sidebar list
- Status badges: ✅ Completed, ⏳ In Progress, ❌ Not Started, 🔄 Processing
- Progress bar per book (compact): green/yellow/red fill
- Filter buttons: All | Completed | In Progress | Not Started
- Sort: Page Number | Progress %

### 7. Translation Review (Editor)

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

- **Mobile** (< 768px): Stack layout, bottom sheet for sidebar, simplified toolbar (icons only, labels hidden)
- **Tablet** (768–1024px): Collapsible sidebar, toolbar with icon+label for important actions
- **Desktop** (> 1024px): Full layout as designed

## Responsive Behavior — Page Editor

| Element | Desktop (>1024px) | Tablet (768–1024px) | Mobile (<768px) |
|---------|------------------|---------------------|-----------------|
| Toolbar | Full horizontal bar with labels | Two-row toolbar, labels visible | Single row, icons only, overflow scroll |
| Canvas | Full width available | Full width, slightly smaller | Full width, min-height 300px |
| Zoom controls | Always visible | Always visible | Collapsed into expandable panel |
| Type selector | Inline in toolbar | Inline in toolbar | Modal/dropdown overlay on tap |
| Sidebar properties | Right sidebar (if applicable) | Bottom sheet | Bottom sheet |

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

## Micro-interactions

- **Rectangle selection**: 150ms border width transition, snap
- **Draw preview**: Dashed outline follows cursor in real-time
- **Zoom**: Smooth scale transition (CSS `transform` on the Stage container)
- **Save success**: Brief green flash on the confirm button before showing checkmark
- **Error**: Subtle shake animation on the error element
- **Hover**: 150ms opacity transition on rectangle fill
