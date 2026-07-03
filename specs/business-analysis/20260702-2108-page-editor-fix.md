# Page Editor Fix — User Stories & Bug Analysis

**Date:** 2026-07-02 21:08  
**Author:** Business Analysis Agent  
**Epic Reference:** Epic 3 — Page Processing (spec.md lines 38–46)

---

## Bug Analysis Summary

The user reports the page editor is not working for the "Find sections of the page" spec section. Four root causes were identified through code analysis:

| # | Issue | Location | Severity |
|---|-------|----------|----------|
| 1 | Page image never renders on canvas — `fillPatternImage` is hardcoded to `undefined` | `PageEditor.tsx:224` | **Critical** |
| 2 | `pageImageUrl` receives raw S3 key (`imageKey`) instead of a presigned URL — browser cannot load the image | `page.tsx:51` + `pages.py:69` | **Critical** |
| 3 | API `PUT /api/pages/{pageId}/sections` payload format mismatch — frontend sends `{ sections: [...] }`, backend expects raw `[...]` | `page.tsx:55-58` vs `pages.py:103` | **High** |
| 4 | Section detection is a stub — creates one dummy PARAGRAPH section, no real ML model or LayoutParser integration | `detect_sections.py:30-42` | **Medium** |

---

## User Stories

### US-PEF-1: Render Page Image on Canvas Background

**As an** editor  
**I want to** see the actual page image rendered as the canvas background in the PageEditor  
**So that** I can visually align section rectangles over the real page content.

**Acceptance Criteria:**

- `PageEditor` stores the loaded `HTMLImageElement` in state after `img.onload` fires
- The image is rendered using either:
  - A `<Konva.Image>` node with the `image` prop set to the loaded image element, or
  - A `<Rect>` with `fillPatternImage` set to the loaded image element
- The image covers the full canvas stage (not just a placeholder text)
- The placeholder `<Text text="Page image would render here"...>` is removed
- The image component is placed in the bottom Layer so sections render on top
- If `pageImageUrl` is provided but fails to load, a fallback error message is shown with a retry option

**Technical Notes:**

- Current code in `PageEditor.tsx:56-66` already loads the image via `new window.Image()` and computes `imageSize`, but the loaded `img` object is never stored or passed to the Konva `Rect`. The image must be kept in a `useState` (or `useRef`) and wired to `fillPatternImage`.
- Alternatively, use `Konva.Image` node which accepts `image={imgElement}` directly.

---

### US-PEF-2: Pass Presigned S3 URL Instead of Raw S3 Key

**As an** editor  
**I want to** the page image to load in the browser  
**So that** I can see the page content before editing sections.

**Acceptance Criteria:**

- The `GET /api/books/{bookId}/pages/{pageNum}` endpoint returns `imageUrl` (a presigned S3 URL) instead of or in addition to `imageKey` (a raw S3 key)
- The frontend `PageEditorPage` passes `pageImageUrl={page.imageUrl}` instead of `page?.imageKey`
- The presigned URL is generated server-side using `get_presigned_url(page["imageKey"])`
- The presigned URL has sufficient expiry (default 3600 seconds)
- For pages where `imageKey` is null/empty, `imageUrl` is returned as null and the editor shows "No page image available"

**Backend Changes:**

- `pages.py:69`: Change `"imageKey"` to `"imageUrl"` and call `await get_presigned_url(page["imageKey"])`
- `PageResponse` schema in `page.py`: Add optional `imageUrl: str | None = None` field
- The `imageKey` field may still be included for debugging but should not be used by the frontend for display

**Frontend Changes:**

- `page.tsx:51`: Change `pageImageUrl={page?.imageKey}` to `pageImageUrl={page?.imageUrl}`
- The `PageDetail` interface should include `imageUrl` as a string field

---

### US-PEF-3: Fix Save Sections API Payload Format

**As a** system  
**I want to** the `PUT /api/pages/{pageId}/sections` endpoint to accept and process the correct payload format  
**So that** section data is persisted when the editor clicks "Confirm Sections".

**Acceptance Criteria:**

- The frontend sends a raw JSON array `[{"id": "s1", "sectionOrder": 0, ...}]` to the API, not a wrapped object
- OR the backend accepts the wrapped format `{"sections": [...]}` by updating the path parameter type or body model
- On success, the API returns `{"status": "SECTIONS_CONFIRMED"}` (already done)
- `crop_sections` Celery task is triggered after save (already done)

**Technical Notes:**

- Current frontend (`page.tsx:53-59`) uses `onSave` with a "use server" directive inside a client component, which is incorrect — the function is passed to a Client Component (`PageEditor`) and runs on the client, but "use server" is for Server Actions. The "use server" directive inside a client component's inline function is a no-op at best and misleading.
- The `onSave` callback should either:
  (a) Be a proper Server Action imported from a separate file, or
  (b) Make a direct `fetch` call to the API from the client (simpler, more consistent with the rest of the app)

**Recommended Fix:**

- Replace the `onSave` prop with an actual API call inside `PageEditorPage` (or pass a client-side fetch function). Remove the `"use server"` directive.
- Fix the payload: send `sections` directly as the array, not wrapped: `body: JSON.stringify(sections.map(...))`

---

### US-PEF-4: Redesign Section Detection to Use Real ML Model

**As a** system  
**I want to** the section detection process to analyze page images and return meaningful sections  
**So that** editors receive useful starting rectangles rather than a single dummy paragraph.

**Acceptance Criteria:**

