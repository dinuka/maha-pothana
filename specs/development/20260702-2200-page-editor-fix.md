# Page Editor Fix — Implementation Spec

**Date**: 2026-07-02 22:00  
**Status**: Complete  
**Commits**: Not yet committed

## Summary

Fixed critical bugs B1–B5 and added features for the Page Editor (`/books/[bookId]/pages/[pageNum]`):
image rendering via presigned URLs, correct save payload format, varied section detection, undo/redo,
keyboard shortcuts, and UI states (loading/error/empty). Also resolved a React 19 `act()` hang in tests.

## Files Changed

### Backend
| File | Change |
|------|--------|
| `apps/api/app/schemas/page.py` | Added `imageUrl` field to `PageResponse` |
| `apps/api/app/api/pages.py` | `get_page()` calls `get_presigned_url(page.get("imageKey"))`; `save_sections` sorts by (y,x) and recalculates `sectionOrder` |
| `apps/api/app/tasks/detect_sections.py` | Returns 5 varied sections (HEADER, 2×PARAGRAPH, FOOTNOTE, PAGE_NUMBER) with proportional sizing; status set to `"PENDING"` |
| `apps/api/tests/test_pages.py` | 12 tests including 2 new: `test_get_page_image_url_null_when_no_image_key`, `test_save_sections_recalculates_order` |

### Frontend
| File | Change |
|------|--------|
| `apps/web/app/books/[bookId]/pages/[pageNum]/page.tsx` | Uses `page?.imageUrl` instead of `page?.imageKey`; sends raw array `JSON.stringify(ordered)`; adds `sectionOrder` via `.map()`; removed `"use server"` directive |
| `apps/web/components/PageEditor.tsx` | Rewritten: Konva.Image on background layer; undo/redo via ref-based stacks; Ctrl+Z/Ctrl+Shift+Z, Delete, Escape, D, Ctrl+S, +/- keyboard shortcuts; loading/error/empty UI states; toolbar with section type selector; section type labels on canvas; `loadImage()` moved to `useLayoutEffect` for testability; refs synced via `useLayoutEffect` instead of render body; eslint warnings fixed |
| `apps/web/__tests__/PageEditor.test.tsx` | 14 tests across 4 describe blocks: no-image, loading, loaded (mock Image), error (mock Image onerror). Uses `flushSync` + `createRoot` (avoids `act()` hang). |

### Deleted
| File | Reason |
|------|--------|
| `apps/web/components/PageEditorMinimal.tsx` | Debug copy, no longer needed |

## Testing Strategy

### Problem
React 19's `act()` hangs when rendering PageEditor (even with fully mocked Image).  
`@testing-library/react`'s `render()` wraps `createRoot` in `act()` — same hang.  
Root cause: `act()` waits for re-render work that never settles in the test environment.

### Solution
Replace `act()`-based rendering with `createRoot().render()` + `flushSync()`:

- **`flushSync(() => root.render(<Component />))`** commits initial render synchronously
- **`useLayoutEffect`** state updates ARE flushed by `flushSync` (unlike `useEffect`)
- **Mock Image** fires `onload`/`onerror` synchronously during `useLayoutEffect`
- After `flushSync`, component state reflects the final post-image-load state
- **`flushSync(() => {})`** after click events flushes state updates from event handlers
- **`key` prop** on `root.render()` forces fresh component mount between tests (prevents state leakage)

### Mock Image Implementation
```ts
const MockImage = function () {
  const img = { onload: null, onerror: null, width: 800, height: 600 }
  Object.defineProperty(img, "src", {
    set(value) {
      if (typeof img.onload === "function") img.onload()
    }
  })
  return img
}
vi.stubGlobal("Image", MockImage)
```
Each describe block creates its own root and manages Image mock via `vi.stubGlobal`/`vi.unstubAllGlobals()`.

## Test Results

| Suite | Tests | Status |
|-------|-------|--------|
| Frontend (Vitest) | 46 | ✅ All pass (7 files, 14 new) |
| Backend (pytest) | 48 | ✅ All pass (2 new) |
| Lint (`pnpm lint`) | — | ✅ 0 errors, 0 warnings |
| Typecheck (`pnpm check-types`) | — | ✅ Passing |

### PageEditor Tests (14 total)
- **No image**: No URL → shows "No page image available" message
- **Loading state**: URL with real Image → shows "Loading page image..." with disabled toolbar
- **Loaded state** (mock Image sync onload, 10 tests): toolbar + stage + section rects; zoom +/- updates; confirm button enabled/calls onSave with ordered sections; delete button disabled when no selection; draw toggle changes button text; undo/redo disabled initially; confirm clears undo stack
- **Empty sections**: URL + empty initialSections → shows "No sections yet" message; confirm disabled
- **Error state** (mock Image onerror): Failed load → shows "Failed to load page image" with Retry button

## Key Techniques

1. **`useLayoutEffect` for image loading**: Synchronous flush makes image state available after `flushSync()` without `act()`.
2. **Mock Image with sync `src` setter**: Fires `onload`/`onerror` during layout effect execution.
3. **`flushSync(() => {})` after click**: Flushes state updates from discrete event handlers.
4. **Separate `createRoot` per describe block**: Clean state isolation.
5. **`key` prop on fresh renders**: Forces component remount, preventing state leakage.
6. **`vi.stubGlobal` + `vi.unstubAllGlobals`**: Image mock lifecycle management per describe block.
