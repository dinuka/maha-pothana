# Epic 5: Book Organization & Publishing — UX/Interaction Specification

**Date:** 2026-07-09 12:00
**Author:** UX Agent
**Epic Reference:** Epic 5 — Book Organization & Publishing
**Business Analysis Reference:** `specs/business-analysis/20260709-1200-epic5-book-organization.md`
**Architecture Reference:** `specs/architecture/20260709-1200-epic5-book-organization.md`
**UI Design Reference:** `specs/ux/ui-design.md`

---

## 1. Page Reorder — Full Interaction Design

### 1.1 Drag-and-Drop Mechanics

**Library recommendation:** `@dnd-kit/core` with `@dnd-kit/sortable` (lightweight, accessible, good keyboard support)

**Component Tree:**

```
<DndContext>
  <SortableContext items={pageIds} strategy={verticalListSortingStrategy}>
    <PageList>
      {pages.map(page => (
        <SortablePageItem key={page.id} page={page}>
          <DragHandle />   ← 32x40px, grab area
          <PageThumbnail />
          <PageProgressBar />
          <PageActions />  ← Delete, context menu
          <AddPageGap />   ← between items (40px, dashed border)
        </SortablePageItem>
      ))}
    </PageList>
    <AddPageButton atBottom />
  </SortableContext>
</DndContext>
```

**Drag Activation:**

- Drag is initiated ONLY from the drag handle (⋮⋮), NOT from the page item body
- This prevents accidental reordering when clicking the item to navigate
- Touch devices: handle is always visible, tap-and-hold on handle activates drag mode

**Drag Handle Design:**

- 48px wide, full height of item (72px)
- Icon: six dots pattern (⋮⋮) — three dots in two rows
- Hover: background color darkens slightly (150ms)
- Cursor: `grab` (default), `grabbing` (while dragging)

### 1.2 Drag States

#### State: Idle

```
┌─────────────────────────────────────────┐
│ ⋮⋮  📷  Page 1  ██████████████ 100%   │
│         5 sections                      │
├─────────────────────────────────────────┤
│  ┌─ Add Page ──────────────────────────┐ │   ← Only visible on hover
│  └─────────────────────────────────────┘ │
├─────────────────────────────────────────┤
│ ⋮⋮  📷  Page 2  ████████░░░░░░  60%   │
│         4 sections                      │
└─────────────────────────────────────────┘
```

#### State: Dragging

```
┌─────────────────────────────────────────┐
│ ⋮⋮  📷  Page 1  ██████████████ 100%   │
│         5 sections                      │
│─────────────────────────────────────────│
│ ───── ⬇ DROP HERE ⬇ ──────── (2px blue line) │
│                                         │
│  ┌~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ┐    │
│  │ ⋮⋮  📷  Page 3  ██████████ 80%│    │  ← Dragged item (shadow, 0.85 opacity)
│  │         3 sections              │    │
│  └~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ┘    │
│                                         │
│ ───── ⬆ DROP HERE ⬆ ──────── (2px blue line) │
│                                         │
│ ⋮⋮  📷  Page 2  ████████░░░░░░  60%   │
│         4 sections                      │
└─────────────────────────────────────────┘
```

**Visual feedback during drag:**

- Dragged item: `z-index: 100`, `box-shadow: 0 8px 24px rgba(0,0,0,0.15)`, `opacity: 0.85`, transform scale(1.02)
- Drop indicator: horizontal line, 2px height, primary blue `#2563EB`, full width with 16px inset on each side, 4px border radius on ends
- Other items: translateY animated 200ms ease-out to make space for the indicator
- Auto-scroll: when dragged item reaches 40px from top/bottom of the list container, list auto-scrolls at 1 item per 150ms

#### State: Dropped (success)

```
┌─────────────────────────────────────────┐
│ ⋮⋮  📷  Page 1  ██████████████ 100%   │
│         5 sections                      │
├─────────────────────────────────────────┤
│ ⋮⋮  📷  Page 3  ██████████░░░░  80%   │
│         3 sections                      │
├─────────────────────────────────────────┤
│ ⋮⋮  📷  Page 2  ████████░░░░░░  60%   │
│         4 sections                      │

┌─────────────────────────────────────────┐
│  ✅ Page order updated     [Undo]       │  ← Toast notification
│  ████████████████░░░░  (5s timer)       │
└─────────────────────────────────────────┘
```

- Item settles into new position with 200ms ease-out
- Toast slides in with "Page order updated" and [Undo] button
- Undo button available for 5 seconds
- Clicking Undo sends reversed order array to the reorder API

#### State: Conflict (409 from backend)

