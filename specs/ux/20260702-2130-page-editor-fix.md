# Page Editor Fix — UX Design

**Date:** 2026-07-02 21:30
**Author:** UX (BMAD)
**Based on:** specs/business-analysis/20260702-2108-page-editor-fix.md, specs/business-analysis/user-stories.md, specs/business-analysis/data-model.md, specs/architecture/architecture.md

---

## Overview

The page editor at `/books/[bookId]/pages/[pageNum]` is the primary tool for editors to define content sections on each scanned book page. It uses a Konva.js canvas to overlay colored, draggable rectangles on the page image, allowing editors to create, modify, and confirm section boundaries before they enter the translation pipeline.

This spec documents the complete UI design for the page editor, including all interaction states, toolbar design, color-coded section types, keyboard shortcuts, undo/redo support, responsive behavior, and accessibility.

## Page Editor Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Header                                                      │
│  [← Back to Book]  Page 5  [🔵 PENDING]  [⚙️ pageId]       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Toolbar (Desktop)                                            │
│  ┌────────────┐ ┌────────┐ ┌──────────────────┐              │
│  │ 📐 Add     │ │ 🗑     │ │ Type: PARAGRAPH ▼ │             │
│  │   Section  │ │ Delete │ │                  │              │
│  └────────────┘ └────────┘ └──────────────────┘              │
│  ┌──────┐ ┌──────┐ ┌────────────────┐                       │
│  │  ↩   │ │  ↪   │ │ ✨ Detect      │                       │
│  │ Undo │ │ Redo │ │   Sections     │                       │
│  └──────┘ └──────┘ └────────────────┘                       │
│  ┌──┐ ┌──────┐ ┌──┐ ┌────────────────────┐                  │
│  │ − │ │ 100% │ │ + │ │ ✓ Confirm Sections │                │
│  └──┘ └──────┘ └──┘ └────────────────────┘                  │
│                                          [?] Help            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   ┌───────────────────────────────────────────────┐         │
│   │          Canvas Area                            │         │
│   │          role="application"                     │         │
│   │          aria-label="Page section editor"       │         │
│   │                                                │         │
│   │   ┌─────────────────────────────────────┐      │         │
│   │   │  Page Image                          │      │         │
│   │   │  (Konva.Layer — bottom)              │      │         │
│   │   │  fillPatternImage={imgElement}       │      │         │
│   │   │                                     │      │         │
│   │   │   ┌─────────┐                       │      │         │
│   │   │   │ HEADER  │  ┌──────────────┐     │      │         │
│   │   │   │ (blue)  │  │ PARAGRAPH    │     │      │         │
│   │   │   └─────────┘  │ (green)      │     │      │         │
│   │   │                └──────────────┘     │      │         │
│   │   │                ┌──────────────────┐ │      │         │
│   │   │                │ PARAGRAPH        │ │      │         │
│   │   │                │ (green)          │ │      │         │
│   │   │                └──────────────────┘ │      │         │
│   │   │                       ┌──────────┐  │      │         │
│   │   │                       │ FOOTNOTE │  │      │         │
│   │   │                       │ (orange) │  │      │         │
│   │   │                       └──────────┘  │      │         │
│   │   │                     ┌──────────┐    │      │         │
│   │   │                     │ PAGE_NUM │    │      │         │
│   │   │                     │ (gray)   │    │      │         │
│   │   │                     └──────────┘    │      │         │
│   │   └─────────────────────────────────────┘      │         │
│   │                                                │         │
│   │   Second Layer (sections):                      │         │
│   │   - Rect: colored fill + stroke                 │         │
│   │   - Transformer: handles on selected            │         │
│   │                                                │         │
│   │   Third Layer (labels):                         │         │
│   │   - Text: type labels at top-left               │         │
│   │                                                │         │
│   └───────────────────────────────────────────────┘         │
│                                                               │
│   Status Bar (below canvas)                                    │
│   ┌──────────────────────────────────────────────────────┐    │
│   │ [sectionCount] sections  |  [dimensions]  |  [zoom]  │    │
│   └──────────────────────────────────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## User Flows

### Flow 1: Load Page Editor

```
[Open page URL] 
  → Fetch page detail from API
  → Show header with Page X title + status badge
  → If pageImageUrl:
       [Loading state] Show skeleton with spinner
       → Image loads via HTMLImageElement
         → Render image on canvas background (Konva.Image or Rect fillPatternImage)
         → If sections exist: render colored rectangles
         → If no sections: show empty state hint
       → Image fails to load
         → Show "Failed to load page image" + [Retry] button
  → If no pageImageUrl:
       Show "No page image available" message
```

