# Page Editor Fix — QA Test Specification

**Date:** 2026-07-02 21:15
**Author:** QA Agent
**Based on:** specs/business-analysis/20260702-2108-page-editor-fix.md, specs/ux/20260702-2130-page-editor-fix.md, specs/qa/test-plan.md

---

## 1. Overview

This document specifies QA test cases for the Page Editor fix at `/books/[bookId]/pages/[pageNum]`. It covers the four critical bugs identified by the BA, the UX-defined UI states (loading, error, empty, edit, detecting, saving, confirmed), and all interactions (toolbar, keyboard shortcuts, undo/redo, zoom/pan, draw tool, save flow).

### Bug Fix Verification Mapping

| Bug ID | BA Ref | Description | QA Test Coverage |
|--------|--------|-------------|------------------|
| B1 | US-PEF-1 | Image never renders (`fillPatternImage=undefined`) | IMG-01, IMG-02, IMG-08, IMG-11 |
| B2 | US-PEF-2 | Raw S3 key passed instead of presigned URL | IMG-09, IMG-10 |
| B3 | US-PEF-3 | Save payload wrapped in `{sections: [...]}`, wrong format | SAVE-02, SAVE-04 |
| B4 | US-PEF-4 | Detection creates single dummy section | SECT-09, SECT-10, SECT-DET-01 |
| B5 | US-PEF-6 | No undo/redo | UR-01 through UR-14 |
| B6 | US-PEF-5 | No loading/error states | IMG-03 through IMG-07, SECT-03, SECT-04 |

---

## 2. Test Cases Mapped to User Stories

### 2.1 US-PEF-1: Render Page Image on Canvas Background

| TC-ID | Scenario | Prerequisites | Steps | Expected Result | Pass Criteria |
|-------|----------|---------------|-------|-----------------|---------------|
| PEF1-01 | Image renders on canvas via Konva.Image or fillPatternImage | Valid page with presigned image URL | 1. Open page editor | Page image visible as canvas background. Placeholder `<Text>` "Page image would render here" is NOT present. | Image covers full stage dimensions. |
| PEF1-02 | Image element stored in component state | Valid page image URL | 1. Open page editor 2. Inspect component state | Loaded `HTMLImageElement` is stored in `useState` (or `useRef`) after `img.onload` fires. | State contains non-null image element. |
| PEF1-03 | Image dimensions determine canvas size | Known image size (e.g., 1200×1800px) | 1. Open page editor | Stage width/height computed from image dimensions scaled to fit container width (max 100%, maintaining aspect ratio). | `displayWidth = min(containerW-40, imgWidth)`, aspect ratio preserved. |
| PEF1-04 | Image component placed in bottom Layer | Multiple sections loaded | 1. Open page editor with sections | Image is in Layer 1 (background). Sections are in Layer 2 (overlay). Labels in Layer 3. Sections render on top of image. | Sections and labels visible above image; image does not obscure sections. |

### 2.2 US-PEF-2: Pass Presigned S3 URL Instead of Raw S3 Key

| TC-ID | Scenario | Prerequisites | Steps | Expected Result | Pass Criteria |
|-------|----------|---------------|-------|-----------------|---------------|
| PEF2-01 | API returns imageUrl field | Valid page with imageKey | 1. Fetch `GET /api/books/{bookId}/pages/{pageNum}` | Response includes `imageUrl` (presigned S3 URL) as a string field. | `imageUrl` starts with `http` and is a valid MinIO/S3 presigned URL. |
| PEF2-02 | Frontend passes imageUrl to PageEditor | API returns imageUrl | 1. Open page editor 2. Inspect PageEditor props | `pageImageUrl` prop receives `page.imageUrl` (NOT `page.imageKey`). | Prop value is the presigned URL string. |
| PEF2-03 | imageKey null returns imageUrl null | Page with no imageKey | 1. Fetch page API | `imageUrl` is null in response. | Frontend shows "No page image available" fallback. |
| PEF2-04 | Presigned URL is valid for browser | Valid presigned URL | 1. Open page editor 2. Inspect network tab | Browser loads image from presigned URL with 200 status. | Image loads correctly, no CORS or 403 errors. |
| PEF2-05 | Presigned URL has sufficient expiry (3600s) | Backend generates URL | 1. Check URL expiry in backend logs/tests | Presigned URL has expiry >= 3600 seconds from generation. | URL works for at least 1 hour. |