```
┌─────────────────────────────────────────┐
│ ❌ Page order was modified by another  │  ← Toast (alert role)
│    editor. Refresh to see latest.     │
│                        [Refresh]       │
└─────────────────────────────────────────┘
```

- All items snap back to their pre-drag positions with 200ms ease animation
- Red flash on all page items (200ms)
- Toast uses `role="alert"` for immediate screen reader announcement
- [Refresh] button triggers `window.location.reload()` or re-fetches page list

### 1.3 Add Page Interaction

**Between Pages (visible on hover):**

```
┌─────────────────────────────────────────┐
│ ⋮⋮  📷  Page 3                        │
├─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┤  ← 40px tall gap area
│  ┌─ [ + Add Page ] ──────────────────┐ │  ← Dashed border, center
│  └───────────────────────────────────┘ │
├─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┤
│ ⋮⋮  📷  Page 4                        │
└─────────────────────────────────────────┘
```

**Add Page Dialog (on click):**

```
┌─────────────────────────────────────────┐
│  Add Blank Page                      │
│                                      │
│  A new blank page will be inserted   │
│  after Page 3. It will have no       │
│  source image and no sections yet.   │
│                                      │
│  [Cancel]  [Add Page]                │
└─────────────────────────────────────────┘
```

- Clicking [Add Page] calls `POST /api/books/{bookId}/pages` with `{ insertAfterOrder: currentOrder }`
- New page appears immediately with status PENDING, pageNumber=0, gray thumbnail placeholder icon
- Optimistic insert: page appears in list, shifts other items down with 200ms animation
- On failure: remove inserted page, show error toast "Failed to add page"

### 1.4 Delete Page Interaction

**Delete Button:** Trash icon visible on page item hover, or in context menu (⋮)

**Confirmation Dialog:**

```
┌─────────────────────────────────────────┐
│  Delete Page 3?                        │
│                                         │
│  ⚠️  This will permanently delete the  │
│  page and all 5 sections on it.         │
│  This action cannot be undone.          │
│                                         │
│  [Cancel]  [Delete] (red destructive)   │
└─────────────────────────────────────────┘
```

- Delete button disabled when only one page remains (tooltip shown on hover)
- On confirmation: `DELETE /api/pages/{pageId}`
- Page item animates out: shrink height to 0 over 300ms, opacity fade
- Remaining items animate to fill the gap (translateY, 200ms)
- On failure: page reappears with 300ms expand animation, error toast

### 1.5 Keyboard Reorder (Accessibility)

- Focus page item in list (via Tab)
- Press Alt+↑ to move item up, Alt+↓ to move down
- Each key press triggers a single position shift
- Visual feedback: item highlights with blue left border during keyboard move
- Announcement: "Page {number} moved to position {newPosition}" via aria-live region
- After move completes: focus stays on the moved item

---

## 2. Translation Review Console

### 2.1 Full Wireframe

```
┌─────────────────────────────────────────────────────────────────────┐
│  ← Back to Book Console   Review: Page 3                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Navigation Header                                                  │
│  [← Previous Section]  Section 3 of 12  [Next Section →]           │
│  Page: [3 ▼]  Section: [2 ▼]                                       │
│                                                                     │
│  ┌─ Reference Image ───────────────────────────────────────────┐   │
│  │                                                              │   │
│  │           Cropped Section Image                              │   │
│  │           (Presigned URL, max-height: 240px)                 │   │
│  │           Click to expand to full height                     │   │
│  │                                                              │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  2 Translations Required · 2 Submitted                              │
│                                                                     │
│  ┌─────── Translation Card 1 ───────────┐ ┌─── Card 2 ──────────┐ │
│  │  👤 Kamal Perera                     │ │ 👤 Priya Seneviratne│ │
│  │  Submitted: 2 hours ago              │ │ 30 min ago          │ │
│  │  ┌─────────────────────────────┐     │ │ ┌────────────────┐  │ │
│  │  │  මාතාව සියලු දේවතාවුන්ගේ      │     │ │ මාතාවගේ සියලු │  │ │
│  │  │  ගුණ ගීතය මෙසේ දැක්වේ...    │     │ │ දේවතාවුන් ගේ │  │ │
│  │  └─────────────────────────────┘     │ │ └────────────────┘  │ │
│  │                         Status: PENDING  │  Status: PENDING   │ │
│  │  [✓ Approve] [✕ Reject]             │ │ [✓] [✕]            │ │
│  └────────────────────────────────────────────┴────────────────────────┘ │
│                                                                     │
│  ┌─ Editor Override ──────────────────────────────────────────────┐ │
│  │  [📋 Copy from Kamal]  [📋 Copy from Priya]              │ │
│  │                                                                   │ │
│  │  ┌───────────────────────────────────────────────────────────────┐   │ │
│  │  │  Type your own translation here (auto-approved as          │   │ │
│  │  │  Editor's Choice)                                       │   │ │
│  │  └───────────────────────────────────────────────────────────────┘   │ │
│  │                                                                   │ │
│  │  [Submit as Editor's Choice]                                      │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  Section Completion Status: ⏳ 2 pending, 2/2 translators submitted │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Translation Card States

#### Idle (Pending)

```
┌──────────────────────────────────────┐
│  👤 Kamal Perera                     │
│  ⏳ Submitted 2 hours ago           │
│                                      │
│  මාතාව සියලු දේවතාවුන්ගේ ගුණ ගීතය... │
│                                      │
│  [✓ Approve]  [✕ Reject]            │
└──────────────────────────────────────┘
```

**Visual specs:**

- Border: 1px solid `#E2E8F0` (slate-200)
- Background: white
- Border radius: 8px
- Padding: 16px
- Translator avatar: 32px circle, first letter if no image
- Timestamp: 12px, `#94A3B8` (slate-400), shows relative time
- Text body: 14px, line-height 1.6, wrap preserved