### Flow 2: Detect Sections

```
[User clicks "Detect Sections"]
  → Button shows spinner, overlay appears: "Detecting sections..."
  → All edit controls disabled
  → POST /api/pages/{pageId}/sections/detect
  → Backend enqueues Celery task
  → Frontend polls page status or waits for completion
  → On complete:
       → Refetch page data
       → Sections appear as colored rectangles
       → Overlay removed
       → Controls re-enabled
       → Toast: "Sections detected: {n} found"
  → On failure:
       → Overlay removed
       → Error state: "Detection failed" + [Retry Detection] button
       → Page status shown as DETECTION_FAILED
```

### Flow 3: Edit Sections

```
[Section(s) visible on canvas]
  → Click rectangle → select it (Transformer handles appear, toolbar shows type selector)
  → Drag rectangle → move it (live position update)
  → Drag Transformer handle → resize (min 10x10 constraint)
  → Click "Delete" or press Delete key → remove section
  → Change type via dropdown → rectangle color updates immediately
  → Ctrl+Z → undo last action
  → Ctrl+Shift+Z → redo last undone action
  → Escape → deselect any selected section
  → D key → toggle draw mode (cursor changes to crosshair)
```

### Flow 4: Draw New Section

```
[User clicks "Add Section" or presses D]
  → Button highlights, cursor changes to crosshair on canvas
  → User mousedown on canvas → record start position
  → User drags → dashed preview rectangle follows cursor
  → User mouseup (area > 10x10px):
       → New section created with type PARAGRAPH
       → Auto-selected with Transformer handles
       → Draw mode automatically exits
  → User presses Escape or clicks "Cancel Draw":
       → Draw mode exits without creating section
```

### Flow 5: Confirm Sections

```
[User clicks "Confirm Sections" or presses Ctrl+S]
  → Button shows spinner, all edit controls disabled
  → Undo/redo stacks cleared
  → PUT /api/pages/{pageId}/sections with raw array body:
       [{ id, sectionOrder, type, x, y, width, height }, ...]
  → On success:
       → Toast: "✓ Sections confirmed!"
       → Canvas enters read-only confirmation state
       → "Re-detect Sections" button appears
       → Status badge updates to SECTIONS_CONFIRMED
  → On failure:
       → Error toast: "Failed to save sections"
       → [Retry] option
       → Controls re-enabled, stacks NOT cleared
```

### Flow 6: Re-detect After Confirmation

```
[Page already has confirmed sections]
  → User clicks "Re-detect Sections"
  → Confirmation dialog: "Re-detecting will replace all current sections. Continue?"
  → [Cancel] [Continue]
  → On continue: same as Flow 2, replaces all existing sections
```

## Section Type Color Scheme