### 2.3 US-PEF-3: Fix Save Sections API Payload Format

| TC-ID | Scenario | Prerequisites | Steps | Expected Result | Pass Criteria |
|-------|----------|---------------|-------|-----------------|---------------|
| PEF3-01 | Payload is raw array, not wrapped object | Sections added on canvas | 1. Click "Confirm Sections" 2. Inspect network request | Request body is `[{ id: "s1", sectionOrder: 0, ... }]` — NOT `{ sections: [...] }`. | `Content-Type: application/json`. Body parses as JSON array. |
| PEF3-02 | "use server" directive removed | PageEditorPage component | 1. Inspect `page.tsx` | `onSave` callback does NOT contain `"use server"` directive. | Callback uses direct `apiFetch` or `fetch` call from client. |
| PEF3-03 | API accepts raw array format | Valid section array | 1. PUT `/api/pages/{pageId}/sections` with raw array | API returns 200 with `{"status": "SECTIONS_CONFIRMED"}`. | Status 200. Body matches expected response schema. |
| PEF3-04 | API rejects wrapped format | Section data wrapped in object | 1. PUT `/api/pages/{pageId}/sections` with `{"sections": [...]}` | API returns 422 validation error. | Status 422. Clear error message in response body. |
| PEF3-05 | crop_sections Celery task triggered on save | Successful save | 1. Confirm sections 2. Check Celery logs | `crop_sections.delay(page_id)` called after successful save. | Celery task enqueued with correct page_id parameter. |

### 2.4 US-PEF-4: Redesign Section Detection to Use Real ML Model

| TC-ID | Scenario | Prerequisites | Steps | Expected Result | Pass Criteria |
|-------|----------|---------------|-------|-----------------|---------------|
| PEF4-01 | Detection returns multiple meaningful sections | Page with varied layout (header, paragraphs, footnotes) | 1. Click "Detect Sections" 2. Check results | Multiple sections returned (not just one). Types include HEADER, PARAGRAPH, etc. | At least 2 sections. Types match actual page regions. |
| PEF4-02 | Section coordinates cover actual content | Known page content | 1. Detect sections 2. Inspect coordinates | Each section's x, y, width, height correspond to real content regions on the page. | No sections covering blank areas. No entire-page single section. |
| PEF4-03 | Detection confidence score populated | ML model returns confidence | 1. Check API response after detection | Each section optionally includes `detectionConfidence` (float 0.0–1.0). | Field present when available from model. |
| PEF4-04 | Detection updates page status | Successful detection | 1. Detect sections 2. Check page status | Page status transitions to SECTIONS_CONFIRMED after detection + optional auto-confirm. | Status updated in MongoDB. |
| PEF4-05 | Detection failure sets DETECTION_FAILED | Unprocessable image | 1. Detect sections on problematic image | Page status = DETECTION_FAILED. Error message returned. | Status visible in UI. Retry option available. |
| PEF4-06 | Detection does NOT crop section images | Detection completes | 1. Check S3 after detection | No images at `books/{bookId}/sections/{sectionId}.png` yet. | Cropping only happens after editor confirmation (US-PEF-3). |

### 2.5 US-PEF-5: Show Canvas Processing & Error States