#### Approved

```
┌──────────────────────────────────────┐
│  👤 Kamal Perera           ✓ APPROVED │  ← Green badge top-right
│  ✅ Approved 30 seconds ago          │
│                                      │
│  මාතාව සියලු දේවතාවුන්ගේ ගුණ ගීතය... │
│                                      │
│  [✓ Approved]  [✕ Reject]           │  ← Approve disabled
└──────────────────────────────────────┘
```

**Visual specs:**

- Border: 2px solid `#22C55E` (green-500)
- Background: `#F0FDF4` (green-50)
- Badge: `#16A34A` background, white text, 12px, rounded-pill
- Green glow: `box-shadow: 0 0 8px rgba(34, 197, 94, 0.2)`
- Approver name shown in approval timestamp

#### Rejected

```
┌──────────────────────────────────────┐
│  👤 Kamal Perera         ✕ REJECTED   │
│  Rejected by Nimal Editor            │
│                                      │
│  ~~මාතාව සියලු දේවතාවුන්ගේ...~~    │  ← strikethrough
│                                      │
│  ▼ Show rejection reason              │  ← expandable
│                                      │
│  [✓ Approve (re-override)]         │  ← still available
└──────────────────────────────────────┘
```

**Visual specs:**

- Opacity: 0.6
- Border: 1px solid `#DC2626` (red-600)
- Background: `#FEF2F2` (red-50)
- Text: `text-decoration: line-through`
- Badge: red background, white text
- Expansion arrow: chevron rotates 180° when expanded

#### Editor's Choice

```
┌──────────────────────────────────────┐
│  👤 Jane Editor        ⭐ EDITOR'S    │
│                            CHOICE    │
│  Auto-approved (Editor's Choice)    │
│                                      │
│  මාතාවගේ සියලු දේවතාවුන් ගේ ගුණ...  │
│                                      │
│  ⭐ This translation was provided    │
│  by the editor and is auto-approved. │
└──────────────────────────────────────┘
```

**Visual specs:**

- Border: 2px solid `#A855F7` (purple-500)
- Background: `#FAF5FF` (purple-50)
- Badge: purple background, star icon, white text
- Slightly larger text (15px) to indicate authority
- No action buttons (auto-approved)

### 2.3 Approve Animation Sequence

```
1. [User clicks Approve]
        │
        ▼
2. Optimistic update:
   - Card border transitions from #E2E8F0 to #22C55E (200ms)
   - Background fades from white to #F0FDF4 (300ms)
   - "✓ APPROVED" badge scales in (0.8 → 1.0, 200ms ease-out)
   - Approve button becomes disabled, text changes to "✓ Approved"
   - Brief green glow appears (box-shadow, 400ms flash)
        │
        ▼
3. API call: PUT /api/translations/{id}/approve
        │
        ├── Success: ✅ toast "Translation approved" (green, 3s)
        │            → Invalidate section translations query
        │            → Invalidate page stats
        │
        └── Failure: ❌ toast "Failed to approve" (red, 5s)
                     → Revert card to Pending state
                     → Re-enable Approve button
```

### 2.4 Reject Animation Sequence

1. [Click Reject] → textarea slides down (200ms max-height animation):

   ```
   ┌──────────────────────────────────────┐
   │  Reason for rejection (optional)     │
   │  ┌──────────────────────────────────┐│
   │  │                                  ││
   │  │  (max 500 chars)                 ││
   │  └──────────────────────────────────┘│
   │  [Cancel]  [Submit]                  │
   └──────────────────────────────────────┘
   ```

