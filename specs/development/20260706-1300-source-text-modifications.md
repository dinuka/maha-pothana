# Source Text Modifications — Development Implementation Spec

**Date:** 2026-07-06 13:00
**Author:** Development Agent
**Related BA:** `specs/business-analysis/20260706-1300-source-text-modifications.md`
**Related Architecture:** `specs/architecture/20260706-1300-source-text-modifications.md`
**Related UX:** `specs/ux/20260706-1300-source-text-modifications.md`
**Related QA:** `specs/qa/20260706-1300-source-text-modifications.md`

---

## 1. Implementation Summary

Implemented AI-powered text extraction and bidirectional transliteration for Indic scripts. The feature introduces OpenAI GPT-4o Vision for OCR replacement and GPT-4o text for script-to-script transliteration, with a redesigned two-row translation UI.

---

## 2. Files Created

### Backend (apps/api)

| File                                 | Purpose                                                                          |
| ------------------------------------ | -------------------------------------------------------------------------------- |
| `app/services/ai_text.py`            | OpenAI GPT-4o Vision + text integration for extraction and transliteration       |
| `app/schemas/extraction.py`          | Pydantic models for extraction/transliteration API contracts                     |
| `app/api/extraction.py`              | 8 API endpoints for extraction, transliteration, source text updates, and status |
| `app/tasks/extract_section_text.py`  | Celery task for single-section AI text extraction                                |
| `app/tasks/transliterate_section.py` | Celery task for transliteration with caching                                     |

### Frontend (apps/web)

| File                                 | Purpose                                     |
| ------------------------------------ | ------------------------------------------- |
| `__tests__/SourceTextPanel.test.tsx` | 18 unit tests for SourceTextPanel component |

---

## 3. Files Modified

### Backend

| File                     | Changes                                                                                                               |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| `app/config.py`          | Added `openai_api_key: str = ""` setting                                                                              |
| `app/db/indexes.py`      | Added indexes for `ai_text_extractions`, `transliterations`, `system_config`, `redis_progress`                        |
| `app/main.py`            | Registered `extraction_router`                                                                                        |
| `app/schemas/section.py` | Added `aiExtractedText` and `extractionStatus` to `SectionResponse`; added `aiExtractedText` to `NextSectionResponse` |
| `app/api/sections.py`    | Updated `get_next_section` to return `aiExtractedText`                                                                |
| `tests/conftest.py`      | Added `ai_text_extractions`, `transliterations`, `system_config`, `redis_progress` to mock_db                         |
| `tests/test_ai_text.py`  | 18 test cases covering all extraction and transliteration endpoints                                                   |

### Frontend

| File                                           | Changes                                                                                                                                                                          |
| ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `app/translate/TranslateTab.tsx`               | Rewritten with 2-row layout: top row (image + source text), bottom row (transliteration + translation). Added extraction trigger, transliteration generation, bidirectional sync |
| `app/translate/components/SourceTextPanel.tsx` | Rewritten with AI/OCR toggle, confidence badge, extract/regenerate buttons, inline editing with debounced save                                                                   |
| `lib/api/translations.ts`                      | Added `aiExtractedText` to `NextSectionResponse` interface                                                                                                                       |

---

## 4. API Endpoints Implemented

| Method | Path                                          | Status  | Description                                          |
| ------ | --------------------------------------------- | ------- | ---------------------------------------------------- |
| POST   | `/api/sections/{sectionId}/extract`           | 202     | Trigger single-section extraction                    |
| POST   | `/api/books/{bookId}/pages/{pageNum}/extract` | 202     | Batch extract all sections on a page                 |
| POST   | `/api/books/{bookId}/extract`                 | 202     | Batch extract all sections in a book                 |
| GET    | `/api/sections/{sectionId}/extraction`        | 200     | Fetch extraction result with confidence              |
| POST   | `/api/sections/{sectionId}/transliterate`     | 200/202 | Generate transliteration (cached or queued)          |
| GET    | `/api/sections/{sectionId}/transliterations`  | 200     | Fetch cached transliterations                        |
| PUT    | `/api/sections/{sectionId}/source-text`       | 200     | Update source text, invalidate transliteration cache |
| GET    | `/api/books/{bookId}/extraction/status`       | 200     | Batch extraction progress                            |

---

## 5. Celery Tasks

| Task                    | Description                                                                                                                              |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `extract_section_text`  | Downloads cropped image from MinIO, sends to GPT-4o Vision, saves to `ai_text_extractions` collection, updates `Section.aiExtractedText` |
| `transliterate_section` | Checks cache first, then calls GPT-4o for script conversion, saves to `transliterations` collection                                      |

Both tasks follow existing patterns from `crop_sections.py` using `run_async()` for async Motor calls in sync Celery workers.

---

## 6. Frontend Component Architecture

### TranslateTab (Redesigned)

```
TranslateTab
├── Header (book title, page indicator, skip/submit)
├── Top Row (2-column grid)
│   ├── Image Column (zoomable, draggable)
│   │   └── Zoom Controls (−, %, +, ⟳)
│   └── Source Text Column
│       └── SourceTextPanel (AI/OCR toggle, confidence badge, edit)
├── Bottom Row (2-column grid)
│   ├── Transliteration Column
│   │   └── Panel (AI Generated badge, editable textarea, generate/regenerate)
│   └── Translation Column
│       └── Panel (Your Translation textarea, draft indicator)
├── My Previous Submission (if exists)
└── Page Context Nav
```

### Shared Zoom State

Image and source text share zoom level via `useState` in `TranslateTab`. Font size scales proportionally: `fontSize = 14 * (zoom / 100)`.

---

## 7. Test Results

### Backend Tests

```
106 passed in 6.25s
```

All existing tests continue to pass. 18 new tests cover extraction and transliteration endpoints.

### Frontend Tests

```
75 passed (11 test files)
```

All existing tests continue to pass. 18 new tests cover SourceTextPanel component.

### Type Check

```
tsc --noEmit — 0 errors
```

### Lint

```
0 errors, 2 warnings (pre-existing in PageEditor.tsx, not from this feature)
```

---

## 8. Graceful Degradation

- If `OPENAI_API_KEY` is not set, AI features return errors but the app continues working with OCR text
- Transliteration failures show "Transliteration unavailable — enter manually"
- Extraction failures retain OCR text and show retry button
- All new Section fields (`aiExtractedText`, `extractionStatus`) are optional

---

## 9. Database Collections

| Collection            | Index                                      | Purpose                                      |
| --------------------- | ------------------------------------------ | -------------------------------------------- |
| `ai_text_extractions` | `{ sectionId: 1 }` unique                  | One extraction per section, idempotent       |
| `transliterations`    | `{ sectionId: 1, targetScript: 1 }` unique | Cached transliterations per section+language |
| `system_config`       | `{ key: 1 }` unique                        | Key-value config store for admin settings    |
| `redis_progress`      | `{ bookId: 1 }`                            | Batch extraction progress tracking           |

---

## 10. Implementation Notes

1. **OpenAI integration uses httpx** — consistent with existing `translate.py` LibreTranslate integration
2. **Confidence scoring** uses a separate GPT-4o text call (not Vision) for cost efficiency
3. **Transliteration caching** uses MongoDB (not Redis) per the architecture spec
4. **Bidirectional sync** is one-way: source text edits invalidate transliteration cache, transliteration edits are independent (manual override)
5. **Debounced source text saves** are handled via `useCallback` with 500ms timeout in SourceTextPanel