| TC-ID | Scenario | Prerequisites | Steps | Expected Result | Pass Criteria |
|-------|----------|---------------|-------|-----------------|---------------|
| PEF5-01 | Loading spinner during image fetch | Slow-loading page image | 1. Open page editor 2. Observe initial render | Skeleton placeholder + spinner + "Loading page image..." text visible. | Spinner visible until `img.onload` fires. |
| PEF5-02 | Detecting overlay during section detection | Detection API called | 1. Click "Detect Sections" | Semi-transparent dark overlay + centered spinner + "Detecting sections..." text. All toolbar buttons disabled except zoom. | Overlay visible. Controls disabled. |
| PEF5-03 | Error banner on image load failure | Broken image URL | 1. Open page with invalid imageUrl | Centered: "Failed to load page image" message + [Retry] button. | Error is role="alert". Retry button functional. |
| PEF5-04 | Error banner on detection failure | Detection API fails | 1. Trigger detection on failing page | Error banner above canvas: "Detection failed" + [Retry Detection] button. | Error visible. Retry triggers new detection. |
| PEF5-05 | Error toast on save failure | Save API fails | 1. Click Confirm Sections 2. API returns error | Error toast: "Failed to save sections" (auto-dismiss after 5s). | Toast slides in from top-right. Dismisses automatically. |
| PEF5-06 | Success toast on save | Save succeeds | 1. Click Confirm Sections 2. API returns 200 | Success toast: "✓ Sections confirmed!" | Toast visible. Fades after ~5s. |
| PEF5-07 | Success toast on detection complete | Detection succeeds | 1. Detect sections 2. API returns results | Toast: "Sections detected: {n} found" | Correct count displayed. |
| PEF5-08 | Controls disabled during save | Save in progress | 1. Click Confirm Sections 2. Observe toolbar | Add Section, Delete, Undo, Redo, Detect Sections all disabled. Confirm button shows spinner. | No interactions allowed during save. |
| PEF5-09 | Controls disabled during detection | Detection in progress | 1. Click Detect Sections 2. Observe toolbar | All buttons except zoom controls disabled. | No edit interactions during detection. |
| PEF5-10 | beforeunload warning on unsaved changes | Sections modified but not saved | 1. Edit sections 2. Close tab/refresh | `beforeunload` fires: "Changes you made may not be saved." | Warning dialog appears with cancel/leave options. |

### 2.6 US-PEF-6: Add Undo/Redo Support for Section Edits

| TC-ID | Scenario | Prerequisites | Steps | Expected Result | Pass Criteria |
|-------|----------|---------------|-------|-----------------|---------------|
| PEF6-01 | Undo/redo buttons available in toolbar | Page editor loaded | 1. Open page editor | Undo (↩) and Redo (↪) buttons visible in toolbar. Both disabled initially. | Buttons present. Disabled state correct. |
| PEF6-02 | Undo add section | Section added | 1. Draw a section 2. Press Ctrl+Z | Section removed. State restored to before addition. | Visual: section disappears. State: array reverts. |
| PEF6-03 | Redo add section | Section added then undone | 1. Draw section 2. Ctrl+Z 3. Ctrl+Shift+Z | Section re-appears with same coordinates, type, size. | Visual: section back. State: restored. |
| PEF6-04 | Undo delete section | Section deleted | 1. Delete section 2. Ctrl+Z | Deleted section restored with original position, size, type. | All original properties preserved. |
| PEF6-05 | Undo section move | Section dragged | 1. Drag section 2. Ctrl+Z | Section returns to previous x, y coordinates. | Coordinates match pre-move state. |
| PEF6-06 | Undo section resize | Section resized | 1. Resize section 2. Ctrl+Z | Section returns to previous width, height, x, y. | Dimensions match pre-resize state. |
| PEF6-07 | Undo type change | Section type changed | 1. Change section type 2. Ctrl+Z | Section reverts to previous type. Color updates to match. | Type field restored. Visual color updates. |
| PEF6-08 | Multiple undos in sequence | 3+ edits made | 1. Make 3 edits 2. Press Ctrl+Z ×3 | All 3 actions undone in reverse order (LIFO). | Final state matches state before any of the 3 edits. |
| PEF6-09 | Redo stack cleared on new action | Undo performed, then new action | 1. Undo 1 action 2. Make new edit | Redo stack cleared. Previously undone action cannot be redone. | Redo button disabled. Ctrl+Shift+Z does nothing. |
| PEF6-10 | Undo/redo stacks cleared on confirm | Edits made then saved | 1. Make edits 2. Confirm sections | Undo/redo stacks cleared. Both buttons disabled. | No undo/redo after confirmation. |
| PEF6-11 | Undo/redo stacks cleared on re-detect | Edits made then re-detected | 1. Make edits 2. Re-detect (after confirmation) | Undo/redo stacks cleared. New sections from detection replace all. | Old edits cannot be undone. |
| PEF6-12 | Max 50 entries in undo stack | 51 edits performed | 1. Perform 51 edits | Only most recent 50 entries kept. Oldest entry dropped. | Undo 50× returns to state at edit #2. CanNOT undo back to state at edit #1. |
| PEF6-13 | Zoom changes NOT in undo stack | Zoom level changed | 1. Zoom in 2. Press Ctrl+Z | Zoom level unaffected by undo. | Zoom label unchanged after Ctrl+Z. |