2. Type reason (optional) → character counter updates live
3. [Submit] →
   - Card dims to 0.6 opacity (300ms)
   - Strikethrough appears on text (200ms width animation, left-to-right)
   - Red badge fades in (200ms)
   - Textarea collapses
   - Red border transitions in (200ms)

### 2.5 Editor Override Flow

```
[Editor types or clicks "Copy from..."]

Copy button:
  ┌───────────────────────────┐
  │ 📋 Copy from Kamal       │  → Click copies Card 1 text to textarea
  │ 📋 Copy from Priya       │  → Click copies Card 2 text to textarea
  └───────────────────────────┘
  → Brief flash on source card (200ms blue glow)
  → Textarea text updates immediately

[Submit as Editor's Choice]
  → POST /api/sections/{sectionId}/translations
  → On success:
    → New card appears at top: "⭐ Editor's Choice"
    → Purple border animation (200ms)
    → Toast "Editor's translation submitted and auto-approved"
  → On failure: error toast, keep editor text for retry
```

### 2.6 Navigation Flow

- **Previous Section / Next Section**: Navigates through sections on the same page
- **Wrapping**: Last section on page → first section of next page
- **Page dropdown**: Jump to a specific page, shows first section
- **Section dropdown**: Jump to a specific section on current page
- **Back to Book Console**: Returns to main console, Review tab stays active

---

## 3. Build Panel

### 3.1 Full Build Flow

```
┌─────────────────────────────────────────────────────────────┐
│  IDLE STATE                                                      │
│                                                                  │
│  ┌─ Summary ────────────────────────────────────────────────────────────┐    │
│  │  📊 Build Summary                                        │    │
│  │                                                           │    │
│  │  ✅ 290 of 320 sections approved (90.6%)                  │    │
│  │  ⚠️ 30 untranslated sections (will be skipped)           │    │
│  │  ⏳ 15 pending review                                     │    │
│  │                                                           │    │
│  │  [🔨 Build Book]  (enabled)                              │    │
│  └───────────────────────────────────────────────────────────┘    │
│                                                                  │
│  (or disabled state)                                             │
│                                                                  │
│  ┌─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐  │
│              [🔨 Build Book] (disabled)                         │
│              ⚠️ No approved translations — review first        │
│  └─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Confirmation Dialog (clicking Build):**

```
┌─────────────────────────────────────────────────────────┐
│  Build Finalized Book                                    │
│                                                          │
│  This will generate a PDF from all approved                  │
│  translations.                                           │
│                                                          │
│  ✅ 290 sections with approved translations              │
│     → Translated text will be rendered in the PDF        │
│                                                          │
│  ⚠️ 30 sections without approval                        │
│     → Original source text used (no translation)        │
│                                                          │
│  ⏳ 15 sections pending review                           │
│     → Original source text used (no translation)        │
│                                                          │
│  [Cancel]  [🔨 Build]                                   │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Building State

```
┌─────────────────────────────────────────────────────────────┐
│  BUILDING STATE                                            │
│                                                            │
│  Building Book — Version 3                                  │
│                                                            │
│  ┌─ Progress ─────────────────────────────────────────┐    │
│  │  ████████████████████░░░░░░░░░░░░░░░  64%         │    │
│  │                                                     │    │
│  │  Building page 23 of 45...                          │    │
│  │  Estimated time remaining: ~44 seconds              │    │
│  │                                                     │    │
│  │  [✕ Cancel Build]                                   │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                            │
└─────────────────────────────────────────────────────────────┘
```

**Progress polling cycle:**

```
Timer: 3s → after 30s: 5s → after 2min: 10s → after 5min: 15s

Each poll response:
  status: "BUILDING"
    currentPage: 23
    totalPages: 45
    estimatedRemainingMs: 44000
    → Update progress bar: (23/45) * 100 = 51.1%
    → Update ETA text: "~44 seconds"
    → Bar fill animates 600ms ease-out

  status: "COMPLETED"
    → Stop polling
    → Fill bar to 100% with green flash (400ms)
    → Transition to Completed state (500ms fade)

  status: "FAILED"
    → Stop polling
    → Transition to Failed state (200ms)
    → Show error message
```

### 3.3 Completed State