- The `detect_sections` Celery task uses a real ML detection model (LayoutParser or similar) to identify page regions
- Detected regions include type classification (HEADER, PARAGRAPH, FOOTNOTE, IMAGE_CAPTION, PAGE_NUMBER, OTHER)
- Each detected section has meaningful x, y, width, height coordinates covering actual content regions
- Multiple sections are created per page (not just one)
- Detection confidence scores can be optionally stored per section
- The task updates page status to SECTIONS_CONFIRMED on completion
- Section images are NOT cropped during detection (cropping happens after editor confirmation)

**Current Limitation:**

`detect_sections.py:30-42` creates a single hardcoded section covering almost the entire page with type PARAGRAPH. This is a stub and must be replaced with actual image analysis.

---

### US-PEF-5: Show Canvas Processing & Error States

**As an** editor  
**I want to** see loading spinners, error messages, and retry options during page image loading and section detection  
**So that** I understand what is happening and can recover from failures.

**Acceptance Criteria:**

- A loading spinner overlay is shown on the canvas while the page image is being fetched from S3
- A loading state is shown while section detection is in progress (polling or WebSocket status update)
- Network errors during image loading show an error banner with "Retry" button
- API errors during save show an error toast/message
- The delete/confirm/add-section buttons are disabled during save operations
- A "Detection Failed" page status is handled gracefully with a retry detection button

---

### US-PEF-6: Add Undo/Redo Support for Section Edits

**As an** editor  
**I want to** undo and redo section modifications during a canvas editing session  
**So that** I can recover from mistakes without losing all changes.

**Acceptance Criteria:**

- Undo (Ctrl+Z) reverses the last section action (add, delete, move, resize, type change)
- Redo (Ctrl+Shift+Z / Ctrl+Y) reapplies the last undone action
- Undo/redo stack is maintained locally in browser memory (not persisted to DB)
- The undo/redo stack is cleared when sections are confirmed/saved
- Buttons for Undo and Redo are available in the toolbar
- Keyboard shortcuts are documented or shown as tooltips

---

### US-PEF-7: Improve Section Order Preservation & Consistency

**As a** system  
**I want to** section order to be consistently assigned and preserved across save/load cycles  
**So that** sections appear in the correct visual order on the translation UI.

**Acceptance Criteria:**

- When sections are saved, each section receives a `sectionOrder` value based on its top-to-bottom, left-to-right position on the page
- When sections are loaded, they are sorted by `sectionOrder`
- New sections added via draw tool are assigned the next available `sectionOrder`
- The backend `save_sections` endpoint recalculates `sectionOrder` based on section positions or accepts the order from the frontend as-is
- Section order is visible in the UI (ordered list or numbered labels)

---

### US-PEF-8: Keyboard Shortcuts for Canvas Operations

**As an** editor  
**I want to** use keyboard shortcuts for common canvas operations  
**So that** I can work faster without reaching for toolbar buttons.

**Acceptance Criteria:**

| Key | Action |
|-----|--------|
| `Delete` / `Backspace` | Delete selected section |
| `Ctrl+Z` | Undo |
| `Ctrl+Shift+Z` / `Ctrl+Y` | Redo |
| `Escape` | Deselect current section / cancel draw mode |
| `+` / `=` | Zoom in |
| `-` | Zoom out |
| `Ctrl+S` | Save/confirm sections |
| `D` | Toggle draw mode (Add Section) |

- Keyboard shortcuts only work when the canvas area is focused
- Shortcuts are documented in a tooltip or help panel
- No conflicts with browser default shortcuts

---

## Implementation Priority

| Priority | Story | Effort | Impact |
|----------|-------|--------|--------|
| P0 | US-PEF-1: Render page image on canvas background | Small | Critical — editor cannot see page |
| P0 | US-PEF-2: Pass presigned S3 URL instead of raw key | Small | Critical — image won't load |
| P0 | US-PEF-3: Fix save sections API payload format | Small | Critical — sections can't be saved |
| P1 | US-PEF-5: Canvas processing & error states | Medium | High — poor UX without feedback |
| P1 | US-PEF-7: Section order preservation | Small | High — incorrect section ordering |
| P2 | US-PEF-4: Redesign section detection with ML | Large | Medium — stub works for demo only |
| P2 | US-PEF-6: Undo/redo support | Medium | Medium — quality of life |
| P3 | US-PEF-8: Keyboard shortcuts | Small | Low — nice to have |

---

## Key Insights

1. **Critical issues are all in the integration layer** — the Konva canvas component itself is well-structured with correct event handlers for drag, resize, delete, and draw. The problems are: (a) the image never renders, (b) the URL is wrong, (c) the save payload is malformed.

2. **Three of four critical bugs can be fixed in a single editing session** — US-PEF-1, US-PEF-2, and US-PEF-3 require changes to only 2 files (`PageEditor.tsx`, `page.tsx`, `pages.py`) and are low-risk.

3. **The "use server" directive in the client component is incorrect** — `onSave` in `page.tsx:53-59` uses `"use server"` inside the component body, which does not create a server action. The function runs on the client and should use a direct `apiFetch` call.

4. **Section detection is currently a stub** — the `detect_sections` Celery task creates only one section covering most of the page. This needs a real ML model integration (LayoutParser or similar) to provide useful automatic section detection.

5. **No thumbnail support for pages in the page editor** — while the book console shows page thumbnails, the page editor itself doesn't show or use the page thumbnail. This is acceptable since the page editor shows the full-resolution image.

6. **The test file (`PageEditor.test.tsx`) mocks react-konva completely** — existing tests verify button states and section counting but cannot verify image rendering. Tests for the image display fix would require either a different approach (integration tests) or updating the mock to include an `Image` component.