### 2.7 US-PEF-7: Improve Section Order Preservation & Consistency

| TC-ID | Scenario | Prerequisites | Steps | Expected Result | Pass Criteria |
|-------|----------|---------------|-------|-----------------|---------------|
| PEF7-01 | sectionOrder assigned on save | Sections positioned on canvas | 1. Position sections top-to-bottom 2. Confirm | Each section gets sequential `sectionOrder` (0, 1, 2...) based on position. | Order matches visual top-to-bottom, left-to-right. |
| PEF7-02 | Sections loaded sorted by sectionOrder | Saved sections with order | 1. Reopen page 2. Inspect loaded sections | Sections rendered in order of `sectionOrder`. | Visual order matches save-time order. |
| PEF7-03 | New section gets next available order | Existing sections present | 1. Draw a new section 2. Confirm | New section assigned `sectionOrder` = max(existing) + 1. | Order field increments correctly. |
| PEF7-04 | Backend recalculates order on save | Sections in arbitrary order | 1. Send sections in scrambled order 2. Check DB | Backend recalculates `sectionOrder` based on position (or accepts frontend order as-is). | DB records have sequential order values. |
| PEF7-05 | Order preserved after re-edit | Confirmed sections modified | 1. Reopen page 2. Reorder sections 3. Re-confirm | New order values saved. Old order overwritten. | Re-saved order correct. |

### 2.8 US-PEF-8: Keyboard Shortcuts for Canvas Operations

| TC-ID | Scenario | Prerequisites | Steps | Expected Result | Pass Criteria |
|-------|----------|---------------|-------|-----------------|---------------|
| PEF8-01 | Delete/Backspace deletes selected section | Section selected | 1. Select section 2. Press Delete | Section removed. | Undo available. |
| PEF8-02 | Ctrl+Z undos | Any action performed | 1. Perform action 2. Ctrl+Z | Last action reversed. | Visual and state match expected undo. |
| PEF8-03 | Ctrl+Shift+Z redos | Undo performed | 1. Ctrl+Z 2. Ctrl+Shift+Z | Last undone action reapplied. | Visual and state match expected redo. |
| PEF8-04 | Ctrl+Y redos | Undo performed | 1. Ctrl+Z 2. Ctrl+Y | Same as Ctrl+Shift+Z. | Redo works with both key combinations. |
| PEF8-05 | Escape deselects section | Section selected | 1. Select section 2. Escape | Section deselected. Transformer hidden. Type selector hidden. | No selection. |
| PEF8-06 | Escape cancels draw mode | Draw mode active | 1. Enter draw mode 2. Escape | Draw mode exits. No section created. | Button returns to "Add Section" state. |
| PEF8-07 | +/= zooms in | Any state | 1. Press + key | Zoom increases by 10%. | Label updates. |
| PEF8-08 | - zooms out | Any state | 1. Press - key | Zoom decreases by 10%. | Label updates. |
| PEF8-09 | D toggles draw mode | Any state | 1. Press D | Draw mode toggled. | Button state toggles between "Add Section" and "Cancel Draw". |
| PEF8-10 | Ctrl+S saves | Sections present | 1. Press Ctrl+S | Same as clicking "Confirm Sections". | Save API called. |
| PEF8-11 | Shortcuts inactive when text input focused | Text input focused | 1. Focus any text input 2. Press D, +, - | Shortcuts do not fire. | No state changes. |
| PEF8-12 | No browser default conflicts | Any state | 1. Test Ctrl+S, Ctrl+Z, etc. | Browser default prevented. App action takes precedence. | `e.preventDefault()` called where appropriate. |

---

## 3. UI State Test Cases (Mapped from UX Spec)

### 3.1 Canvas States

