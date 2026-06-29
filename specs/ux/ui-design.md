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

### 2. Translation Interface

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

- Mobile: < 768px — Stack layout, bottom sheet for sidebar
- Tablet: 768-1024px — Collapsible sidebar
- Desktop: > 1024px — Full layout as designed
