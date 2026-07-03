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

### 6. Book Organization & Publishing

| TC-ID  | Scenario                      | Steps                                                                   | Expected Result                                                                                              |
| ------ | ----------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| ORG-01 | Reorder pages                 | 1. Drag page in list to new position                                    | Page order updated                                                                                           |
| ORG-02 | Delete page                   | 1. Click delete on page 2. Confirm                                      | Page removed. Sections cascade deleted.                                                                      |
| ORG-03 | Filter by status              | 1. Click "Completed" filter                                             | Only completed pages shown                                                                                   |
| ORG-04 | Sort by progress              | 1. Select sort by "Progress %"                                          | Pages sorted ascending/descending                                                                            |
| ORG-05 | Review translations           | 1. Open section with translations 2. View side-by-side                  | All N translations shown with translator info. Exact letter field shown if provided.                         |
| ORG-06 | Approve multiple translations | 1. Click "Approve" on Translation A 2. Click "Approve" on Translation B | Both marked approved with star badges                                                                        |
| ORG-07 | Reject a translation          | 1. Click "Reject" on a translation                                      | Translation marked with strikethrough + "Rejected" badge                                                     |
| ORG-08 | Reject all translations       | 1. Click "Reject All"                                                   | Section re-enters translation pool. Message: "All translations rejected. Translators will need to resubmit." |
| ORG-09 | Editor override translation   | 1. Type own translation 2. Click "Write your own"                       | Editor's version saved as approved translation                                                               |
| ORG-10 | Resubmit after rejection      | 1. Editor rejects all 2. Translator opens section again                 | Section appears in queue for re-translation                                                                  |
| ORG-11 | Build finalized book          | 1. Click "Build" 2. Wait for processing                                 | Book build status: BUILDING → COMPLETED. Download link appears.                                              |
| ORG-12 | Download finalized book       | 1. Click Download                                                       | PDF downloaded using original page numbers for labels                                                        |
| ORG-13 | Rebuild book                  | 1. Make changes 2. Click "Build" again                                  | New PDF overwrites previous in S3                                                                            |

### 7. Team Management

| TC-ID   | Scenario           | Steps                                         | Expected Result                                                       |
| ------- | ------------------ | --------------------------------------------- | --------------------------------------------------------------------- |
| TEAM-01 | Invite translator  | 1. Search user by email 2. Send invite        | User appears in invited list with PENDING status                      |
| TEAM-02 | Accept invitation  | 1. Login as invited user 2. Navigate to books | Book appears in "Assigned to me"                                      |
| TEAM-03 | Block translator   | 1. Click "Block" on translator                | Translator removed from book access. Existing translations preserved. |
| TEAM-04 | Unblock translator | 1. Click "Unblock"                            | Translator regains access to book                                     |

### 8. Edge Cases & Error Handling

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