| TC-ID | State | Trigger | Verification |
|-------|-------|---------|-------------|
| UI-01 | loading | Page mount with valid imageUrl | Skeleton placeholder matching image aspect ratio + spinning loader + text "Loading page image..." |
| UI-02 | no-image | pageImageUrl is null/undefined | Centered: large document icon + "No page image available" + subtitle "Upload a book and process it to see pages here" |
| UI-03 | error-loading | img.onerror fires | Centered: warning icon + "Failed to load page image" + [Retry] button. Retry reloads image. |
| UI-04 | empty | Image loaded, no sections exist | Page image visible. Below canvas or overlay hint: "No sections yet. Click 'Detect Sections' or draw manually." |
| UI-05 | detecting | POST /api/pages/{pageId}/sections/detect sent | Semi-transparent dark overlay + centered spinner + "Detecting sections..." text. All toolbar buttons disabled except zoom. |
| UI-06 | detection-failed | Detection API error | Error banner above canvas: "Detection failed" + [Retry Detection] button. Toolbar: Delete/Add enabled for manual editing. |
| UI-07 | edit | Sections loaded/added, user modifying | Colored rectangles on image. Toolbar fully active. Transformer on selected section. Zoom/labels functional. |
| UI-08 | saving | Confirm clicked, API in flight | "Confirm Sections" button shows spinner. All edit toolbar buttons disabled. Undo/redo NOT cleared yet. |
| UI-09 | confirmed | Save API returns 200 | Status badge updates to SECTIONS_CONFIRMED. "Detect Sections" button replaced by "Re-detect Sections". Sections rendered read-only (draggable=false) OR still editable. Success toast visible. |
| UI-10 | save-failed | Save API error (4xx/5xx/network) | Error toast "Failed to save sections" + [Retry] button on Confirm. Controls re-enabled. Undo/redo stacks retained. |

### 3.2 Toolbar Button State Matrix

| TC-ID | Button | Condition | Expected Visual State |
|-------|--------|-----------|----------------------|
| UI-20 | Add Section | Default | Normal background, 📐 Add Section text |
| UI-21 | Add Section | Draw mode active | Primary background, white text, ✕ Cancel Draw |
| UI-22 | Add Section | Detection/saving in progress | Disabled (grayed out) |
| UI-23 | Delete | No section selected | Disabled |
| UI-24 | Delete | Section selected | Enabled |
| UI-25 | Delete | Detection/saving in progress | Disabled |
| UI-26 | Type Selector | No section selected | Hidden (not in toolbar) |
| UI-27 | Type Selector | Section selected | Visible dropdown with 6 options |
| UI-28 | Type Selector | Detection/saving in progress | Disabled |
| UI-29 | Undo | Undo stack empty | Disabled |
| UI-30 | Undo | Undo stack has entries | Enabled |
| UI-31 | Undo | Detection/saving in progress | Disabled |
| UI-32 | Redo | Redo stack empty | Disabled |
| UI-33 | Redo | Redo stack has entries | Enabled |
| UI-34 | Redo | Detection/saving in progress | Disabled |
| UI-35 | Detect Sections | Default (not confirmed) | ✨ Detect Sections, enabled |
| UI-36 | Detect Sections | Confirmed state | 🔄 Re-detect Sections, enabled |
| UI-37 | Detect Sections | Detection/saving in progress | Disabled, spinner replaces icon |
| UI-38 | Zoom Out | Zoom > 50% | Enabled |
| UI-39 | Zoom Out | Zoom = 50% | Disabled |
| UI-40 | Zoom In | Zoom < 300% | Enabled |
| UI-41 | Zoom In | Zoom = 300% | Disabled |
| UI-42 | Confirm Sections | Sections exist, not saving | Enabled, ✓ Confirm Sections, primary bg |
| UI-43 | Confirm Sections | No sections | Disabled |
| UI-44 | Confirm Sections | Saving in progress | Disabled, spinner replaces checkmark |
| UI-45 | Confirm Sections | Save failed | Enabled, [Retry] text |

### 3.3 ARIA & Accessibility States