```
┌─────────────────────────────────────────────────────────────┐
│  COMPLETED STATE                                            │
│                                                             │
│  ┌─ Success ───────────────────────────────────────────┐    │
│  │  ✅ Build complete!                                  │    │
│  │                                                     │    │
│  │  Version 3                                           │    │
│  │  320 sections processed · 290 approved translations  │    │
│  │  Build time: 8 minutes 40 seconds                    │    │
│  │  Built by: Jane Editor · Jul 9, 2026 12:30 PM       │    │
│  │                                                     │    │
│  │  ┌─────────────────────────────────────────────┐    │    │
│  │  │  📥  Download PDF  [Gaha Ulela-v3.pdf]      │    │    │
│  │  └─────────────────────────────────────────────┘    │    │
│  │                                                     │    │
│  │  [🔗 Copy Link]                                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Download interaction:**

1. Click "Download PDF"
2. Page calls `GET /api/books/{bookId}/versions/{versionNumber}/download`
3. Backend returns presigned URL with 1-hour expiry + filename
4. Browser initiates download via `<a href={url} download={filename}>` or `window.open(url)`
5. Loading state: button shows spinner during URL fetch (200ms typical)
6. If expired: show "Link expired — generating new..." with spinner, then auto-trigger URL regeneration

**Copy Link interaction:**

1. Click "Copy Link"
2. Fetch presigned URL via same API endpoint
3. `navigator.clipboard.writeText(url)`
4. Toast: "Link copied!" (2s)
5. Fallback for non-HTTPS: show text field with selectable URL + "Copy manually"

### 3.4 Failed State

```
┌─────────────────────────────────────────────────────────────┐
│  FAILED STATE                                               │
│                                                             │
│  ┌─ Error ────────────────────────────────────────────┐    │
│  │  ❌  Build failed                                    │    │
│  │                                                      │    │
│  │  Error: S3 upload failed after 3 retries:            │    │
│  │  Connection timed out while uploading page 23 image   │    │
│  │                                                      │    │
│  │  [🔄 Retry Build]   [✕ Dismiss]                     │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

- **Error styling**: Red left border, red ❌ icon, error message in monospace code block
- **Retry**: Re-triggers build with confirmation (same confirmation dialog)
- **Dismiss**: Returns to Idle state with build summary; failed build remains in version history
- **Error types**:
  - S3/timeout: "S3 upload failed after {N} retries: {error}"
  - PDF generation: "PDF generation failed at page {N}: {error}"
  - Database: "Failed to read page {N}: {error}"
  - Cancellation: "Build cancelled by user"

### 3.5 Cancel Build Interaction

```
1. User clicks [✕ Cancel Build]
        │
        ▼
2. Confirmation dialog:
   ┌─────────────────────────────────────┐
   │  Cancel Build?                       │
   │                                      │
   │  Are you sure you want to cancel     │
   │  this build? Partial artifacts will  │
   │  be discarded.                       │
   │                                      │
   │  [No, Continue]  [Yes, Cancel]       │
   └─────────────────────────────────────┘
        │
        ▼
3. On confirm:
   → DELETE /api/books/{bookId}/builds/latest
   → Button shows spinner: "Cancelling..."
   → Timer (max 5s wait)
        │
        ├── Success (200 OK)
        │   → Return to Idle state
        │   → Toast: "Build cancelled"
        │
        └── Timeout/no response
             → Toast: "Failed to cancel — build may complete shortly"
             → Continue polling, show result
```

---

## 4. Version History Panel

### 4.1 Full Wireframe

```
┌─────────────────────────────────────────────────────────────┐
│  Version History                     [+ Create Version]    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📌 Current: Version 3                                      │
│                                                             │
│  ┌──── Version 3 ──────────────────────────────────────┐   │
│  │  v3  ✅ FINALIZED  ·  Jul 9, 2026, 12:30 PM         │   │
│  │  ⭐ CURRENT                                      │   │
│  │  320 sections · 290 approved · 8m 40s build           │   │
│  │  Built by: Jane Editor                              │   │
│  │  ┌─────────────────────────────────────────┐        │   │
│  │  │  📥 Download PDF  [Gaha Ulela-v3.pdf]       │        │   │
│  │  └─────────────────────────────────────────┘        │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  ▲ Hide details                                  │   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──── Version 2 ──────────────────────────────────────┐   │
│  │  v2  ❌ FAILED  ·  Jul 8, 2026, 10:15 AM            │   │
│  │  Error: PDF generation timed out after 5 min        │   │
│  │  Built by: Jane Editor                              │   │
│  │                                                     │   │
│  │  [🔄 Retry Build]  [✕ Dismiss]                     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──── Version 1 ──────────────────────────────────────┐   │
│  │  v1  ✅ FINALIZED  ·  Jul 7, 2026, 2:15 PM        │   │
│  │  280 sections · 260 approved · 7m 10s build         │   │
│  │  Built by: Sam Editor                               │   │
│  │                                                     │   │
│  │  [📥 Download]  [⭐ Set as Current]                │   │
│  └──────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──── Manual Version — Draft ────────────────────────┐   │
│  │  Label: "Proofread v2" (created manually)          │   │
│  │  v0  📄 DRAFT  ·  Jul 6, 2026, 4:00 PM            │   │
│  │  Changelog: "Added translations for chapters 1-5"│   │
│  │  No PDF available — run a build to generate        │   │
│  └──────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Version Item States

| State                   | Left Border          | Icon | Background | Actions Available        |
| ----------------------- | -------------------- | ---- | ---------- | ------------------------ |
| FINALIZED (current)     | Green `#22C55E`, 4px | ✅   | White      | Download, Copy Link      |
| FINALIZED (not current) | None                 | ✅   | White      | Download, Set as Current |
| FAILED                  | Red `#DC2626`, 3px   | ❌   | `#FEF2F2`  | Retry, Dismiss           |
| DRAFT                   | Blue `#3B82F6`, 3px  | 📄   | `#EFF6FF`  | (no download — no PDF)   |

