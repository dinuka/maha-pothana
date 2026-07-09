# Maha Pothana — Test Plan

## Scope

This test plan covers the core features of the Maha Pothana book translation platform. Since no test framework is configured, testing is manual and scenario-based.

## Test Categories

### 1. Authentication & Authorization

| TC-ID   | Scenario                    | Steps                                                                                      | Expected Result                                                       |
| ------- | --------------------------- | ------------------------------------------------------------------------------------------ | --------------------------------------------------------------------- |
| AUTH-01 | Google SSO login            | 1. Click "Sign in with Google" 2. Select Google account 3. Allow permissions               | Redirected to dashboard. User created with EDITOR + TRANSLATOR roles. |
| AUTH-02 | First-time login flow       | 1. Login with new Google account                                                           | User record created, both roles assigned, onboarding shown            |
| AUTH-03 | Returning user login        | 1. Login with existing Google account                                                      | Dashboard shown with existing roles and data                          |
| AUTH-04 | Super Admin role management | 1. Login as super admin 2. Navigate to Admin > Users 3. Change user role 4. User refreshes | Role change visible on user's next page load                          |
| AUTH-05 | Role-based nav visibility   | 1. Login as Editor-only 2. Login as Translator-only                                        | Editor sees Books/Upload; Translator sees Translate only              |
| AUTH-06 | Unauthenticated access      | 1. Visit any protected route without login                                                 | Redirected to login page                                              |
| AUTH-07 | Invalid Google token        | 1. Use expired/revoked Google token                                                        | Error message shown, login failed                                     |

### 2. Book Upload

| TC-ID     | Scenario                  | Steps                                                                                     | Expected Result                                                 |
| --------- | ------------------------- | ----------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| UPLOAD-01 | Upload valid PDF          | 1. Fill title/author/source language/target languages 2. Select valid PDF 3. Click Upload | Progress bar shown, then redirect to book console               |
| UPLOAD-02 | Duplicate book detection  | 1. Upload same file twice                                                                 | Error: "This book has already been uploaded" + link to existing |
| UPLOAD-03 | Invalid file type         | 1. Select non-PDF file                                                                    | Error: "Please upload a valid PDF"                              |
| UPLOAD-04 | Missing required fields   | 1. Leave title/author/source language/target languages empty 2. Click Upload              | Validation errors shown on empty fields                         |
| UPLOAD-05 | Large file upload         | 1. Upload 500MB+ PDF                                                                      | Progress bar works, no timeout, redirect on success             |
| UPLOAD-06 | Cancel upload             | 1. Start upload 2. Click Cancel                                                           | Upload cancelled, file not saved                                |
| UPLOAD-07 | Editor-only access        | 1. Login as translator 2. Navigate to /books/new                                          | 403 or hidden from nav                                          |
| UPLOAD-08 | Multiple target languages | 1. Select 2+ target languages 2. Upload                                                   | Book shows both languages in metadata                           |

### 3. Page Processing

| TC-ID   | Scenario                     | Steps                                                      | Expected Result                                                        |
| ------- | ---------------------------- | ---------------------------------------------------------- | ---------------------------------------------------------------------- |
| PAGE-01 | Auto page splitting          | 1. Upload book 2. Wait for processing                      | All pages extracted, numbered 1..N, status shows "Ready"               |
| PAGE-02 | Failed page split            | 1. Upload corrupted PDF                                    | Error shown, book status = FAILED, retry option                        |
| PAGE-03 | View page list               | 1. Open book console                                       | Page list shows all pages with status badges                           |
| PAGE-04 | Select page to edit          | 1. Click a page in sidebar                                 | Page image loaded in viewer                                            |
| PAGE-05 | Original page number display | 1. Upload book with roman-numbered pages 2. View page list | Pages show original labels (i, ii, 1, 1b) alongside sequential numbers |

### 4. Section Detection & Editing

#### 4a. Section Detection

| TC-ID   | Scenario                          | Steps                                                          | Expected Result                                                                                                                          |
| ------- | --------------------------------- | -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| SECT-01 | Trigger section detection         | 1. Open page with image loaded 2. Click "Detect Sections"      | Detection overlay appears with "Detecting sections..." spinner. All edit controls disabled except zoom.                                  |
| SECT-02 | Sections appear after detection   | 1. Click "Detect Sections" 2. Wait for completion              | Colored rectangles overlaid on page image with type labels. Overlay removed. Controls re-enabled. Toast: "Sections detected: {n} found". |
| SECT-03 | Detection failure — API error     | 1. Click "Detect Sections" on problematic page                 | Error banner: "Detection failed" + [Retry Detection] button. Page status = DETECTION_FAILED.                                             |
| SECT-04 | Detection failure — network error | 1. Click "Detect Sections" 2. Disconnect network mid-detection | Graceful error message with retry option. No phantom sections created.                                                                   |
| SECT-05 | Detection produces no results     | 1. Click "Detect Sections" on blank page                       | Message: "No sections detected" or empty result set. Page remains in current state.                                                      |
| SECT-06 | Re-detect after confirmation      | 1. Confirm sections 2. Click "Re-detect Sections"              | Confirmation dialog: "Re-detecting will replace all current sections. Continue?" [Cancel] [Continue].                                    |
| SECT-07 | Re-detect replaces sections       | 1. Confirm dialog → Continue                                   | Old sections replaced by new detection results. All new rectangles overlaid.                                                             |
| SECT-08 | Re-detect cancelled               | 1. Confirm dialog → Cancel                                     | Existing confirmed sections remain unchanged. No API call made.                                                                          |
| SECT-09 | ML detection returns all 6 types  | 1. Page with varied content 2. Detect sections                 | At least one section of each type (HEADER, PARAGRAPH, FOOTNOTE, IMAGE_CAPTION, PAGE_NUMBER, OTHER) appears where appropriate.            |
| SECT-10 | Detection confidence score        | 1. Inspect API response after detection                        | Each section optionally includes `detectionConfidence` (0.0–1.0) field.                                                                  |

#### 4b. Section Rectangle Manipulation