| TC-ID | Element | ARIA | Verification |
|-------|---------|------|-------------|
| A11Y-01 | Canvas container | `role="application"`, `aria-label="Page section editor for page {n}"` | Present on Stage container div |
| A11Y-02 | Each section rect | `aria-label="{type} section at position ({x}, {y}), size {width} by {height}"` | Present on each Konva Rect node |
| A11Y-03 | Toolbar | `role="toolbar"`, `aria-label="Section editing tools"` | Present on toolbar container |
| A11Y-04 | Add Section button | `aria-pressed="{isDrawing}"` | Updates with toggle state |
| A11Y-05 | Delete button | `aria-disabled="{!selectedId}"` | Updates with selection state |
| A11Y-06 | Zoom level display | `aria-live="polite"` | Announces zoom changes |
| A11Y-07 | Loading/detecting overlay | `role="status"`, `aria-live="polite"` | Announces async progress |
| A11Y-08 | Error messages | `role="alert"` | Announces errors immediately |
| A11Y-09 | Keyboard navigation | Tab order | All toolbar buttons focusable via Tab. Shift+Tab reverse. Canvas focusable. |

---

## 4. Integration Test Scenarios

### 4.1 Frontend → Backend API Integration

| TC-ID | Scenario | Endpoint | Request | Expected Response | Data Verification |
|-------|----------|----------|---------|-------------------|-------------------|
| INT-01 | Fetch page with sections | `GET /api/books/{bookId}/pages/{pageNum}` | — | `{ id, pageNumber, imageUrl, status, sections: [...] }` | `imageUrl` is presigned URL, `sections` array has correct types |
| INT-02 | Trigger section detection | `POST /api/pages/{pageId}/sections/detect` | `{}` | `{ "status": "processing" }` or `{ "status": "completed", sections: [...] }` | Celery task enqueued or detection complete |
| INT-03 | Save confirmed sections | `PUT /api/pages/{pageId}/sections` | `[{ id, sectionOrder, type, x, y, width, height }, ...]` (raw array) | `{ "status": "SECTIONS_CONFIRMED" }` | Sections persisted in MongoDB. Page status updated. |
| INT-04 | Save with wrapped payload (should fail) | `PUT /api/pages/{pageId}/sections` | `{ "sections": [...] }` | 422 Validation Error | Clear error message about expected format |
| INT-05 | Re-open page after confirmation | `GET /api/books/{bookId}/pages/{pageNum}` | — | Page status = `SECTIONS_CONFIRMED`. Sections array contains saved sections. | All fields (type, x, y, w, h, sectionOrder) match saved values |
| INT-06 | Crop sections triggered after save | Celery task log | — | `crop_sections` task called with `pageId` | Cropped images appear in S3 at `books/{bookId}/sections/{sectionId}.png` |
| INT-07 | Detection on already-confirmed page | `POST /api/pages/{pageId}/sections/detect` | — | Old sections replaced. New sections saved. | Page status updated. Old sections deleted from DB. |

### 4.2 API Contract Tests

| TC-ID | Scenario | Endpoint | Test |
|-------|----------|----------|------|
| API-01 | Page response schema | `GET /api/books/{bookId}/pages/{pageNum}` | Response includes: `id` (string), `pageNumber` (int), `imageKey` (string), `imageUrl` (string\|null), `status` (string), `sections` (array) |
| API-02 | Section object schema | In page response or PUT body | Each section object: `id` (string), `sectionOrder` (int), `type` (enum: HEADER\|PARAGRAPH\|FOOTNOTE\|IMAGE_CAPTION\|PAGE_NUMBER\|OTHER), `x` (float), `y` (float), `width` (float), `height` (float) |
| API-03 | Presigned URL format | `imageUrl` field | Valid S3 presigned URL containing `X-Amz-Signature`, `X-Amz-Credential`, `X-Amz-Expires` query params |
| API-04 | Auth requirement | All page/section endpoints | Returns 401/403 without valid JWT Bearer token |
| API-05 | Role enforcement — detection | `POST /api/pages/{pageId}/sections/detect` | Only EDITOR/SUPER_ADMIN roles can trigger detection. TRANSLATOR gets 403. |

---

## 5. E2E Test Scenarios

### 5.1 Full User Flows