### 4.3 Set as Current Interaction

1. User clicks "⭐ Set as Current" on a non-current finalized version
2. Confirmation: "Set Version {N} as the current version? This will mark it as the canonical version."
3. [Cancel] [Set as Current]
4. On success:
   - Previous current version: "⭐ Current" label removed, green border removed
   - New current version: label appears with slide-in (200ms from right), green border appears (200ms)
   - Toast: "Version {N} is now the current version"
5. On failure: error toast

### 4.4 Create Version Modal

```
┌─────────────────────────────────────────────┐
│  Create Version                                │
│                                                │
│  Version number will auto-increment to v{next} │
│                                                │
│  Label (optional)                              │
│  ┌─────────────────────────────────────────┐  │
│  │ e.g., "Proofread v2"                    │  │
│  └─────────────────────────────────────────┘  │
│                                                │
│  Changelog (optional)                          │
│  ┌─────────────────────────────────────────┐  │
│  │  e.g., "Added translations for          │  │
│  │  chapters 1-5"                          │  │
│  └─────────────────────────────────────────┘  │
│                                                │
│  Note: This creates a manual version label.      │
│  Use the Build panel to generate a PDF.        │
│                                                │
│  [Cancel]  [Create Version]                    │
└─────────────────────────────────────────────┘
```

- Modal: centered, backdrop, 500ms fade in/scale up
- Label max length: 100 chars
- Changelog max length: 500 chars
- On create: POST /api/books/{bookId}/versions, new item appears with DRAFT status

### 4.5 Download Interaction (from Version History)

Same as Build panel download:

1. Click Download → GET download API → presigned URL → `window.open` or `<a>` download
2. Show spinner during URL fetch
3. Handle expiry same as Build panel

---

## 5. Micro-interactions Summary

### 5.1 Page Reorder

| Interaction                  | Animation                                | Duration | Easing      |
| ---------------------------- | ---------------------------------------- | -------- | ----------- |
| Drag start (lift)            | Scale(1.02), shadow, opacity(0.85)       | 100ms    | ease-out    |
| Drop indicator appear        | Border fade-in + inset width grow        | 200ms    | ease        |
| Adjacent items shift         | translateY to make space                 | 200ms    | ease-out    |
| Drop settle                  | Scale(1.0), remove shadow, opacity(1.0)  | 200ms    | ease-out    |
| Conflict revert (snap back)  | translateY to original position          | 200ms    | ease-in-out |
| Conflict red flash           | background-color flash                   | 200ms    | ease        |
| Add page between (hover)     | border highlight, fade-in of button      | 200ms    | ease        |
| New page insert (optimistic) | Scale from 0 to 1, opacity 0→1           | 300ms    | ease-out    |
| Delete page remove           | Height shrink 100%→0, opacity 1→0        | 300ms    | ease-in     |
| Keyboard reorder             | translateY(48px), blue left border flash | 200ms    | ease-out    |

### 5.2 Translation Review

| Interaction                    | Animation                                                    | Duration | Easing      |
| ------------------------------ | ------------------------------------------------------------ | -------- | ----------- |
| Card approval                  | Border color transition, background tint, badge scale(0.8→1) | 300ms    | ease-out    |
| Card badge green glow          | box-shadow intensity                                         | 400ms    | ease-in-out |
| Card reject dim                | Opacity 1→0.6, strikethrough width 0→100%                    | 300ms    | ease        |
| Reject reason expand           | max-height 0→100px                                           | 200ms    | ease        |
| Reject reason collapse         | max-height 100→0px                                           | 200ms    | ease-in     |
| Copy from translator           | Source card blue flash                                       | 200ms    | ease        |
| Editor's Choice card appear    | Slide down + fade in                                         | 300ms    | ease-out    |
| Navigation (prev/next section) | Content slide in from left/right                             | 200ms    | ease-out    |