| TC-ID   | Scenario                        | Steps                                                            | Expected Result                                                                                                                            |
| ------- | ------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| SECT-11 | Click to select section         | 1. Click on a rectangle                                          | Rectangle gets white 2px border. Transformer handles appear at corners/edges. Type selector appears in toolbar.                            |
| SECT-12 | Click empty canvas to deselect  | 1. Select a rectangle 2. Click empty area on canvas              | Rectangle deselected. Transformer hidden. Type selector hidden.                                                                            |
| SECT-13 | Drag section to new position    | 1. Select rectangle 2. Click and drag to new location            | Rectangle moves smoothly. Coordinates update in real-time. Position values stored correctly.                                               |
| SECT-14 | Drag section outside canvas     | 1. Drag rectangle partially off-canvas edge                      | Rectangle is constrained — at minimum partially visible. No data loss.                                                                     |
| SECT-15 | Resize via corner handle        | 1. Select rectangle 2. Drag corner Transform handle              | Rectangle resizes proportionally or freely. New dimensions update correctly.                                                               |
| SECT-16 | Resize via edge handle          | 1. Select rectangle 2. Drag edge handle                          | Width or height changes independently.                                                                                                     |
| SECT-17 | Minimum section size constraint | 1. Try to resize below 10×10px                                   | Transformer `boundBoxFunc` prevents shrink below 10×10. Old size maintained.                                                               |
| SECT-18 | Maximum section size constraint | 1. Try to resize beyond canvas/image bounds                      | Rectangle constrained to image bounds (no constrain logic — verify behavior).                                                              |
| SECT-19 | Delete selected section         | 1. Select rectangle 2. Click Delete button or press Delete key   | Rectangle removed from canvas. Section count decreases. Undo available.                                                                    |
| SECT-20 | Delete with nothing selected    | 1. Click Delete while no section selected                        | Nothing happens. Delete button is disabled when no selection.                                                                              |
| SECT-21 | Add section via draw tool       | 1. Click "Add Section" 2. Mousedown on canvas 3. Drag 4. Mouseup | New PARAGRAPH section created with area >10×10px. Auto-selected with Transformer handles. Draw mode exits automatically.                   |
| SECT-22 | Draw tool — minimum area        | 1. Click "Add Section" 2. Drag less than 10×10px                 | No section created. Draw mode still active or exits (verify behavior).                                                                     |
| SECT-23 | Cancel draw mode via button     | 1. Click "Add Section" 2. Click "Cancel Draw"                    | Draw mode exits. No section created. Cursor returns to normal.                                                                             |
| SECT-24 | Cancel draw mode via Escape     | 1. Click "Add Section" 2. Press Escape                           | Draw mode exits. No section created.                                                                                                       |
| SECT-25 | Draw preview follows cursor     | 1. Click "Add Section" 2. Mousedown + drag on canvas             | Dashed preview rectangle follows mouse in real-time during drag.                                                                           |
| SECT-26 | Cursor changes in draw mode     | 1. Click "Add Section"                                           | Cursor changes to crosshair over canvas area.                                                                                              |
| SECT-27 | Change section type — dropdown  | 1. Select rectangle 2. Choose "FOOTNOTE" from type dropdown      | Rectangle color updates to orange (#F97316). Label updates to "FOOTNOTE". Type field saved correctly.                                      |
| SECT-28 | Change section type — all types | 1. Select rectangle 2. Change to each of the 6 section types     | Each type renders with correct color: HEADER=blue, PARAGRAPH=green, FOOTNOTE=orange, IMAGE_CAPTION=purple, PAGE_NUMBER=gray, OTHER=violet. |
| SECT-29 | Multiple sections visible       | 1. Add 3+ sections                                               | All sections rendered with correct colors, labels, and positions. No overlap rendering glitches.                                           |
| SECT-30 | Section hover opacity change    | 1. Hover mouse over a section rectangle                          | Rectangle fill opacity increases from 25% to ~40% (150ms transition).                                                                      |
| SECT-31 | Section label positioning       | 1. Inspect any section                                           | Type label text at top-left corner of rectangle with 4px offset. Font: 11px bold in matching color.                                        |
| SECT-32 | Section order assignment        | 1. Add sections top-to-bottom, left-to-right                     | Each section gets sequential `sectionOrder` value. Order preserved upon reload.                                                            |

#### 4c. Canvas Image Rendering

| TC-ID  | Scenario                          | Steps                                            | Expected Result                                                                                                                            |
| ------ | --------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| IMG-01 | Page image loads on canvas        | 1. Open page editor with valid imageUrl          | Page image rendered as canvas background (via `fillPatternImage` or `Konva.Image`). Image covers full stage. Placeholder text NOT visible. |
| IMG-02 | Image scales to fit container     | 1. Open page editor                              | Image width capped to container width minus padding (40px). Aspect ratio maintained. Image never scales up >100%.                          |
| IMG-03 | Loading spinner shown             | 1. Open page editor with slow-loading image      | Skeleton placeholder (aspect-ratio matching container) + spinner icon + "Loading page image..." text displayed.                            |
| IMG-04 | Image loaded state                | 1. Wait for image to load                        | Image becomes visible. Loading skeleton/spinner removed.                                                                                   |
| IMG-05 | Image error state                 | 1. Open page editor with broken/invalid imageUrl | "Failed to load page image" message + [Retry] button. No broken image icon.                                                                |
| IMG-06 | Retry after image load failure    | 1. See error state 2. Click Retry                | Image fetch retried. Loading spinner shown again. On success: image renders. On failure: error persists.                                   |
| IMG-07 | No image URL — empty state        | 1. Open page editor with null/undefined imageUrl | Centered: "No page image available" + subtitle "Upload a book and process it to see pages here". Back to book link available.              |
| IMG-08 | Sections render over image        | 1. Load page with sections                       | Section rectangles overlaid on top of the page image. Sections visible and interactive.                                                    |
| IMG-09 | Presigned URL passed correctly    | 1. Inspect network request for page data         | Response includes `imageUrl` field (presigned S3 URL), not raw `imageKey`.                                                                 |
| IMG-10 | Presigned URL expiry              | 1. Wait 1 hour 2. Refresh page                   | Image still loads (URL regenerated on each page fetch).                                                                                    |
| IMG-11 | Image dimensions stored correctly | 1. Open page editor 2. Inspect stage dimensions  | Stage width/height match image's natural dimensions (scaled down to fit, not scaled up).                                                   |

#### 4d. Toolbar Functionality

| TC-ID | Scenario                          | Steps                                                     | Expected Result                                                                           |
| ----- | --------------------------------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| TB-01 | Add Section button — default      | 1. Open page editor                                       | Button shows "[📐] Add Section" with normal background.                                   |
| TB-02 | Add Section button — active       | 1. Click "Add Section"                                    | Button switches to "[✕] Cancel Draw" with primary color background and white text.        |
| TB-03 | Add Section button — disabled     | 1. Start detection or save                                | "Add Section" button disabled during detection/save operations.                           |
| TB-04 | Delete button — disabled          | 1. Open page with no selection                            | Delete button disabled (grayed out, not clickable).                                       |
| TB-05 | Delete button — enabled           | 1. Click a section rectangle                              | Delete button becomes enabled.                                                            |
| TB-06 | Type selector — hidden            | 1. Open page, no section selected                         | Type dropdown NOT visible in toolbar.                                                     |
| TB-07 | Type selector — visible           | 1. Click a section rectangle                              | Type dropdown appears with current type selected. Shows all 6 section types.              |
| TB-08 | Type selector — disabled          | 1. Select section 2. Start detection/save                 | Type selector disabled during async operations.                                           |
| TB-09 | Undo button — disabled            | 1. Open page editor before any action                     | Undo button disabled (stack empty).                                                       |
| TB-10 | Undo button — enabled             | 1. Make an edit (add/delete/move)                         | Undo button becomes enabled.                                                              |
| TB-11 | Redo button — disabled            | 1. After undo or before any action                        | Redo button disabled (stack empty).                                                       |
| TB-12 | Redo button — enabled             | 1. Make edit 2. Press Undo                                | Redo button becomes enabled.                                                              |
| TB-13 | Detect Sections button — default  | 1. Open page editor                                       | Button shows "[✨] Detect Sections". Enabled when not in confirmed state.                 |
| TB-14 | Detect Sections button — disabled | 1. Start detection or save, OR page is in confirmed state | Button disabled. During detection: spinner replaces icon.                                 |
| TB-15 | Re-detect Sections button         | 1. Confirm sections successfully                          | Button text changes to "Re-detect Sections" with refresh icon.                            |
| TB-16 | Zoom Out button — enabled         | 1. Open page editor 2. Click −                            | Zoom decreases by 10%. Zoom label updates.                                                |
| TB-17 | Zoom Out button — at min (50%)    | 1. Click − repeatedly until minimum                       | Zoom stops at 50%. Button disabled or click has no effect.                                |
| TB-18 | Zoom label displays percentage    | 1. Zoom in/out                                            | Label shows current zoom as integer percentage (e.g., "100%", "80%", "150%").             |
| TB-19 | Zoom In button — enabled          | 1. Open page editor 2. Click +                            | Zoom increases by 10%. Zoom label updates.                                                |
| TB-20 | Zoom In button — at max (300%)    | 1. Click + repeatedly until maximum                       | Zoom stops at 300%. Button disabled or click has no effect.                               |
| TB-21 | Confirm Sections button — default | 1. Open page editor with sections                         | Button shows "[✓] Confirm Sections" with primary background.                              |
| TB-22 | Confirm Sections button — saving  | 1. Click "Confirm Sections"                               | Button shows spinner replacing checkmark icon. All edit controls disabled.                |
| TB-23 | Confirm Sections — no sections    | 1. Remove all sections 2. Check button state              | Confirm button disabled when no sections exist.                                           |
| TB-24 | Help button — toggles overlay     | 1. Click [?] Help button                                  | Keyboard shortcuts cheat sheet overlay appears. Click again or press Escape to close.     |
| TB-25 | Toolbar layout — desktop          | 1. View on >1024px viewport                               | Full horizontal toolbar with all controls visible. Labels displayed.                      |
| TB-26 | Toolbar layout — tablet           | 1. View on 768–1024px viewport                            | Toolbar wraps to two rows. Controls still accessible.                                     |
| TB-27 | Toolbar layout — mobile           | 1. View on <768px viewport                                | Single-row toolbar with horizontal scroll. Labels hidden. Essential controls shown first. |

#### 4e. Keyboard Shortcuts

| TC-ID | Scenario                         | Steps                                             | Expected Result                                                                             |
| ----- | -------------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| KB-01 | Delete key removes section       | 1. Select a section 2. Press Delete               | Selected section removed from canvas.                                                       |
| KB-02 | Backspace key removes section    | 1. Select a section 2. Press Backspace            | Selected section removed from canvas.                                                       |
| KB-03 | Ctrl+Z undos last action         | 1. Add a section 2. Press Ctrl+Z                  | Section removed (last action undone). Undo stack decreases by 1. Redo stack increases by 1. |
| KB-04 | Ctrl+Shift+Z redos last undo     | 1. Undo an action 2. Press Ctrl+Shift+Z           | Undone action reapplied. Redo stack decreases by 1.                                         |
| KB-05 | Ctrl+Y redos last undo           | 1. Undo an action 2. Press Ctrl+Y                 | Undone action reapplied (same as Ctrl+Shift+Z).                                             |
| KB-06 | Escape deselects section         | 1. Select a section 2. Press Escape               | Section deselected. Transformer hidden. Type selector hidden.                               |
| KB-07 | Escape cancels draw mode         | 1. Enter draw mode 2. Press Escape                | Draw mode exits. No section created.                                                        |
| KB-08 | + key zooms in                   | 1. Press + key                                    | Zoom increases by 10%. Zoom label updates.                                                  |
| KB-09 | = key zooms in (alternate)       | 1. Press = key                                    | Zoom increases by 10%. Same as + key.                                                       |
| KB-10 | - key zooms out                  | 1. Press - key                                    | Zoom decreases by 10%. Zoom label updates.                                                  |
| KB-11 | D key toggles draw mode          | 1. Press D                                        | Draw mode toggled. Button state updates. Same as clicking "Add Section".                    |
| KB-12 | Ctrl+S triggers save             | 1. Make edits 2. Press Ctrl+S                     | Same as clicking "Confirm Sections". Save operation triggered.                              |
| KB-13 | Shortcuts inactive in text input | 1. Focus a text input 2. Press keyboard shortcuts | Shortcuts do NOT fire when text input is focused.                                           |
| KB-14 | Tooltips show shortcut           | 1. Hover over Delete button                       | Tooltip: "Delete (Delete)".                                                                 |
| KB-15 | Keyboard shortcut cheat sheet    | 1. Click [?] Help button                          | Overlay shows all shortcuts in a table format.                                              |

#### 4f. Undo/Redo History

| TC-ID | Scenario                           | Steps                                 | Expected Result                                                    |
| ----- | ---------------------------------- | ------------------------------------- | ------------------------------------------------------------------ |
| UR-01 | Undo add section                   | 1. Add section via draw 2. Ctrl+Z     | Section removed. Previous state restored.                          |
| UR-02 | Redo add section                   | 1. Undo add 2. Ctrl+Shift+Z           | Section re-added.                                                  |
| UR-03 | Undo delete section                | 1. Delete section 2. Ctrl+Z           | Deleted section restored with original position, size, type.       |
| UR-04 | Redo delete section                | 1. Undo delete 2. Ctrl+Shift+Z        | Section removed again.                                             |
| UR-05 | Undo move section                  | 1. Drag section 2. Ctrl+Z             | Section returns to previous position (x, y).                       |
| UR-06 | Undo resize section                | 1. Resize section 2. Ctrl+Z           | Section returns to previous width, height, x, y.                   |
| UR-07 | Undo type change                   | 1. Change type 2. Ctrl+Z              | Section reverts to previous type with corresponding color.         |
| UR-08 | Multiple undo steps                | 1. Perform 3 actions 2. Ctrl+Z ×3     | All 3 actions undone in reverse order.                             |
| UR-09 | Redo stack cleared on new action   | 1. Undo 2. Make a new edit (not redo) | Redo stack cleared. Previously undone action cannot be redone.     |
| UR-10 | Stack cleared on confirm           | 1. Make edits 2. Confirm sections     | Undo/redo stacks cleared. Undo and Redo buttons disabled.          |
| UR-11 | Stack cleared on re-detect         | 1. Make edits 2. Re-detect sections   | Undo/redo stacks cleared. New sections from detection replace all. |
| UR-12 | Max 50 entries in undo stack       | 1. Perform 51 small edits             | Only the most recent 50 entries are kept. Oldest entry dropped.    |
| UR-13 | Memory/performance with 50 entries | 1. Perform 50 section modifications   | No noticeable lag or memory issues. Canvas remains responsive.     |
| UR-14 | Zoom is NOT undoable               | 1. Zoom in 2. Ctrl+Z                  | Zoom level unchanged. No entry added to undo stack.                |

#### 4g. Section Type Color Coding

| TC-ID  | Scenario                        | Steps                                     | Expected Result                                                                                 |
| ------ | ------------------------------- | ----------------------------------------- | ----------------------------------------------------------------------------------------------- |
| CLR-01 | HEADER section color            | 1. Create/change section to HEADER        | Fill: #3B82F6 at 25% opacity (`40` hex). Stroke: #3B82F6, 1px. Label: "HEADER" in bold #3B82F6. |
| CLR-02 | PARAGRAPH section color         | 1. Create/change section to PARAGRAPH     | Fill: #22C55E at 25% opacity. Stroke: #22C55E, 1px. Label: "PARAGRAPH" in bold #22C55E.         |
| CLR-03 | FOOTNOTE section color          | 1. Create/change section to FOOTNOTE      | Fill: #F97316 at 25% opacity. Stroke: #F97316, 1px. Label: "FOOTNOTE" in bold #F97316.          |
| CLR-04 | IMAGE_CAPTION section color     | 1. Create/change section to IMAGE_CAPTION | Fill: #A855F7 at 25% opacity. Stroke: #A855F7, 1px. Label: "IMAGE_CAPTION" in bold #A855F7.     |
| CLR-05 | PAGE_NUMBER section color       | 1. Create/change section to PAGE_NUMBER   | Fill: #6B7280 at 25% opacity. Stroke: #6B7280, 1px. Label: "PAGE_NUMBER" in bold #6B7280.       |
| CLR-06 | OTHER section color             | 1. Create/change section to OTHER         | Fill: #8B5CF6 at 25% opacity. Stroke: #8B5CF6, 1px. Label: "OTHER" in bold #8B5CF6.             |
| CLR-07 | Selected section — white stroke | 1. Select any section                     | Stroke changes to white (#fff), 2px width. All other properties unchanged.                      |

#### 4h. Zoom and Pan Interactions

| TC-ID   | Scenario                           | Steps                                                           | Expected Result                                                                                    |
| ------- | ---------------------------------- | --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| ZOOM-01 | Zoom in via button                 | 1. Click + button 5 times                                       | Zoom increases from 100% → 110% → 120% → 130% → 140% → 150%. Canvas scales with smooth transition. |
| ZOOM-02 | Zoom out via button                | 1. Click − button 5 times                                       | Zoom decreases from 100% → 90% → 80% → 70% → 60% → 50%. Canvas scales with smooth transition.      |
| ZOOM-03 | Zoom in via keyboard (+)           | 1. Press + key 3 times                                          | Same as clicking + button 3 times.                                                                 |
| ZOOM-04 | Zoom out via keyboard (-)          | 1. Press - key 3 times                                          | Same as clicking - button 3 times.                                                                 |
| ZOOM-05 | Zoom minimum (50%)                 | 1. Click − until min                                            | Zoom does not go below 50%. Button disabled.                                                       |
| ZOOM-06 | Zoom maximum (300%)                | 1. Click + until max                                            | Zoom does not go above 300%. Button disabled.                                                      |
| ZOOM-07 | Zoom preserves section coordinates | 1. Zoom to 200% 2. Check section data                           | Section coordinates (x, y, width, height) remain unchanged. Only visual scale changes.             |
| ZOOM-08 | Zoom preserves image position      | 1. Zoom in 2. Scroll/pan within container                       | Canvas container scrolls (overflow: auto). User can pan to see zoomed-in areas.                    |
| ZOOM-09 | Zoom level display                 | 1. Zoom to 73% (7 clicks down from 100%)                        | Label shows "70%" (rounded to nearest integer).                                                    |
| ZOOM-10 | Zoom with sections present         | 1. Add sections 2. Zoom in/out                                  | Sections scale with canvas. Transform handles scale correctly. All interactions work.              |
| ZOOM-11 | Pan when zoomed in                 | 1. Zoom to 150% 2. Scroll container horizontally and vertically | Canvas scrolls. All areas reachable. Sections remain interactive.                                  |

#### 4i. Save/Confirm Flow with API Error Handling

| TC-ID   | Scenario                          | Steps                                                  | Expected Result                                                                                                                       |
| ------- | --------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| SAVE-01 | Confirm sections — success        | 1. Add sections 2. Click "Confirm Sections"            | Sections saved to API. Page status = SECTIONS_CONFIRMED. Success toast: "✓ Sections confirmed!"                                       |
| SAVE-02 | Confirm sections — payload format | 1. Click "Confirm Sections" 2. Inspect network request | Request body is raw array `[{id, sectionOrder, type, x, y, width, height}, ...]` — NOT wrapped in `{sections: ...}`.                  |
| SAVE-03 | Confirm sections — sectionOrder   | 1. Verify saved sections in DB                         | Each section has sequential `sectionOrder` based on position (top-to-bottom, left-to-right).                                          |
| SAVE-04 | Confirm sections — API 422 error  | 1. Send malformed payload to API                       | Error response. Error toast: "Failed to save sections" + [Retry]. Controls re-enabled.                                                |
| SAVE-05 | Confirm sections — network error  | 1. Click Confirm 2. Disconnect network                 | Error toast: "Failed to save sections" + [Retry]. Undo/redo stacks NOT cleared.                                                       |
| SAVE-06 | Confirm sections — retry on fail  | 1. See error 2. Click Retry (or click Confirm again)   | Save re-attempted. On success: toast, confirmation state. On failure: error persists.                                                 |
| SAVE-07 | Confirm sections — server 500     | 1. Backend returns 500 error                           | Error toast. Page status unchanged. Sections still visible on canvas.                                                                 |
| SAVE-08 | Confirm sections — UI transition  | 1. Click Confirm 2. Observe button state               | "Confirm Sections" button shows spinner. All edit controls disabled. On success: button returns to normal with possible state change. |
| SAVE-09 | Confirmed state — re-edit         | 1. Confirm sections 2. Modify sections 3. Re-confirm   | Changes saved. New confirmation overwrites previous.                                                                                  |
| SAVE-10 | Confirm with no sections          | 1. Delete all sections 2. Click Confirm                | Confirm button disabled or shows warning "No sections to confirm".                                                                    |
| SAVE-11 | Crop sections triggered           | 1. Confirm sections 2. Check Celery logs               | `crop_sections` task enqueued after successful save.                                                                                  |
| SAVE-12 | Crop sections — success           | 1. Wait for crop task to complete                      | Each section gets `croppedImageKey` in MongoDB. Cropped images stored in S3 at `books/{bookId}/sections/{sectionId}.png`.             |
| SAVE-13 | Crop sections — failure           | 1. Crop task fails (e.g., invalid coordinates)         | Error logged. Section remains without cropped image. Retry mechanism expected.                                                        |

### 5. Translation

| TC-ID    | Scenario                                | Steps                                                                        | Expected Result                                                               |
| -------- | --------------------------------------- | ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| TRANS-01 | Get next section                        | 1. Open Translate page 2. Click "Next Section"                               | Random untranslated section displayed with auto-translated text               |
| TRANS-02 | Submit translation                      | 1. Enter translated text 2. Click Save                                       | "Translation saved" toast. Section removed from queue.                        |
| TRANS-03 | Submit with exact letter                | 1. Enter translated text 2. Enter exact letter transliteration 3. Click Save | Both fields saved. Section shows exact letter field on review.                |
| TRANS-04 | Empty queue                             | 1. Translate all assigned sections 2. Click "Next"                           | "All sections translated!" message                                            |
| TRANS-05 | Page context viewing                    | 1. Open a section 2. Click "View Full Page"                                  | Full page shown with section highlighted                                      |
| TRANS-06 | Navigate to adjacent pages              | 1. Click "Previous Page" / "Next Page"                                       | Adjacent page loaded, context updated. Page labels show `originalPageNumber`. |
| TRANS-07 | Zoom in/out                             | 1. Click + / - zoom buttons                                                  | Image scales, zoom % updates. Reset works.                                    |
| TRANS-08 | Skip section                            | 1. Click "Skip"                                                              | Next section loaded. Skipped section returns to pool.                         |
| TRANS-09 | Add comment                             | 1. Type comment 2. Click Post                                                | Comment appears with name + timestamp                                         |
| TRANS-10 | Threaded replies                        | 1. Click "Reply" on existing comment 2. Type 3. Post                         | Nested reply shown under parent                                               |
| TRANS-11 | Multiple translators per section        | 1. Set translator count to 2 2. Two translators each translate same section  | Both saved. Section complete only after N submissions.                        |
| TRANS-12 | See own pending translation             | 1. Submit translation 2. Re-open section                                     | "My previous submission" panel shows own pending translation. Edit allowed.   |
| TRANS-13 | Cannot see others' pending translations | 1. Translator A submits 2. Translator B opens same section                   | Translator B does not see Translator A's pending translation                  |
| TRANS-14 | See others' approved translation        | 1. Editor approves A's translation 2. Translator B reopens section           | Translator B sees A's approved translation and can comment                    |

#### 5a. Auto-Load & Tab System

| TC-ID     | Scenario                         | Steps                                                     | Expected Result                                                          |
| --------- | -------------------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------ |
| TRANS-A01 | Auto-load first section on mount | 1. Open `/translate` 2. Wait for mount                    | First untranslated section loaded automatically (no "Next" click needed) |
| TRANS-A02 | Auto-load respects filters       | 1. Set lang=si, page=3 2. Reload page                     | First section matching si + page=3 loaded                                |
| TRANS-A03 | Tab bar renders with 3 tabs      | 1. Login as editor 2. Open `/translate`                   | Translate, History, Stats tabs visible                                   |
| TRANS-A04 | Translator sees 2 tabs           | 1. Login as translator 2. Open `/translate`               | Translate and History tabs only (Stats hidden)                           |
| TRANS-A05 | Default tab is Translate         | 1. Open `/translate` without `?tab=` param                | Translate tab active by default                                          |
| TRANS-A06 | Tab switch updates URL           | 1. Click History tab                                      | URL updates to `?tab=history`                                            |
| TRANS-A07 | Tab state survives reload        | 1. Click History tab 2. Reload page                       | History tab remains active                                               |
| TRANS-A08 | Stats tab editor-only            | 1. Login as translator 2. Try to navigate to `?tab=stats` | Stats tab not shown, URL param ignored or redirected to translate tab    |

#### 5b. Source Text Side-by-Side

| TC-ID     | Scenario                         | Steps                                                  | Expected Result                                              |
| --------- | -------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------ |
| TRANS-S01 | Source text panel visible        | 1. Open Translate tab with section loaded              | Two-column layout: image+source left, editor right           |
| TRANS-S02 | Source text labeled              | 1. Inspect source text panel                           | Header shows "Source Text" with icon                         |
| TRANS-S03 | Source text read-only            | 1. Try to click/type in source text panel              | No cursor, no editing possible                               |
| TRANS-S04 | Missing original text fallback   | 1. Section with empty `originalText` 2. Open Translate | Message: "Original text not available — use the image above" |
| TRANS-S05 | Mobile stacked layout            | 1. View on <768px viewport                             | Stacked: image, source text, then editor                     |
| TRANS-S06 | Auto-translation prefills editor | 1. Section with auto-translation from LibreTranslate   | Translation textarea pre-filled with auto-translated text    |
| TRANS-S07 | Edit original text link (editor) | 1. Login as editor 2. View source text panel           | "Edit original text" link visible, navigates to page editor  |
| TRANS-S08 | No edit link for translator      | 1. Login as translator 2. View source text panel       | "Edit original text" link NOT visible                        |

#### 5c. Translation History (US-TR-1)

| TC-ID     | Scenario                         | Steps                                                                | Expected Result                                                                                 |
| --------- | -------------------------------- | -------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| TRANS-H01 | History tab renders list         | 1. Click History tab                                                 | List of past translations shown, sorted most recent first                                       |
| TRANS-H02 | History item fields              | 1. Inspect first history item                                        | Shows: thumbnail, page number, section order, text snippet (≤80 chars), status badge, timestamp |
| TRANS-H03 | Status badge colors              | 1. View history items                                                | APPROVED=green, REJECTED=red, PENDING=amber                                                     |
| TRANS-H04 | Infinite scroll loads more       | 1. Scroll to bottom of history list                                  | Next batch of items appended, loading indicator shown                                           |
| TRANS-H05 | Cursor-based pagination          | 1. Scroll through 3 pages of history                                 | Items contiguous, no duplicates, no gaps                                                        |
| TRANS-H06 | End of history                   | 1. Scroll through all items                                          | No more fetches, list ends                                                                      |
| TRANS-H07 | Empty history state              | 1. Translator with no submissions 2. Open History                    | "No translations yet — start translating!" with link to Translate tab                           |
| TRANS-H08 | Click item navigates to section  | 1. Click a history item                                              | Navigates to `/translate?section={sectionId}`                                                   |
| TRANS-H09 | Translator sees own history only | 1. Login as translator-a 2. Open History                             | Only translator-a's translations shown                                                          |
| TRANS-H10 | Editor sees all history          | 1. Login as editor 2. Open History                                   | All translators' translations shown                                                             |
| TRANS-H11 | Badge updates on approve         | 1. Translator submits 2. Editor approves 3. Translator views History | Badge changes from PENDING to APPROVED                                                          |
| TRANS-H12 | History filters independent      | 1. Set lang=si on Translate 2. Switch to History 3. Set lang=ta      | History shows ta, Translate still has si                                                        |

#### 5d. Translation Statistics (US-TR-2)

| TC-ID     | Scenario                         | Steps                                                            | Expected Result                                               |
| --------- | -------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------- |
| TRANS-T01 | Stats tab editor-only            | 1. Login as translator 2. Open `/translate`                      | Stats tab NOT visible                                         |
| TRANS-T02 | Stats card renders               | 1. Login as editor 2. Click Stats tab                            | Progress bar, approved/pending/in-progress/total counts shown |
| TRANS-T03 | Progress bar matches data        | 1. View progress bar                                             | Bar fill width matches percentage displayed                   |
| TRANS-T04 | Per-language breakdown           | 1. Multi-language book 2. View Stats                             | Language cards shown with correct per-language stats          |
| TRANS-T05 | Per-page grid                    | 1. View Stats tab                                                | Color-coded cells: green=100%, yellow=partial, gray=0%        |
| TRANS-T06 | Stats refresh every 30s          | 1. Open Stats 2. Submit translation from another tab 3. Wait 30s | Stats update automatically                                    |
| TRANS-T07 | Stats cached in Redis            | 1. GET stats 2. GET stats again within 30s                       | Second request served from cache                              |
| TRANS-T08 | Cache invalidated on translation | 1. GET stats 2. Submit translation 3. GET stats                  | Fresh data returned                                           |
| TRANS-T09 | Empty book stats                 | 1. Book with 0 sections 2. View Stats                            | Shows 0/0, 0%                                                 |

#### 5e. Translator Performance Stats (US-TR-3)

| TC-ID     | Scenario                             | Steps                                                                 | Expected Result                                                       |
| --------- | ------------------------------------ | --------------------------------------------------------------------- | --------------------------------------------------------------------- |
| TRANS-P01 | Translator table renders             | 1. Login as editor 2. Open Stats tab                                  | Table with Name, Assigned, Approved, Rejected, Rate, Avg Time columns |
| TRANS-P02 | Default sort by approval rate        | 1. View translator table                                              | Rows sorted by approval rate descending                               |
| TRANS-P03 | Sort by any column                   | 1. Click "Name" header                                                | Table sorts by name. Click again = reverse sort                       |
| TRANS-P04 | Approval rate correct                | 1. View translator row                                                | = approved / (approved + rejected) \* 100, rounded to 1 decimal       |
| TRANS-P05 | Zero submissions shows "No activity" | 1. Translator with no submissions 2. View Stats                       | Row shows "—" for metrics, not 0% or N/A                              |
| TRANS-P06 | Click row expands activity           | 1. Click translator row                                               | Row expands to show last 10 submissions                               |
| TRANS-P07 | Translator cannot see others' stats  | 1. Login as translator 2. Attempt `/api/books/{id}/translators/stats` | API returns 403 Forbidden                                             |

#### 5f. Filters (US-TR-4)

| TC-ID     | Scenario                           | Steps                                                           | Expected Result                                                         |
| --------- | ---------------------------------- | --------------------------------------------------------------- | ----------------------------------------------------------------------- |
| TRANS-F01 | Filter bar visible                 | 1. Open `/translate`                                            | Language dropdown, page dropdown, status dropdown, clear button visible |
| TRANS-F02 | Language filter hidden single lang | 1. Book with 1 target language 2. View filters                  | Language dropdown not shown                                             |
| TRANS-F03 | Filter applies immediately         | 1. Select lang=si                                               | Next section fetched with `language=si`                                 |
| TRANS-F04 | Filters compose (AND logic)        | 1. Select lang=si, page=3, status=PENDING                       | API called with all three params                                        |
| TRANS-F05 | Filters persist in URL             | 1. Set lang=si, page=3 2. Check URL                             | URL shows `?lang=si&page=3`                                             |
| TRANS-F06 | URL params survive reload          | 1. Set filters 2. Reload page                                   | Filters restored from URL                                               |
| TRANS-F07 | Clear filters resets defaults      | 1. Set filters 2. Click Clear                                   | All filters reset, URL params cleared                                   |
| TRANS-F08 | History filters independent        | 1. Set lang=si on Translate 2. Switch to History 3. Set lang=ta | History shows ta, Translate still has si                                |
| TRANS-F09 | No match empty state               | 1. Set filters matching nothing 2. Click Next                   | "No sections match your filters" with Clear Filters CTA                 |
| TRANS-F10 | Invalid URL params handled         | 1. Navigate to `?lang=xyz&page=-1`                              | Invalid params ignored, defaults used, no crash                         |

#### 5g. Auto-save Drafts (US-TR-6)

| TC-ID     | Scenario                          | Steps                                                             | Expected Result                                       |
| --------- | --------------------------------- | ----------------------------------------------------------------- | ----------------------------------------------------- |
| TRANS-D01 | Draft saves after 5s inactivity   | 1. Type in textarea 2. Stop typing 3. Wait 5s                     | "Draft saved ✓" indicator appears briefly             |
| TRANS-D02 | Draft debounce resets on typing   | 1. Type 2. Wait 3s 3. Type again 4. Wait 5s                       | Draft saves only after final 5s of inactivity         |
| TRANS-D03 | Draft does not save empty text    | 1. Clear textarea 2. Wait 5s                                      | No draft saved                                        |
| TRANS-D04 | Draft prefills on section load    | 1. Save draft for section A 2. Return to section A                | Translation textarea prefilled with draft text        |
| TRANS-D05 | Draft deleted on submit           | 1. Save draft 2. Submit translation                               | Draft deleted from TranslationDrafts collection       |
| TRANS-D06 | Draft not created if already done | 1. Section already translated by this translator 2. Open section  | No draft created                                      |
| TRANS-D07 | Unsaved changes warning           | 1. Type translation 2. Try to close tab                           | Browser shows "You have unsaved changes" confirmation |
| TRANS-D08 | No warning when clean             | 1. Open section 2. Don't type 3. Close tab                        | No warning shown                                      |
| TRANS-D09 | Draft expires after 24h           | 1. Create draft 2. Set createdAt to 25h ago 3. GET draft          | 404 — draft not found                                 |
| TRANS-D10 | Drafts per-translator per-section | 1. Translator A saves draft for section X 2. Translator B opens X | B does NOT see A's draft                              |
| TRANS-D11 | POST draft creates                | 1. POST `{ sectionId, translatedText }`                           | 200: `{ draftId, updatedAt }`                         |
| TRANS-D12 | POST draft upserts                | 1. POST draft 2. POST again same sectionId                        | Draft updated, same draftId                           |
| TRANS-D13 | GET draft returns                 | 1. Create draft 2. GET `?sectionId=X`                             | Returns draft with text                               |
| TRANS-D14 | GET draft 404                     | 1. GET nonexistent section                                        | 404: `{ "detail": "No draft found" }`                 |
| TRANS-D15 | DELETE draft success              | 1. Create draft 2. DELETE by draftId                              | 200: `{ "status": "deleted" }`                        |
| TRANS-D16 | localStorage fallback             | 1. Mock API delay 10s 2. Type translation                         | Draft saved to localStorage immediately               |

### 6. Book Organization & Publishing

#### 6a. Page Organization (US-5.1)

| TC-ID  | Scenario                        | Steps                                       | Expected Result                                                                                   |
| ------ | ------------------------------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| ORG-01 | Drag reorder page               | 1. Drag page to new position in list        | Page order updates, `order` field reflects new position, `pageNumber` unchanged                   |
| ORG-02 | Reorder persists on reload      | 1. Reorder pages 2. Refresh page            | New order preserved                                                                               |
| ORG-03 | Add blank page                  | 1. Click "Add Page" between pages           | New Page with pageNumber=0, originalPageNumber="inserted", order at insertion point               |
| ORG-04 | Delete page                     | 1. Click delete 2. Confirm in dialog        | Page + all child sections/translations/comments deleted. Remaining orders compacted.              |
| ORG-05 | Delete prevents last page       | 1. Try to delete only page                  | Delete disabled with tooltip "Book must have at least one page"                                   |
| ORG-06 | Reorder conflict detection      | 1. Two editors reorder simultaneously       | Toast "Page order was modified by another editor — refresh"                                       |
| ORG-07 | Reorder undo                    | 1. Reorder pages 2. Press Ctrl+Z            | Order reverts to previous state                                                                   |
| ORG-08 | Add sections to blank page      | 1. Create blank page 2. Open canvas editor  | Sections can be added/detected on blank page just like regular pages                              |
| ORG-09 | Delete page confirmation dialog | 1. Click delete on page                     | Dialog shows "Delete Page N?" with section count and warning text. Cancel closes, Delete removes. |
| ORG-10 | Page history panel              | 1. Open page editor with confirmed sections | History timeline shows past saves with timestamps and editor names                                |
| ORG-11 | Restore section snapshot        | 1. Click restore on historical snapshot     | Sections replaced with historical version                                                         |
| ORG-12 | Section edit history tracked    | 1. Edit sections 2. Save changes            | New SectionEditHistory entry created for each save                                                |
| ORG-13 | Big page list (500+ pages)      | 1. Reorder near bottom of long list         | Auto-scroll during drag works, performance acceptable                                             |

#### 6b. Filter & Sort (US-5.2)

| TC-ID  | Scenario                        | Steps                                    | Expected Result                                                |
| ------ | ------------------------------- | ---------------------------------------- | -------------------------------------------------------------- |
| FLT-01 | Filter by status - All          | 1. Click "All" filter                    | All pages shown                                                |
| FLT-02 | Filter by status - Completed    | 1. Click "Completed" filter              | Only pages with 100% approved sections shown                   |
| FLT-03 | Filter by status - Not Started  | 1. Click "Not Started" filter            | Pages with 0 submitted translations shown                      |
| FLT-04 | Filter by status - In Progress  | 1. Click "In Progress" filter            | Pages with partial translation shown                           |
| FLT-05 | Filter by status - Needs Review | 1. Click "Needs Review" filter           | Pages with all sections submitted, awaiting approval           |
| FLT-06 | Sort by page order (asc)        | 1. Select sort -> Page Order Asc         | Ordered by `order` ascending                                   |
| FLT-07 | Sort by translation % (desc)    | 1. Select sort -> % Descending           | Most complete pages first                                      |
| FLT-08 | Filter + sort combination       | 1. Filter=Completed 2. Sort=% Asc        | Completed pages sorted least-to-most complete                  |
| FLT-09 | Filter state in URL             | 1. Set filter=in_progress 2. Reload page | Filter persists from URL                                       |
| FLT-10 | Progress bar colors             | 1. View pages at 0%, 50%, 100%           | 0%=gray, 1-99%=blue, 100%=green                                |
| FLT-11 | Summary stats bar               | 1. View page list                        | Shows total pages, sections, translated, pending, completion % |
| FLT-12 | Empty filter result             | 1. Filter matching zero pages            | "No pages match filter" with "Clear filter" CTA                |
| FLT-13 | Pre-detection state             | 1. Book with no sections on pages        | "Process pages first to see translation progress"              |
| FLT-14 | Sticky filter bar               | 1. Scroll through long page list         | Filter/sort bar remains visible                                |

#### 6c. Translation Review (US-5.3)

| TC-ID  | Scenario                            | Steps                                                 | Expected Result                                                                  |
| ------ | ----------------------------------- | ----------------------------------------------------- | -------------------------------------------------------------------------------- |
| REV-01 | View all translations for section   | 1. Open review console for section                    | All N submitted translations displayed side by side                              |
| REV-02 | Approve one translation             | 1. Click Approve on translation A                     | Translation A gets green "Approved" badge. isApproved=true                       |
| REV-03 | Approve multiple translations       | 1. Approve A 2. Approve B                             | Both A and B approved. Section considered translated.                            |
| REV-04 | Reject a translation                | 1. Click Reject on translation A                      | Translation A dimmed, strikethrough, red "Rejected" badge                        |
| REV-05 | Reject with reason                  | 1. Click Reject 2. Type reason 3. Submit              | Translation.rejectionReason saved. Rejected badge shown.                         |
| REV-06 | Reject all translations -> re-entry | 1. Reject all N translations                          | Section status -> pending. Re-enters translation pool.                           |
| REV-07 | Re-entry notification               | 1. All translations rejected                          | Notification sent to translators: "Section on page N needs re-translation"       |
| REV-08 | Editor override translation         | 1. Type own text 2. Click "Submit as Editor's Choice" | Editor's version saved as Translation, isApproved=true labeled "Editor's Choice" |
| REV-09 | Copy from submitted translation     | 1. Click "Copy from Kamal" on editor override         | Editor's textarea filled with Kamal's translation text                           |
| REV-10 | Blocked translator review           | 1. Blocked user's translation visible                 | Translation shown with "Blocked User" label, still approve/rejectable            |
| REV-11 | Audit trail created                 | 1. Approve + reject some translations                 | TranslationHistoryItem created for each action (APPROVED/REJECTED)               |
| REV-12 | Review navigation                   | 1. Navigate between sections                          | Keyboard prev/next, section counter "Section 3 of 12"                            |

#### 6d. Build Book (US-5.4)

| TC-ID  | Scenario                                | Steps                                          | Expected Result                                                      |
| ------ | --------------------------------------- | ---------------------------------------------- | -------------------------------------------------------------------- |
| BLD-01 | Build button enabled                    | 1. Book has approved translations              | Build button active                                                  |
| BLD-02 | Build button disabled - no sections     | 1. Book with no sections                       | Disabled, tooltip: "No sections detected"                            |
| BLD-03 | Build button disabled - no approvals    | 1. Sections exist but no approved translations | Disabled, tooltip: "No approved translations"                        |
| BLD-04 | Build summary panel                     | 1. View build panel                            | Shows total/approved/pending/untranslated counts with warnings       |
| BLD-05 | Confirmation dialog before build        | 1. Click Build                                 | Dialog shows skipped sections count, Cancel/Build buttons            |
| BLD-06 | Build progress polling                  | 1. After starting build                        | Frontend polls GET /api/books/{bookId}/builds/latest every 3s        |
| BLD-07 | Progress bar during build               | 1. Build in progress                           | Shows "Building page X of Y..." with progress fill                   |
| BLD-08 | Cancel build                            | 1. Click Cancel Build during build             | Celery task revoked, BookBuild status set to CANCELLED               |
| BLD-09 | Build completes                         | 1. Wait for build                              | BuildProgress -> 100%. Download button appears.                      |
| BLD-10 | Download PDF                            | 1. Click Download                              | PDF downloaded with filename "{title}-v{version}.pdf"                |
| BLD-11 | Copy download link                      | 1. Click Copy Link                             | Presigned URL copied to clipboard, toast confirmation                |
| BLD-12 | Rebuild creates new version             | 1. Build 2. Rebuild                            | Version number increments (v2, v3, ...). Previous builds accessible. |
| BLD-13 | Version history panel                   | 1. After 3 builds                              | Shows v3, v2, v1 with status badges, dates, download buttons         |
| BLD-14 | Download older version                  | 1. Click Download on v1                        | v1 PDF downloaded (presigned URL)                                    |
| BLD-15 | Build failure                           | 1. Mock build failure                          | "Build failed" status, error message, Retry button                   |
| BLD-16 | Build failure notification              | 1. Editor navigates away during build          | Badge/indicator shows "Build complete" or "Build failed"             |
| BLD-17 | Build in-progress prevents second build | 1. Click Build while already building          | "Build in progress" button, disabled                                 |
| BLD-18 | Concurrent builds                       | 1. Start build 2. Try to build again           | 409 Conflict, "Build already in progress"                            |

#### 6e. Error Handling — Epic 5 Edge Cases

| TC-ID     | Scenario                           | Steps                                                      | Expected Result                                                                                 |
| --------- | ---------------------------------- | ---------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| E5-ERR-01 | Reorder network error              | 1. Reorder pages 2. API fails (timeout/500)                | Toast "Failed to update page order. [Retry]", revert to previous order                          |
| E5-ERR-02 | Reorder validation error           | 1. Send pageId not belonging to book                       | Toast "Some pages could not be reordered. [Refresh]"                                            |
| E5-ERR-03 | Delete last page blocked           | 1. Try to delete the only page                             | Delete button disabled, tooltip "A book must have at least one page"                            |
| E5-ERR-04 | Delete network error               | 1. DELETE API fails                                        | Toast "Failed to delete page. [Retry]", page item re-appears                                    |
| E5-ERR-05 | Add page network error             | 1. POST API fails                                          | Remove optimistic page item, toast "Failed to add page. [Retry]"                                |
| E5-ERR-06 | Approve conflict (409)             | 1. Translation already approved/rejected by another editor | Toast "This translation was already {status} by another editor", auto-refresh translations list |
| E5-ERR-07 | Reject network error               | 1. API request fails                                       | Toast "Failed to reject translation. [Retry]", keep card in Pending state                       |
| E5-ERR-08 | Editor override API failure        | 1. POST API fails                                          | Toast "Failed to submit editor's translation. [Retry]", keep text for retry                     |
| E5-ERR-09 | Section image load error in review | 1. Presigned URL expired or S3 down                        | Image shows broken placeholder with "Reference image unavailable" + Retry                       |
| E5-ERR-10 | Build failure (S3)                 | 1. S3 upload timeout after 3 retries                       | Red error card with error message, [Retry Build] button                                         |
| E5-ERR-11 | Build failure (PDF generation)     | 1. PDF generation crashes on page N                        | Error card with page number, [Retry Build]                                                      |
| E5-ERR-12 | Build failure (DB read)            | 1. Cannot read page/section data                           | Error card with DB error details, [Retry Build]                                                 |
| E5-ERR-13 | Build cancel fails                 | 1. DELETE endpoint fails after timeout                     | Toast "Failed to cancel — build may complete shortly", continue polling                         |
| E5-ERR-14 | Concurrent build blocked           | 1. Click Build while another is active                     | Button disabled, tooltip "A build is already in progress"                                       |
| E5-ERR-15 | Download URL expired               | 1. Click download link after >1h                           | Toast "Download link expired — generating new link...", auto-generate new URL                   |
| E5-ERR-16 | Version download not found         | 1. Version or PDF file missing                             | Toast "Version not found or has no associated PDF file" with [Refresh]                          |

### 7. Team Management

| TC-ID   | Scenario           | Steps                                         | Expected Result                                                       |
| ------- | ------------------ | --------------------------------------------- | --------------------------------------------------------------------- |
| TEAM-01 | Invite translator  | 1. Search user by email 2. Send invite        | User appears in invited list with PENDING status                      |
| TEAM-02 | Accept invitation  | 1. Login as invited user 2. Navigate to books | Book appears in "Assigned to me"                                      |
| TEAM-03 | Block translator   | 1. Click "Block" on translator                | Translator removed from book access. Existing translations preserved. |
| TEAM-04 | Unblock translator | 1. Click "Unblock"                            | Translator regains access to book                                     |

### 8. AI Text Extraction (US-ST-1)

| TC-ID  | Scenario                             | Steps                                                                    | Expected Result                                                          |
| ------ | ------------------------------------ | ------------------------------------------------------------------------ | ------------------------------------------------------------------------ |
| EXT-01 | Trigger extraction — success         | 1. Click "Extract Text" on section 2. Wait                               | Extraction completes. AI text shown with confidence badge.               |
| EXT-02 | Extraction — no cropped image        | 1. `POST /api/sections/{id}/extract` for section without croppedImageKey | 422: "Section has no cropped image."                                     |
| EXT-03 | Extraction — already extracted       | 1. Extract section 2. `POST` again                                       | 409: existing result returned (idempotent).                              |
| EXT-04 | Fetch extraction result              | 1. `GET /api/sections/{id}/extraction` after completion                  | 200: extractedText, confidence, model, processingTimeMs                  |
| EXT-05 | Extraction returns correct text      | 1. Section with known Sinhala text 2. Extract 3. Compare                 | `aiExtractedText` matches expected text                                  |
| EXT-06 | Confidence score in range            | 1. Extract section 2. Check confidence                                   | Float between 0.0 and 1.0                                                |
| EXT-07 | High confidence badge (green)        | 1. Section with confidence ≥ 0.9 2. View panel                           | Green badge: `[AI Extracted] 94% ●`                                      |
| EXT-08 | Medium confidence badge (yellow)     | 1. Section with confidence ≥ 0.7 and < 0.9                               | Yellow badge: `[AI Extracted] 78% ●`                                     |
| EXT-09 | Low confidence badge (red)           | 1. Section with confidence < 0.7                                         | Red badge: `[AI Extracted] 45% ●`                                        |
| EXT-10 | OCR fallback badge (gray)            | 1. Section without AI extraction                                         | Gray badge: `[OCR] ●`                                                    |
| EXT-11 | Extract button visible (editor)      | 1. Login as editor 2. Section without AI text                            | "Extract Text" button visible                                            |
| EXT-12 | Extract button hidden (translator)   | 1. Login as translator 2. Section without AI text                        | Button NOT visible                                                       |
| EXT-13 | Regenerate shows confirmation        | 1. Click "Regenerate" on extracted section                               | Dialog: "Re-extract text? This will replace current AI text."            |
| EXT-14 | Regenerate replaces previous result  | 1. Extract section (result A) 2. Re-extract (result B)                   | Previous AITextExtraction replaced, Section.aiExtractedText updated to B |
| EXT-15 | Editor sees both texts               | 1. Login as editor 2. Section with AI extraction                         | Both OCR and AI text visible in section detail view                      |
| EXT-16 | AI extraction failure — OpenAI error | 1. Mock OpenAI 500 2. Trigger extraction                                 | Task retries 3x, then marks FAILED, section retains OCR text             |
| EXT-17 | Extraction semaphore (max 5)         | 1. Trigger 6 extractions simultaneously                                  | 5 run concurrently, 1 queued (Redis semaphore)                           |
| EXT-18 | Extraction is idempotent             | 1. Extract section 2. Re-extract                                         | Previous result replaced, no duplicate documents                         |
| EXT-19 | Batch page extraction                | 1. `POST /api/books/{id}/pages/{pageNum}/extract`                        | 202: all sections on page queued for extraction                          |
| EXT-20 | Extraction in-progress indicator     | 1. Trigger extraction 2. Immediately view panel                          | Blue animated badge: `[Extracting...] ●○○`                               |

### 9. AI Transliteration (US-ST-2)

| TC-ID   | Scenario                         | Steps                                                               | Expected Result                                                    |
| ------- | -------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------ |
| TRNS-01 | Transliterate — success          | 1. Click "Generate with AI" on section with AI text 2. Wait         | Transliteration generated, pre-fills exact letter field            |
| TRNS-02 | Transliterate — cached           | 1. Generate transliteration 2. Load same section again              | Pre-filled from cache, no new OpenAI call                          |
| TRNS-03 | Transliterate — no source text   | 1. `POST /api/sections/{id}/transliterate` for section without text | 422: "No source text available. Run AI extraction first."          |
| TRNS-04 | Transliteration matches source   | 1. Known Devanagari text 2. Transliterate to Sinhala                | Correct letter-for-letter conversion                               |
| TRNS-05 | Transliteration preserves spaces | 1. Transliterate multi-word text                                    | Word boundaries preserved in output                                |
| TRNS-06 | Spinner during generation        | 1. Click generate 2. Check panel                                    | `[Generating...] ●○○` badge, "Generating transliteration..." text  |
| TRNS-07 | Failure shows manual prompt      | 1. Transliteration API fails                                        | "Transliteration unavailable — enter manually"                     |
| TRNS-08 | Manual edit marks as manual      | 1. Edit pre-filled transliteration 2. Check transliterationSource   | Source changed to "manual"                                         |
| TRNS-09 | Regenerate button for cached     | 1. Section with cached transliteration 2. View panel                | "Regenerate" button visible below transliteration                  |
| TRNS-10 | Cache per section+language pair  | 1. Generate for Sinhala 2. Generate for Tamil                       | Two separate Transliteration documents created                     |
| TRNS-11 | Fetch cached transliterations    | 1. `GET /api/sections/{id}/transliterations`                        | 200: array of transliterations with targetScript, text, confidence |
| TRNS-12 | OpenAI failure → retry           | 1. Mock OpenAI failure 2. Trigger transliteration                   | Task retries 3x, then fails gracefully                             |

### 10. Bidirectional Sync

| TC-ID   | Scenario                                   | Steps                                                                 | Expected Result                                                                |
| ------- | ------------------------------------------ | --------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| SYNC-01 | Edit source text invalidates cache         | 1. Edit source text 2. Wait 500ms debounce                            | `PUT /api/sections/{id}/source-text` called, transliteration cache invalidated |
| SYNC-02 | Regenerate button appears after edit       | 1. Edit source text 2. Check transliteration panel                    | "Regenerate" button pulses/appears                                             |
| SYNC-03 | Source text debounce works                 | 1. Type in source text 2. Wait 300ms 3. Type more 4. Wait 500ms       | Single API call with final text                                                |
| SYNC-04 | Edit transliteration doesn't modify source | 1. Edit transliteration text 2. Check source text panel               | Source text unchanged                                                          |
| SYNC-05 | Manual transliteration marked as manual    | 1. Edit transliteration 2. Check transliterationSource                | Source changed to "manual"                                                     |
| SYNC-06 | No infinite loops                          | 1. Edit source text 2. Wait for invalidation 3. Check transliteration | Transliteration shows "Regenerate" but does NOT auto-update                    |
| SYNC-07 | Rapid edits don't cascade                  | 1. Rapidly edit source text 10 times                                  | Only last edit triggers API (debounce), no cascading updates                   |
| SYNC-08 | Concurrent source edits — last write wins  | 1. User A edits source 2. User B edits source (different text)        | Last save wins, no data corruption                                             |

### 11. Extraction Status Tracking (US-ST-4)

| TC-ID   | Scenario                           | Steps                                                       | Expected Result                                             |
| ------- | ---------------------------------- | ----------------------------------------------------------- | ----------------------------------------------------------- |
| STAT-01 | Extracted section — green overlay  | 1. Section with AITextExtraction 2. View book page          | Green "Extracted" badge on section thumbnail                |
| STAT-02 | Pending section — gray overlay     | 1. Section without AITextExtraction 2. View page            | Gray "Pending" badge                                        |
| STAT-03 | Failed section — red overlay       | 1. Section with failed extraction 2. View page              | Red "Failed" badge                                          |
| STAT-04 | Click Failed opens retry dialog    | 1. Click "Failed" badge                                     | Retry dialog opens                                          |
| STAT-05 | Page-level extraction progress     | 1. View page with mixed extraction states                   | "8/12 sections extracted" with progress bar                 |
| STAT-06 | Stats API includes extractionStats | 1. `GET /api/books/{id}/stats`                              | `extractionStats` with total, extracted, pending, failed    |
| STAT-07 | Filter by extraction status        | 1. Open section list 2. Select "EXTRACTED" filter           | Only extracted sections shown                               |
| STAT-08 | Batch extraction progress tracking | 1. Trigger batch 2. `GET /api/books/{id}/extraction/status` | `{ totalSections, extracted, pending, failed, inProgress }` |

### 12. Batch Auto-Extract (US-ST-5)

| TC-ID    | Scenario                             | Steps                                                          | Expected Result                                         |
| -------- | ------------------------------------ | -------------------------------------------------------------- | ------------------------------------------------------- |
| BATCH-01 | Trigger batch — success              | 1. `POST /api/books/{id}/extract`                              | 202: taskId, totalSections, estimatedCost               |
| BATCH-02 | Batch — already in progress          | 1. Trigger batch 2. `POST` again                               | 409: in-progress status with completed/total counts     |
| BATCH-03 | Batch confirmation dialog            | 1. Click "Extract All" 2. Check dialog                         | "This will extract 156 sections. Cost: $1.28. Proceed?" |
| BATCH-04 | Batch progress bar                   | 1. Trigger batch 2. View console                               | "Extracting section 34/156..." with progress bar        |
| BATCH-05 | Batch — individual failure continues | 1. One section fails during batch                              | Remaining sections processed, failed count incremented  |
| BATCH-06 | Batch summary — failures             | 1. Batch completes with 2 failures 2. View summary             | "154 extracted, 2 failed" with "Retry Failed" button    |
| BATCH-07 | Retry Failed re-runs failed sections | 1. Click "Retry Failed"                                        | Only failed sections re-extracted                       |
| BATCH-08 | Batch — cost limit enforced          | 1. Set cost limit $0.50 2. Book with 100 sections (est. $0.70) | Batch blocked: cost exceeds limit                       |
| BATCH-09 | Button shows progress when active    | 1. Batch in progress 2. Check button text                      | "Extraction in progress (34/156)"                       |
| BATCH-10 | Button disabled during batch         | 1. Batch in progress 2. Check button state                     | "Extract All Sections" button disabled                  |

### 13. Admin Configuration (US-ST-6)

| TC-ID    | Scenario                              | Steps                                                         | Expected Result                                                            |
| -------- | ------------------------------------- | ------------------------------------------------------------- | -------------------------------------------------------------------------- |
| ADMIN-01 | GET extraction config                 | 1. `GET /api/admin/settings/extraction`                       | `{ model, confidenceThreshold, maxConcurrent, costLimitPerBook, enabled }` |
| ADMIN-02 | PUT update config                     | 1. `PUT /api/admin/settings/extraction` with new values       | Config updated, 200 response                                               |
| ADMIN-03 | Config persisted in SystemConfig      | 1. Update config 2. Check MongoDB `system_config` collection  | Key-value document exists with correct values                              |
| ADMIN-04 | Threshold affects badge color         | 1. Set threshold 0.8 2. Section with confidence 0.85          | Badge shows yellow (below 0.9, above 0.8 threshold)                        |
| ADMIN-05 | Low confidence flagged for review     | 1. Set threshold 0.8 2. Section with confidence 0.6           | Extraction saved but flagged for manual review                             |
| ADMIN-06 | Cost limit blocks batch               | 1. Set cost limit $0.10 2. Book with 50 sections (est. $0.35) | Batch blocked with warning                                                 |
| ADMIN-07 | Model change takes effect immediately | 1. Change model to "gpt-4o-mini" 2. Trigger extraction        | New model used (check AITextExtraction.model)                              |
| ADMIN-08 | Max concurrent affects semaphore      | 1. Set max concurrent 3 2. Trigger batch                      | Only 3 concurrent extractions                                              |
| ADMIN-09 | Disabled extraction blocks triggers   | 1. Set enabled=false 2. Click "Extract Text"                  | "AI extraction is disabled" message                                        |
| ADMIN-10 | Audit log endpoint                    | 1. `GET /api/admin/extraction/audit`                          | Array of extraction records with model, cost, confidence                   |
| ADMIN-11 | Admin settings page UI                | 1. Login as super admin 2. `/admin/settings`                  | AI Extraction section with model dropdown, threshold slider, cost input    |
| ADMIN-12 | Config — 403 for non-admin            | 1. GET/PUT settings as editor                                 | 403 Forbidden                                                              |

### 14. Layout — Translation Page Redesign

| TC-ID  | Scenario                      | Steps                            | Expected Result                                                     |
| ------ | ----------------------------- | -------------------------------- | ------------------------------------------------------------------- |
| LAY-01 | Two-row four-panel layout     | 1. View translate tab on desktop | Top row: image+source. Bottom row: translit+translation             |
| LAY-02 | Shared zoom — image and text  | 1. Click + zoom button           | Image scales, source text font scales proportionally (14px × zoom%) |
| LAY-03 | Zoom range 50%–300%           | 1. Zoom to min 2. Zoom to max    | Min 50%, max 300% enforced                                          |
| LAY-04 | Reset zoom restores 100%      | 1. Zoom to 200% 2. Click ⟳       | Both image and text return to 100%                                  |
| LAY-05 | Mobile stacked layout         | 1. View on <768px                | All four panels stacked vertically                                  |
| LAY-06 | Tablet side-by-side           | 1. View on 768–1024px            | Side-by-side with collapsible image panel                           |
| LAY-07 | Image drag-to-pan at any zoom | 1. Zoom to 200% 2. Drag image    | Image pans smoothly                                                 |

### 15. Edge Cases & Error Handling

| TC-ID   | Scenario                                 | Steps                                                              | Expected Result                                                    |
| ------- | ---------------------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------ |
| EDGE-01 | Concurrent translation save              | 2 translators save same section simultaneously                     | No data loss. Both saves succeed.                                  |
| EDGE-02 | Network failure during upload            | 1. Upload file 2. Disconnect network mid-upload                    | Upload fails. User can retry from where it left off.               |
| EDGE-03 | Browser tab close during section editing | 1. Edit sections 2. Close tab without confirming                   | Changes not saved. User warned before close (beforeunload).        |
| EDGE-04 | Empty book (0 pages)                     | 1. Upload empty PDF                                                | Error: "Book has no pages"                                         |
| EDGE-05 | Very large page count (10000+)           | 1. Upload 10000+ page book                                         | Pages process asynchronously. Paginated page list.                 |
| EDGE-06 | Section with no text detected            | 1. Blank page image 2. Detect sections                             | No sections found. "No sections detected" message.                 |
| EDGE-07 | MongoDB connection failure               | 1. Stop MongoDB 2. Try to upload book                              | Graceful error: "Database connection failed. Please try again."    |
| EDGE-08 | Section crop failure                     | 1. Confirm sections with invalid coordinates 2. Wait for crop task | Error logged. Section remains without cropped image. Retry option. |
| EDGE-09 | OpenAI API key invalid                   | 1. Set invalid OPENAI_API_KEY 2. Trigger extraction                | Graceful error: "AI extraction unavailable", section retains OCR   |
| EDGE-10 | OpenAI quota exceeded                    | 1. Mock quota exceeded 2. Trigger extraction                       | Error logged, extraction FAILED, retry available                   |
| EDGE-11 | Redis unavailable for semaphore          | 1. Stop Redis 2. Trigger extraction                                | Extraction proceeds without concurrency limit or graceful error    |
| EDGE-12 | Section with very long text              | 1. Section with 5000+ char text 2. Transliterate                   | Transliteration handles long text, no truncation                   |
| EDGE-13 | Batch extraction with 0 sections         | 1. Book with no sections 2. Trigger batch                          | 422 or 0 totalSections                                             |
| EDGE-14 | Source text edit with only OCR text      | 1. Section with no AI text 2. Edit OCR text                        | OCR text updated, no transliteration invalidation                  |
| EDGE-15 | Transliterate before extraction          | 1. Click "Transliterate" on section without any text               | 422 error, "Run AI extraction first" shown                         |

### 16. Page Editor — Concurrent Editing & Race Conditions

| TC-ID   | Scenario                                     | Steps                                                              | Expected Result                                                                             |
| ------- | -------------------------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------- |
| CONC-01 | Two editors edit same page simultaneously    | 1. Both open same page 2. Both modify sections 3. Both confirm     | Last save wins. No data corruption.                                                         |
| CONC-02 | Save while detection running                 | 1. Start detection 2. Immediately click Confirm                    | Confirm button disabled during detection. Queue save after detect.                          |
| CONC-03 | Detection while saving                       | 1. Click Confirm 2. Immediately click Detect                       | Detect button disabled during save. Queue detect after save.                                |
| CONC-04 | Rapid double-click Confirm                   | 1. Click Confirm twice rapidly                                     | Only one API call made. No duplicate sections created.                                      |
| CONC-05 | Rapid double-click Delete                    | 1. Select section 2. Double-click Delete                           | Section deleted once. No error from deleting non-existent section.                          |
| CONC-06 | Rapid draw + delete                          | 1. Draw section 2. Immediately delete                              | Section added then removed. Undo stack has two entries.                                     |
| CONC-07 | Browser back button during save              | 1. Click Confirm 2. Immediately navigate away                      | User warned via `beforeunload` if save in flight.                                           |
| CONC-08 | Page reload during drawing                   | 1. Enter draw mode 2. Reload page                                  | Draw mode cancelled. No phantom section created.                                            |
| CONC-09 | Multiple rapid zoom changes                  | 1. Rapidly click +/- 10 times                                      | Zoom stabilizes at correct value. No performance degradation.                               |
| CONC-10 | API returns stale data after concurrent save | 1. Two editors save different sections 2. Refresh                  | Full section state reflects last write for each section.                                    |
| CONC-11 | Same section deleted by two editors          | 1. Editor A deletes section S1 2. Editor B also deletes section S1 | No error. Section S1 not present after both saves.                                          |
| CONC-12 | Detection triggered while editing            | 1. Edit sections manually 2. Click Detect                          | Confirmation dialog: "Detect will replace your manual edits. Continue?" [Cancel] [Continue] |

### 9. Page Editor — Concurrent Editing & Race Conditions

| TC-ID   | Scenario                                     | Steps                                                              | Expected Result                                                                             |
| ------- | -------------------------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------- |
| CONC-01 | Two editors edit same page simultaneously    | 1. Both open same page 2. Both modify sections 3. Both confirm     | Last save wins. No data corruption.                                                         |
| CONC-02 | Save while detection running                 | 1. Start detection 2. Immediately click Confirm                    | Confirm button disabled during detection. Queue save after detect.                          |
| CONC-03 | Detection while saving                       | 1. Click Confirm 2. Immediately click Detect                       | Detect button disabled during save. Queue detect after save.                                |
| CONC-04 | Rapid double-click Confirm                   | 1. Click Confirm twice rapidly                                     | Only one API call made. No duplicate sections created.                                      |
| CONC-05 | Rapid double-click Delete                    | 1. Select section 2. Double-click Delete                           | Section deleted once. No error from deleting non-existent section.                          |
| CONC-06 | Rapid draw + delete                          | 1. Draw section 2. Immediately delete                              | Section added then removed. Undo stack has two entries.                                     |
| CONC-07 | Browser back button during save              | 1. Click Confirm 2. Immediately navigate away                      | User warned via `beforeunload` if save in flight.                                           |
| CONC-08 | Page reload during drawing                   | 1. Enter draw mode 2. Reload page                                  | Draw mode cancelled. No phantom section created.                                            |
| CONC-09 | Multiple rapid zoom changes                  | 1. Rapidly click +/- 10 times                                      | Zoom stabilizes at correct value. No performance degradation.                               |
| CONC-10 | API returns stale data after concurrent save | 1. Two editors save different sections 2. Refresh                  | Full section state reflects last write for each section.                                    |
| CONC-11 | Same section deleted by two editors          | 1. Editor A deletes section S1 2. Editor B also deletes section S1 | No error. Section S1 not present after both saves.                                          |
| CONC-12 | Detection triggered while editing            | 1. Edit sections manually 2. Click Detect                          | Confirmation dialog: "Detect will replace your manual edits. Continue?" [Cancel] [Continue] |

## Regression Checklist

### Core Platform

- [ ] Auth flow works after user management changes
- [ ] Book list updates after upload/delete
- [ ] Page list updates after page processing
- [ ] Section coordinates persist correctly after edit
- [ ] Translation count (N translators) is enforced
- [ ] Final PDF includes all approved translations in correct order
- [ ] Role-based access enforced on all API routes
- [ ] No data leakage between books (user A cannot see user B's books)
- [ ] Translator can see own pending translation but not others'
- [ ] Section re-enters pool after all translations rejected
- [ ] Cropped section images generated after section confirmation
- [ ] Original page numbers displayed correctly in page context
- [ ] Page image renders on canvas (not placeholder text)
- [ ] Image loads from presigned URL, not raw S3 key
- [ ] Sections save with raw array payload (not wrapped `{sections: [...]}`)
- [ ] Undo/redo history works for all section operations
- [ ] Keyboard shortcuts function when canvas is focused
- [ ] Loading/error states display during async operations
- [ ] Section colors match type correctly (6 types)
- [ ] Zoom range 50%–300% with 10% increments
- [ ] Concurrent edits do not cause data corruption
- [ ] Draw tool creates sections with min 10×10px constraint
- [ ] `sectionOrder` persists correctly across save/load cycles
- [ ] Confirmed sections can be re-edited and re-confirmed
- [ ] Re-detect replaces sections only after user confirmation

### Translation Page Redesign

- [ ] Translation page auto-loads first section on mount
- [ ] Tab system renders correctly (Translate, History, Stats)
- [ ] Stats tab hidden from translators, visible to editors
- [ ] Source text panel shows original text side-by-side
- [ ] Missing original text shows fallback message
- [ ] Translation history shows correct items with status badges
- [ ] History infinite scroll loads more items via cursor pagination
- [ ] History click navigates to section
- [ ] Translator sees only own history; editor sees all
- [ ] Stats card shows correct totals and percentages
- [ ] Progress bar matches translation percentage
- [ ] Per-language breakdown correct for multi-language books
- [ ] Per-page grid color-coding matches actual progress
- [ ] Stats refresh every 30s via React Query
- [ ] Stats cached in Redis with 30s TTL
- [ ] Translator performance table renders with correct metrics
- [ ] Approval rate calculated correctly
- [ ] Translator row expand shows recent activity
- [ ] Filters apply immediately on selection
- [ ] Filters compose with AND logic
- [ ] Filter state persisted in URL query params
- [ ] Clear filters resets to defaults
- [ ] History tab filters independent from Translate tab
- [ ] Draft auto-saves after 5s inactivity
- [ ] Draft prefills textarea on section load
- [ ] Draft deleted on translation submission
- [ ] Drafts expire after 24h (TTL index)
- [ ] Drafts isolated per-translator per-section
- [ ] beforeunload warning for unsaved changes
- [ ] localStorage fallback when API unavailable

### Source Text Modifications (AI Extraction & Transliteration)

- [ ] AI extraction triggers successfully per-section and batch
- [ ] Extracted text saved to Section.aiExtractedText and AITextExtraction collection
- [ ] Confidence score displayed as badge (green/yellow/red)
- [ ] Extraction idempotent — re-run replaces previous result
- [ ] Extraction failure retains OCR text, shows error toast
- [ ] Batch extraction processes sections with max 5 concurrency (Redis semaphore)
- [ ] Batch progress tracked in Redis and displayed in UI
- [ ] Transliteration generates correctly for Indic scripts
- [ ] Transliteration cached per section+language pair
- [ ] Transliteration pre-fills exactLetterTranslation field
- [ ] Manual transliteration edit marked as "manual" source
- [ ] Source text edit invalidates transliteration cache (500ms debounce)
- [ ] Transliteration edit does NOT modify source text
- [ ] No infinite loops from bidirectional sync
- [ ] Translation editor shows AI text as primary when available
- [ ] Fallback to OCR text when AI extraction unavailable
- [ ] Auto-translation uses AI text (not OCR) when available
- [ ] Two-row four-panel layout renders correctly on desktop
- [ ] Shared zoom scales image and source text proportionally
- [ ] Mobile stacked layout works on <768px viewports
- [ ] Admin can configure model, threshold, concurrent limit, cost limit
- [ ] Cost limit enforced before batch extraction
- [ ] Extraction audit log available for admin review
- [ ] AI extraction disabled via config blocks all triggers
- [ ] OPENAI_API_KEY required in environment

### Book Organization & Publishing (Epic 5)

- [ ] Pages can be reordered via drag-and-drop with visual drop indicator
- [ ] Reordered page order persists on page reload
- [ ] Blank pages can be added between pages
- [ ] Pages can be deleted with cascade of child documents
- [ ] Delete prevents removal of the last remaining page
- [ ] Reorder conflict detection shows toast warning on simultaneous edit
- [ ] Ctrl+Z undoes page reorder actions
- [ ] Blank pages accept sections in canvas editor
- [ ] Page history panel shows timeline of section snapshots
- [ ] Section snapshots can be restored from history
- [ ] SectionEditHistory entries created on each section save
- [ ] Page list loads quickly for 500+ page books
- [ ] Filter by status works correctly (All, Not Started, In Progress, Completed, Needs Review)
- [ ] Filter state persists in URL and survives reload
- [ ] Sort by page order and translation percentage works correctly
- [ ] Filter + sort combination works correctly
- [ ] Progress bar colors: gray (0%), blue (1-99%), green (100%)
- [ ] Summary stats bar shows accurate aggregate counts
- [ ] Empty filter result shows "No pages match filter" with clear CTA
- [ ] Pre-detection state shows "Process pages first" message
- [ ] Filter/sort bar is sticky during scroll
- [ ] Translation review console shows all submitted translations side-by-side
- [ ] Approve marks translation with green badge, isApproved=true
- [ ] Multiple translations can be approved
- [ ] Reject dims card with strikethrough and red badge
- [ ] Reject with reason saves rejectionReason to Translation
- [ ] Rejecting all translations causes section to re-enter pool
- [ ] Re-entry notification sent to translators
- [ ] Editor override creates auto-approved "Editor's Choice" translation
- [ ] Copy from submitted translation fills editor textarea
- [ ] Blocked user translations still visible in review
- [ ] Audit trail (TranslationHistoryItem) created for each approve/reject action
- [ ] Review navigation shows section counter and supports keyboard prev/next
- [ ] Build button enabled only with sections + approved translations
- [ ] Build summary panel shows accurate counts with warnings
- [ ] Build confirmation dialog shows skipped sections
- [ ] Frontend polls build progress every 3 seconds
- [ ] Progress bar shows "Building page X of Y..."
- [ ] Cancel build terminates Celery task and sets CANCELLED status
- [ ] Download button appears on build completion
- [ ] Download PDF filename matches "{title}-v{version}.pdf"
- [ ] Copy Link copies presigned URL to clipboard
- [ ] Rebuild increments version number
- [ ] Version history panel shows all builds with download
- [ ] Older versions remain downloadable
- [ ] Build failure shows error message with Retry
- [ ] In-progress build prevents triggering a second build
- [ ] Concurrent build request returns 409 Conflict
- [ ] Build notifications/indicators shown when editor navigates away