| TC-ID | Flow | Steps | Success Criteria |
|-------|------|-------|-----------------|
| E2E-01 | Complete page editing workflow | 1. Login as Editor 2. Navigate to book 3. Open page editor 4. Image loads automatically 5. Click "Detect Sections" 6. Wait for detection 7. Sections appear as colored rectangles 8. Select a section 9. Drag to new position 10. Change type via dropdown 11. Add new section via draw tool 12. Click "Confirm Sections" 13. Success toast appears 14. Page status updates | All 14 steps complete without errors. Sections persisted. |
| E2E-02 | Error recovery workflow | 1. Open page with broken image URL 2. See error state 3. Click Retry 4. Image loads (or error persists) 5. Navigate back to book | Error state shows correctly. Retry works. Graceful handling. |
| E2E-03 | Undo/redo workflow | 1. Add 3 sections 2. Change one type 3. Delete one 4. Undo (Ctrl+Z ×2) 5. Redo (Ctrl+Shift+Z ×1) 6. Confirm sections | State correctly reflects the undo/redo sequence. |
| E2E-04 | Keyboard shortcut workflow | 1. Press D (draw mode) 2. Press Escape (cancel) 3. Press D again 4. Draw section 5. Select section 6. Press Delete 7. Press Ctrl+Z (undo) 8. Press + (zoom) 9. Press Ctrl+S (save) | All shortcuts work as expected. |
| E2E-05 | Re-detect after confirmation | 1. Confirm sections 2. Click "Re-detect Sections" 3. Confirm dialog appears 4. Click Continue 5. New sections replace old ones | Old sections gone. New sections from detection rendered. |
| E2E-06 | Zoom and pan workflow | 1. Open page editor 2. Zoom to 200% via + clicks 3. Pan via scroll 4. Zoom to 50% via - clicks 5. Edit section at different zoom levels | All edits at different zoom levels produce correct coordinates. |
| E2E-07 | Mobile responsive workflow | 1. Open page editor at <768px width 2. Observe toolbar layout 3. Draw a section 4. Change type | Single-row scrollable toolbar. Core functionality works. |
| E2E-08 | Concurrent edit — two editors | 1. Editor A and B open same page 2. A adds section S1 3. B adds section S2 4. A confirms 5. B confirms (refresh-based) | Both sections saved. No data loss. |

### 5.2 Boundary Tests

| TC-ID | Boundary | Test | Expected |
|-------|----------|------|----------|
| BOUND-01 | Min zoom (50%) | Click − 10× from 100% | Zoom = 50%. Button disabled. Can still edit sections. |
| BOUND-02 | Max zoom (300%) | Click + 20× from 100% | Zoom = 300%. Button disabled. Transformer handles functional. |
| BOUND-03 | Min section size (10×10) | Draw rectangle < 10×10 | Section not created. No error. |
| BOUND-04 | Max undo entries (50) | Perform 51 edits | Only 50 entries in undo stack. Oldest dropped. |
| BOUND-05 | Max sections on page | Add 200 sections | All sections rendered. Performance acceptable (< 1s frame time). |
| BOUND-06 | Extra-large page image (10000×15000px) | Load large page image | Image scales down to fit container. Canvas usable. |
| BOUND-07 | Zero sections confirm | Confirm with 0 sections | Button disabled or shows "No sections to confirm" |

---

## 6. Edge Cases

| TC-ID | Edge Case | Steps | Expected Behavior |
|-------|-----------|-------|-------------------|
| EDGE-PE-01 | Page with null imageKey | Load page editor | Fallback "No page image available" state. Sections metadata still loads. |
| EDGE-PE-02 | Page with empty sections array | Load page with status SECTIONS_CONFIRMED but no sections | Empty state hint shown. Re-detect button available. |
| EDGE-PE-03 | Network disconnected mid-draw | Draw section, disconnect network, continue editing | All edits work locally. Confirm fails. Error toast shown. Edits preserved in state. |
| EDGE-PE-04 | Very fast double-click on canvas | Double-click during draw mode | Second click does not create duplicate section. First click-drag completes normally. |
| EDGE-PE-05 | Section dragged behind image boundary | Drag section entirely off-image | Section position constrained to image bounds (or handled gracefully). No phantom data. |
| EDGE-PE-06 | Browser back/forward during editing | Press browser back then forward | State restored from server (not local). Server-side data shown. |
| EDGE-PE-07 | Tab away and return | 1. Start editing 2. Switch to another tab 3. Return after 30 min | Page still loaded. Session still valid. Unsaved edits preserved in state. |
| EDGE-PE-08 | All 6 section types on single page | Manually create one of each type | All 6 colors render correctly. All labels visible. No overlap of text labels. |
| EDGE-PE-09 | Section with 0 width or height via direct API | POST section with w=0 or h=0 | API rejects with validation error. |
| EDGE-PE-10 | Image loads after sections already rendered | Slow network: sections from API arrive before image | Sections rendered on grey background. When image loads, sections appear over image. No layout shift. |
| EDGE-PE-11 | Presigned URL expires mid-session | Wait > 1 hour then interact | Image still cached in browser. If not cached, shows error but can still edit sections. |
| EDGE-PE-12 | Detection returns 0 sections | Detect sections on blank image | Toast: "No sections detected". Toolbar: manual Add Section available. |