### 5.3 Build Panel

| Interaction              | Animation                             | Duration    | Easing      |
| ------------------------ | ------------------------------------- | ----------- | ----------- |
| Progress bar fill        | Width transition                      | 600ms       | ease-out    |
| Page counter update      | Number fade in/out                    | 200ms       | ease        |
| ETA value change         | Opacity fade                          | 200ms       | ease        |
| Build complete           | Green flash on bar                    | 400ms       | ease-in-out |
| Download button appear   | Scale(0.95→1.0) + fade                | 300ms       | ease-out    |
| Copy Link toast          | Slide in, 2s display, slide out       | 300ms+200ms | ease-in-out |
| Cancel build spinner     | Rotation                              | continuous  | linear      |
| Confirmation dialog open | Backdrop fade + modal scale(0.95→1.0) | 200ms       | ease-out    |

### 5.4 Version History

| Interaction            | Animation                   | Duration | Easing   |
| ---------------------- | --------------------------- | -------- | -------- |
| Version item expand    | max-height transition       | 200ms    | ease     |
| Set as Current         | Label slide-in from right   | 300ms    | ease-out |
| Create Version modal   | Backdrop fade + modal scale | 200ms    | ease-out |
| Download button appear | Same as build panel fade-in | 300ms    | ease-out |
| Version item hover     | Background highlight        | 150ms    | ease     |

---

## 6. Error States

### 6.1 Page Reorder Errors

| Error                      | Trigger                                        | Visual                                                                                        | Recovery                    |
| -------------------------- | ---------------------------------------------- | --------------------------------------------------------------------------------------------- | --------------------------- |
| **Conflict (409)**         | Simultaneous edit by another editor            | Revert optimistic reorder, toast "Modified by another editor — refresh" with [Refresh] button | Refresh page                |
| **Network error**          | API request fails (timeout, 500)               | Toast "Failed to update page order. [Retry]" (5s), revert to previous order                   | Click Retry                 |
| **Validation error (400)** | pageId doesn't belong to book                  | Toast "Some pages could not be reordered. [Refresh]"                                          | Refresh                     |
| **Delete last page**       | Editor tries to delete the only remaining page | Delete button disabled, tooltip "A book must have at least one page"                          | Cannot proceed              |
| **Delete network error**   | DELETE API fails                               | Toast "Failed to delete page. [Retry]"                                                        | Retry, page item re-appears |
| **Add page error**         | POST API fails                                 | Remove optimistic page item, toast "Failed to add page. [Retry]"                              | Retry                       |

### 6.2 Translation Review Errors

| Error                        | Trigger                                                 | Visual                                                                       | Recovery                                                     |
| ---------------------------- | ------------------------------------------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------ |
| **Approve conflict (409)**   | Translation already approved/rejected by another editor | Toast "This translation was already {status} by another editor."             | Auto-refresh translations list                               |
| **Reject network error**     | API request fails                                       | Toast "Failed to reject translation. [Retry]"                                | Keep card in Pending state with rejection reason in textarea |
| **Editor override error**    | POST API fails                                          | Toast "Failed to submit editor's translation. [Retry]"                       | Keep editor's text in textarea for retry                     |
| **Section image load error** | Presigned URL expired or S3 down                        | Image shows broken image placeholder with "Reference image unavailable" text | Retry button reloads the presigned URL                       |

### 6.3 Build Panel Errors

| Error                        | Trigger                                             | Visual                                                                                                           | Recovery                                       |
| ---------------------------- | --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| **Build failure (S3)**       | S3 upload timeout after 3 retries                   | Red error card with error message, [🔄 Retry Build] button                                                       | Click Retry to re-trigger build                |
| **Build failure (PDF gen)**  | PDF generation crashes on page N                    | Error card with page number, [🔄 Retry Build]                                                                    | Retry — same version number incremented        |
| **Build failure (DB)**       | Cannot read page/section data                       | Error card with DB error details, [🔄 Retry Build]                                                               | Retry                                          |
| **Cancel failed**            | DELETE endpoint fails after timeout                 | Toast "Failed to cancel — build may complete shortly"                                                            | Continue polling; build will complete normally |
| **Concurrent build**         | Editor clicks Build while another is active         | Button disabled, tooltip "A build is already in progress" input                                                  | Wait for current build to complete             |
| **No approved translations** | Editor clicks Build with zero approved translations | Confirmation dialog disabled or button grayed with tooltip "No approved translations — review and approve first" | Review translations first                      |
| **Download URL expired**     | User clicks download link after >1h                 | Toast "Download link expired — generating new link..."                                                           | Auto-generate new URL                          |