| Type | Color | Hex | Fill Opacity | Stroke | Label Text |
|------|-------|-----|-------------|--------|------------|
| HEADER | Blue | `#3B82F6` | 25% (`40` hex) | `#3B82F6` at 1px, selected: white 2px | `HEADER` (bold, #3B82F6, 11px) |
| PARAGRAPH | Green | `#22C55E` | 25% | `#22C55E` at 1px | `PARAGRAPH` (bold, #22C55E, 11px) |
| FOOTNOTE | Orange | `#F97316` | 25% | `#F97316` at 1px | `FOOTNOTE` (bold, #F97316, 11px) |
| IMAGE_CAPTION | Purple | `#A855F7` | 25% | `#A855F7` at 1px | `IMAGE_CAPTION` (bold, #A855F7, 11px) |
| PAGE_NUMBER | Gray | `#6B7280` | 25% | `#6B7280` at 1px | `PAGE_NUMBER` (bold, #6B7280, 11px) |
| OTHER | Violet | `#8B5CF6` | 25% | `#8B5CF6` at 1px | `OTHER` (bold, #8B5CF6, 11px) |

## UI States Matrix

### Canvas States

| State | Trigger | Visual | Actions Available |
|-------|---------|--------|-------------------|
| **loading** | Page mount, image fetching | Skeleton placeholder (aspect ratio of container) + spinning loader icon + text "Loading page image..." | None |
| **no-image** | `pageImageUrl` is null/undefined | Centered: large document icon + "No page image available" + subtitle | Back to book |
| **error-loading** | `img.onerror` fires | Centered: warning icon + "Failed to load page image" + [Retry] button | Retry, back to book |
| **empty** | Image loaded, no sections exist | Page image visible + bottom overlay hint: "No sections yet. Click 'Detect Sections' or draw manually." | Detect Sections, Add Section, zoom |
| **detecting** | POST to detection API | Semi-transparent dark overlay + centered spinner + "Detecting sections..." text. All toolbar buttons disabled except zoom | Cancel detection (if polling) |
| **detection-failed** | Detection API error | Overlay removed, error banner above canvas: "Detection failed" + [Retry Detection] button | Retry Detection, Add Section (manual) |
| **edit** | Sections loaded, user modifying | Colored rectangles visible, toolbar fully active, Transformer on selected | All edit, draw, detect, zoom, save |
| **saving** | Confirm clicked, API in flight | "Confirm Sections" button shows spinner, all edit buttons disabled | Wait |
| **confirmed** | Save API success | Same as edit but with "✓ Re-detect Sections" button replacing "Detect Sections". Sections rendered read-only (draggable=false) | Re-detect, zoom |
| **save-failed** | Save API error | Error toast "Failed to save sections" + [Retry] on Confirm button | Retry, edit |

### Toolbar Button States

| Button | Default | Active | Disabled | Loading |
|--------|---------|--------|----------|---------|
| Add Section | Normal background | Primary background, white text | During detect/save | — |
| Delete | Normal | — | No selection / during detect/save | — |
| Type Selector | Hidden | Visible when section selected | During detect/save | — |
| Undo | Normal | — | Stack empty / during detect/save | — |
| Redo | Normal | — | Stack empty / during detect/save | — |
| Detect Sections | Normal | — | During detect/save/confirmed | Spinner replacing icon |
| Zoom Out | Normal | — | At min (50%) | — |
| Zoom In | Normal | — | At max (300%) | — |
| Confirm Sections | Primary background | — | No sections / during detect/save | Spinner replacing checkmark |
| Re-detect Sections | Normal | — | During detect/save | Spinner replacing icon |

## Toolbar Icon System

Since the project does not yet use an icon library, the toolbar controls use Unicode symbols as icon representations. These should be replaced with proper SVG icons (e.g., from Lucide or Heroicons) when an icon system is established.

| Tool | Unicode Icon | Semantic | Tooltip (Desktop) | Keyboard Shortcut |
|------|-------------|----------|-------------------|-------------------|
| Add Section | `📐` (or `⊞` / plus box) | Add section rectangle | "Add Section (D)" | `D` |
| Add Section (active) | `✕` (multiplication sign) or close icon | Cancel draw | "Cancel Draw (Esc)" | `Escape` |
| Delete | `🗑` (trash) | Delete selected section | "Delete (Delete)" | `Delete` / `Backspace` |
| Undo | `↩` (left arrow with hook) | Undo last action | "Undo (Ctrl+Z)" | `Ctrl+Z` |
| Redo | `↪` (right arrow with hook) | Redo last undone | "Redo (Ctrl+Shift+Z)" | `Ctrl+Shift+Z` |
| Detect Sections | `✨` (sparkle) or magic wand | Auto-detect sections | "Detect Sections" | — |
| Zoom In | `+` / `+` icon | Zoom in | "Zoom In (+)" | `+` |
| Zoom Out | `−` / minus icon | Zoom out | "Zoom Out (-)" | `-` |
| Confirm | `✓` or checkmark | Save & confirm sections | "Confirm Sections (Ctrl+S)" | `Ctrl+S` |
| Re-detect | `🔄` (refresh) | Re-run detection | "Re-detect Sections" | — |
| Help | `?` (question mark) | Show keyboard shortcuts | "Keyboard Shortcuts" | — |

## Undo/Redo Design

### Architecture

- **History stack**: Array of section arrays `Section[][]` stored in `useState`
- **Redo stack**: Separate `Section[][]` for undone states
- **Maximum depth**: 50 entries to cap memory usage

### What is undoable

| Action | Undo Behavior | Redo Behavior |
|--------|---------------|---------------|
| Add section | Remove the added section | Re-add the section |
| Delete section | Restore the deleted section | Re-delete |
| Move section | Restore previous x, y | Re-apply move |
| Resize section | Restore previous width, height, x, y | Re-apply resize |
| Type change | Restore previous type | Re-apply type change |

### What is NOT undoable

- Zoom level changes (separate from section state)
- Detection results (would require re-running detection)
- Confirmed/saved sections (stack cleared on confirm)

### Stack Management

- Before each undoable action, a snapshot of the current `sections` array is pushed to the undo stack
- The redo stack is cleared whenever a NEW action is performed (not an undo/redo)
- The undo stack is cleared when sections are confirmed/saved
- If undo stack reaches 50 entries, the oldest entry is dropped

## Responsive Behavior

### Desktop (>1024px)

- Full horizontal toolbar with labels
- Toolbar right section floats right
- Canvas fills available width
- Status bar visible below canvas

### Tablet (768–1024px)

- Toolbar wraps to two rows:
  - Row 1: Add Section, Delete, Type selector
  - Row 2: Undo, Redo, Detect Sections, zoom controls, Confirm Sections
- Canvas slightly smaller (accounts for sidebar if present)
- Type selector remains inline

### Mobile (<768px)

- Toolbar becomes a single row with horizontal scroll (icons only, labels hidden via CSS)
- Essential controls shown first: Add Section, Delete, Detect, Confirm
- Secondary controls (Undo, Redo) in overflow menu or second row
- Zoom controls collapsed into expandable panel or positioned at bottom-right corner of canvas
- Type selector opens as bottom sheet modal on mobile
- Canvas min-height: 300px (vertical layout)
- Status bar simplified: just section count
- Canvas takes full viewport width on narrow screens

### Canvas Sizing Logic

```
maxCanvasWidth = containerRef.offsetWidth - 40 (padding)
scale = min(maxCanvasWidth / imageWidth, 1)
displayWidth = imageWidth * scale
displayHeight = imageHeight * scale
```

- Image never scales up beyond 100% (only scales down to fit)
- Zoom multiplies the displayed size: `stageWidth = displayWidth * zoom`
- Zoom range: 50% to 300%

## Accessibility

### ARIA Roles & Labels

| Element | ARIA | Notes |
|---------|------|-------|
| Canvas container | `role="application"`, `aria-label="Page section editor for page {n}"` | Wraps the Konva Stage |
| Each section rect | `aria-label="{type} section at position ({x}, {y}), size {width} by {height}"` | On click/focus |
| Toolbar | `role="toolbar"`, `aria-label="Section editing tools"` | Groups toolbar actions |
| Add Section button | `aria-pressed="{isDrawing}"` | Toggle state |
| Delete button | `aria-disabled="{!selectedId}"` | Disabled state |
| Zoom level | `aria-live="polite"` | Announces zoom changes |
| Loading overlay | `role="status"`, `aria-live="polite"` | Announces detection/saving progress |
| Error messages | `role="alert"` | Announces errors |

### Keyboard Navigation

- All toolbar buttons are keyboard-focusable (Tab order left to right)
- Canvas itself is focusable: Tab to canvas, then keyboard shortcuts active
- Shift+Tab reverse navigation
- Escape returns focus from canvas to the first toolbar button
- Ctrl+S save works globally when not in a text input

### Screen Reader Announcements

| Event | Announcement |
|-------|-------------|
| Image loading starts | "Loading page image" |
| Image loaded | "Page image loaded" |
| Image error | "Failed to load page image" |
| Detection starts | "Detecting sections" |
| Detection complete | "{n} sections detected" |
| Detection error | "Section detection failed" |
| Section selected | "{type} section selected at position {x}, {y}" |
| Section deselected | "No section selected" |
| Section created | "New {type} section created" |
| Section deleted | "{type} section deleted" |
| Undo | "Undo: {action}" |
| Redo | "Redo: {action}" |
| Save starts | "Saving sections" |
| Save success | "Sections confirmed successfully" |
| Save error | "Failed to save sections. Please try again." |

### Color & Contrast

- Section colors are used with 25% fill + 100% stroke for contrast
- Type labels use 100% color fill at 11px bold for readability
- White stroke (2px) on selected rectangles ensures visibility on dark backgrounds
- Error messages use both icon + text, never color alone
- Loading overlays use semi-transparent dark background for contrast with spinner

## Component Design

| Component | Purpose | States | Props |
|-----------|---------|--------|-------|
| `PageEditor` | Main canvas editor component | loading, no-image, error-loading, empty, detecting, detection-failed, edit, saving, confirmed, save-failed | `pageImageUrl`, `initialSections`, `onSave`, `pageId` |
| `EditorToolbar` | Horizontal bar with all editing tools | desktop, tablet, mobile; active/inactive toggle states | `isDrawing`, `selectedId`, `sectionTypes`, `zoom`, `canUndo`, `canRedo`, `isDetecting`, `isSaving`, `isConfirmed`, `onAction` |
| `SectionRect` | Single draggable/resizable rectangle on canvas | default, selected, hover, drawing | `section`, `isSelected`, `onSelect`, `onDragEnd`, `onTransformEnd` |
| `SectionLabel` | Type label text overlay on each section | always visible | `section`, `color` |
| `DrawingPreview` | Dashed rectangle while user draws new section | visible when drawing | `startPoint`, `currentPoint` |
| `LoadingOverlay` | Semi-transparent overlay with spinner + text | visible during detection/saving | `message` |
| `ErrorBanner` | Error message with retry action | visible on error | `message`, `onRetry` |
| `StatusBar` | Info panel below canvas | always visible below canvas | `sectionCount`, `imageDimensions`, `zoom` |
| `HelpOverlay` | Keyboard shortcuts popup | toggled by `?` button | `shortcuts[]`, `onClose` |
| `ConfirmDialog` | Confirmation modal for destructive actions | visible on re-detect after confirm | `title`, `message`, `onConfirm`, `onCancel` |

## Micro-interactions

| Interaction | Animation | Duration | Notes |
|-------------|-----------|----------|-------|
| Section hover | Fill opacity increase from 25% to 40% | 150ms | CSS transition |
| Section select | Border width from 1px to 2px | 100ms | Immediate feel |
| Draw preview | Dashed line follows cursor in real-time | Continuous | Using Konva Line with dash |
| Zoom change | Canvas scales smoothly | 200ms | CSS transform on Stage container |
| Button loading | Icon fades out, spinner fades in | 200ms | Avoids jarring swap |
| Save success | Brief green flash, then checkmark | 500ms | Then toast slides in |
| Error toast | Slide in from top-right | 300ms | Auto-dismisses after 5s |
| Overlay appear | Fade in | 200ms | Semi-transparent dark bg |
| Tooltip appear | Fade in with slight delay | 150ms + 500ms delay | Standard tooltip pattern |

---

## Appendix: Known Bugs Fixed by This UX

| Bug ID | Issue | UX Impact | Fix |
|--------|-------|-----------|-----|
| B1 | `fillPatternImage={undefined}` | Image never renders on canvas | Store loaded `HTMLImageElement` in state and pass to `fillPatternImage` |
| B2 | `pageImageUrl` receives raw S3 key | Browser cannot load image | Backend returns presigned URL as `imageUrl` field |
| B3 | `"use server"` directive in client component + wrapped payload | Save API call fails with 422 | Remove `"use server"`, send raw array `[{...}]` |
| B4 | Detection creates single dummy section | Only one PARAGRAPH rectangle covering entire page | Integrate real ML model (LayoutParser) |
| B5 | No undo/redo | Editors cannot recover from mistakes | Add history stacks + Ctrl+Z/Ctrl+Shift+Z |
| B6 | No loading/error states | Poor UX during async operations | Add overlays, banners, toasts for all states |

## Appendix: Implementation Priority (UX Perspective)

| Priority | Feature | UX Rationale |
|----------|---------|-------------|
| P0 | Render page image (B1+B2) | Editor cannot see the page — app is unusable |
| P0 | Fix save payload (B3) | Sections cannot be persisted — core workflow broken |
| P1 | Loading/error states (B6) | Without feedback, user thinks app is frozen |
| P1 | Section order preservation | Without correct ordering, pages render wrong sections |
| P2 | Undo/redo (B5) | Editors make mistakes; recovery without redo is tedious |
| P2 | Real ML detection (B4) | Stub works for demo; ML needed for real use |
| P3 | Keyboard shortcuts | Power-user feature; nice-to-have |
| P3 | Help overlay | Self-documenting shortcuts; educational |

## Appendix: Canvas Layer Architecture

```
Stage (scaleX=zoom, scaleY=zoom)
├── Layer 1 (Background) — Page image
│   └── Rect with fillPatternImage={imgElement}
│       or Image node with image={imgElement}
├── Layer 2 (Sections) — Colored rectangles + Transformer
│   ├── Rect[] (section rectangles, draggable=true)
│   │   - fill: {color}40 (25% opacity)
│   │   - stroke: {color} (1px) or white (2px if selected)
│   │   - onClick, onDragEnd, onTransformEnd
│   └── Transformer
│       - ref={trRef}
│       - boundBoxFunc: enforce min 10x10
└── Layer 3 (Labels) — Type text labels
    └── Text[] (type labels, top-left of each rect)
        - x: section.x + 4
        - y: section.y + 4
        - text: section.type
        - fontSize: 11, fontStyle: bold
        - fill: SECTION_COLORS[section.type]
```