---

## 7. Performance & Load Tests

| TC-ID | Scenario | Test | Acceptable Threshold |
|-------|----------|------|---------------------|
| PERF-01 | Page load time | Open page editor with 50 sections | < 3s to interactive (first paint of image + sections) |
| PERF-02 | Section render performance | Render 100 section rectangles simultaneously | < 200ms render time. No frame drops during interaction. |
| PERF-03 | Zoom responsiveness | Zoom from 100% to 300% | Smooth transition. < 100ms update time per zoom step. |
| PERF-04 | Undo/redo with 50 entries | Perform 50 actions, then undo all 50 | Each undo < 50ms. No cumulative lag. |
| PERF-05 | Draw preview performance | Draw large rectangle (> 80% of canvas) | Dashed preview follows cursor without lag. |
| PERF-06 | Image load with large file | 50MP page image (15MB PNG) | Loads within 10s on fast connection. Image scales correctly. |
| PERF-07 | Memory usage with heavy editing | Add, move, resize 50 sections continuously | No significant memory leak. Heap stable (±10MB). |

---

## 8. Test Environment Requirements

| Requirement | Details |
|-------------|---------|
| Browser | Chrome 125+, Firefox 128+, Safari 17+ |
| Viewport | Desktop 1440×900, Tablet 1024×768, Mobile 375×667 |
| Backend | FastAPI running on localhost:8000 with test MongoDB |
| MinIO | Running with test bucket and pre-seeded page images |
| Auth | Test JWT token with EDITOR role for page operations |
| Network | Simulated slow network (3G throttling) for loading states |
| Accessibility | NVDA or VoiceOver for screen reader testing |
| Test data | Book with at least 3 pages, one page with 5+ sections, one page with 0 sections |

---

## 9. Bug-Specific Verification Checklist

- [ ] **B1 fixed**: Page image renders on canvas (not placeholder text). Verified via IMG-01, IMG-02.
- [ ] **B2 fixed**: Frontend receives `imageUrl` (presigned URL), not raw `imageKey`. Verified via IMG-09, PEF2-01, PEF2-02.
- [ ] **B3 fixed**: Save sends raw array `[...]`, not `{sections: [...]}`. Verified via SAVE-02, PEF3-01.
- [ ] **B4 fixed**: Detection returns multiple sections with correct types. Verified via PEF4-01, PEF4-02.
- [ ] **B5 fixed**: Undo/redo functional for all section operations. Verified via PEF6-01 through PEF6-13.
- [ ] **B6 fixed**: All loading, error, and empty states render correctly. Verified via UI-01 through UI-10.

---

## 10. Test Traceability Matrix

| User Story | Test IDs |
|------------|----------|
| US-PEF-1 | PEF1-01, PEF1-02, PEF1-03, PEF1-04, IMG-01, IMG-02, IMG-08, IMG-11 |
| US-PEF-2 | PEF2-01, PEF2-02, PEF2-03, PEF2-04, PEF2-05, IMG-09, IMG-10 |
| US-PEF-3 | PEF3-01, PEF3-02, PEF3-03, PEF3-04, PEF3-05, SAVE-01, SAVE-02 |
| US-PEF-4 | PEF4-01, PEF4-02, PEF4-03, PEF4-04, PEF4-05, PEF4-06, SECT-01, SECT-02 |
| US-PEF-5 | PEF5-01 through PEF5-10, UI-01 through UI-10, IMG-03 through IMG-07 |
| US-PEF-6 | PEF6-01 through PEF6-13, UR-01 through UR-14 |
| US-PEF-7 | PEF7-01, PEF7-02, PEF7-03, PEF7-04, PEF7-05, SECT-32 |
| US-PEF-8 | PEF8-01 through PEF8-12, KB-01 through KB-15 |