### 6.4 Version History Errors

| Error                                   | Trigger                     | Visual                                                  | Recovery                 |
| --------------------------------------- | --------------------------- | ------------------------------------------------------- | ------------------------ |
| **Download failed (version not found)** | Version or PDF file missing | Toast "Version not found or has no associated PDF file" | Provide [Refresh] button |
| **Create version error**                | POST API fails              | Toast "Failed to create version. [Retry]"               | Retry                    |
| **Set as Current error**                | PUT API fails               | Toast "Failed to update current version. [Retry]"       | Retry                    |

---

## 7. Empty States

### 7.1 Page List — No Pages

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│             📄                                      │
│                                                     │
│  No pages yet                                       │
│                                                     │
│  Upload a book first, then pages will               │
│  appear here after processing.                      │
│                                                     │
│  [Go to Book Settings]                              │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 7.2 Page List — No Sections on Pages

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│             🔍                                      │
│                                                     │
│  No sections detected                               │
│                                                     │
│  Process pages to detect sections before             │
│  translation progress can be tracked.                │
│                                                     │
│  [Go to First Page]                                 │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 7.3 Review Panel — No Translations for Section

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│             ⏳                                      │
│                                                     │
│  No translations submitted yet                      │
│                                                     │
│  This section is awaiting translations from          │
│  translators. Check back later or assign            │
│  translators to this book.                          │
│                                                     │
│  [Assign Translators]                                │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 7.4 Build Panel — No Builds Yet

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│             🔨                                      │
│                                                     │
│  No builds yet                                       │
│                                                     │
│  Approve some translations first, then use           │
│  the Build tab to generate your first PDF.            │
│                                                     │
│  [Go to Review]                                     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 7.5 Version History — No Versions

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│             📦                                      │
│                                                     │
│  No versions yet                                     │
│                                                     │
│  Use the Build panel to create your first            │
│  version, or create a manual version label           │
│  to organize your work.                             │
│                                                     │
│  [Go to Build Panel]                                │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 8. Component States Reference

### 8.1 PageListItem

| State                  | Visual                                                           | Interactions                             |
| ---------------------- | ---------------------------------------------------------------- | ---------------------------------------- |
| Default                | Thumbnail, page number, progress bar, drag handle, section count | Click navigates to page, drag to reorder |
| Active (selected)      | Blue left border (3px)                                           | Focus visible, keyboard shortcuts active |
| Dragging               | Shadow, elevated, opacity 0.85                                   | Moving with cursor                       |
| Adding (optimistic)    | Gray thumbnail placeholder, pulse animation                      | Not yet persisted, showing "Adding..."   |
| Deleting               | Height shrink, opacity fade out                                  | Being removed                            |
| Over limit (last page) | Delete button disabled, tooltip                                  | Cannot delete                            |

### 8.2 TranslationCard

| State           | Visual                                | Actions                                     |
| --------------- | ------------------------------------- | ------------------------------------------- |
| Pending         | White, neutral border                 | Approve, Reject                             |
| Approved        | Green border, green badge, green tint | Reject only (if re-override needed)         |
| Rejected        | Dimmed, strikethrough, red badge      | Approve (re-override), Expand reject reason |
| Editor's Choice | Purple border, purple star badge      | None (auto-approved)                        |
| Loading         | Skeleton card                         | Waiting for data                            |
| Error           | Red error banner in card              | Retry                                       |

### 8.3 BuildProgress

| State     | Visual                                                | Actions               |
| --------- | ----------------------------------------------------- | --------------------- |
| Idle      | Summary counts, [Build] button                        | Click Build           |
| Disabled  | Gray [Build] button, tooltip                          | Hover for explanation |
| Building  | Progress bar, percentage, page counter, ETA, [Cancel] | Cancel                |
| Completed | Green checkmark, version info, [Download] [Copy Link] | Download, Copy        |
| Failed    | Red X, error message, [Retry] [Dismiss]               | Retry, Dismiss        |

### 5.4 VersionItem

| State                   | Visual                                   | Actions                          |
| ----------------------- | ---------------------------------------- | -------------------------------- |
| FINALIZED (current)     | Green left border, ✅ badge, ⭐ Current  | Download, Copy Link, expand      |
| FINALIZED (not current) | Neutral                                  | Download, Set as Current, expand |
| FAILED                  | Red left border, ❌ badge, error message | Retry, Dismiss, expand           |
| DRAFT                   | Blue left border, 📄 badge, no PDF       | (expand only)                    |
