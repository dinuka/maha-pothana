# Source Text Modifications — User Stories

**Date:** 2026-07-06 13:00
**Author:** Business Analysis Agent
**Epic Reference:** Epic 1 — Book Upload & Processing, Epic 4 — Translation

---

## Context

The current workflow relies on Tesseract OCR for text extraction from section images. Tesseract produces poor results for Indic scripts (Sinhala, Tamil, Devanagari) due to complex ligatures and conjunct characters. Translators currently have no automated way to generate letter-for-letter transliterations between Indic scripts — they do it manually, which is error-prone and slow. This set of stories introduces AI-powered text extraction and transliteration to dramatically improve source text quality and translator efficiency.

---

## User Stories

### US-ST-1: AI Text Extraction for Sections

**As an** editor
**I want to** trigger AI-powered text extraction on section images
**So that** the source text is more accurate than Tesseract OCR, especially for Indic scripts.

**Acceptance Criteria:**

- After sections are confirmed (cropped), an "Extract Text" button is available per-section and as a batch action for the entire page
- Clicking "Extract Text" enqueues a background job that sends the cropped section image to an AI vision model (e.g. GPT-4o or similar)
- Extracted text is saved to `Section.aiExtractedText` and to `AITextExtraction` collection for audit
- The extraction result shows a confidence score displayed as a badge (green ≥ 0.9, yellow ≥ 0.7, red < 0.7)
- Editors can compare OCR text vs AI text side-by-side in the section detail view
- If AI extraction fails (timeout, API error), the section retains its OCR text and shows an error toast
- Batch extraction processes sections in parallel (max 5 concurrent) with a progress indicator
- Extraction is idempotent — re-running replaces the previous AI extraction result
- AI extraction cost is estimated and displayed before running ("This will process 12 sections — estimated cost: $0.04")

**API (new):**

- `POST /api/sections/{sectionId}/extract` — trigger single-section extraction
- `POST /api/books/{bookId}/pages/{pageNum}/extract` — batch extract all sections on a page
- `GET /api/sections/{sectionId}/extraction` — fetch extraction result with confidence

**Backend:**

- New `AITextExtraction` collection (defined in `data-model.md`)
- Celery task `extract_section_text` processes one section: downloads cropped image from MinIO, sends to vision model API, stores result
- Rate limiting via Redis semaphore (max 5 concurrent extractions)
- Model response cached in `AITextExtraction.rawResponse` for debugging

---

### US-ST-2: AI Transliteration Between Indic Scripts

**As a** translator
**I want to** see an AI-generated letter-for-letter transliteration of the source text
**So that** I can quickly understand the phonetic structure of the source without manually converting scripts.

**Acceptance Criteria:**

- When a section has `aiExtractedText`, the translation editor shows a "Transliterate" button
- Clicking "Transliterate" generates a letter-for-letter conversion from the source script to the target script (e.g. Devanagari → Sinhala)
- The transliteration is displayed in a read-only field labeled "AI Transliteration" between the source text and translation input
- Transliteration is pre-filled into the `exactLetterTranslation` field of the Translation document
- The translator can edit the pre-filled transliteration before submitting
- Transliteration source is marked as "ai" in `Translation.transliterationSource`
- If the translator manually types an `exactLetterTranslation`, it is marked as "manual"
- Transliterations are cached per section+language pair (stored in `Transliteration` collection)
- Regenerating a transliteration overwrites the previous result and updates the cache
- If transliteration fails, show "Transliteration unavailable — enter manually" and leave the field empty

**API (new):**

- `POST /api/sections/{sectionId}/transliterate?targetScript={script}` — generate transliteration
- `GET /api/sections/{sectionId}/transliterations` — fetch cached transliterations

**Backend:**

- New `Transliteration` collection (defined in `data-model.md`)
- Celery task `transliterate_section` uses an Indic script transliteration model
- Cache lookup before API call: if `Transliteration` exists for section+targetScript, return cached
- `exactLetterTranslation` on Translation is auto-populated from the transliteration result

---

### US-ST-3: Replace OCR Text with AI Extracted Text in Translation Flow

**As a** translator
**I want to** see the AI-extracted text instead of OCR text when it's available
**So that** I work with accurate source text and produce better translations.

**Acceptance Criteria:**

- The translation editor shows `aiExtractedText` as the primary source text when it exists, falling back to `originalText` (OCR) if not
- The source text panel has a toggle: "Show AI text" (default: on) / "Show OCR text"
- The auto-translation from LibreTranslate is triggered on the AI-extracted text (not OCR) when available
- If `aiExtractedText` is empty or extraction failed, the system silently falls back to `originalText`
- The source text panel clearly labels which text is displayed: "AI Extracted" or "OCR"
- Editors see both texts in the section detail view for comparison
- Translators see only the active source text (AI or OCR) by default

**No new API required** — `Section.aiExtractedText` is returned by the existing sections API. Translation endpoint uses the best available text.

**Backend:**

- `GET /api/sections/next` returns both `originalText` and `aiExtractedText` — client decides which to display
- Auto-translation Celery task checks `aiExtractedText` first, falls back to `originalText`

---

### US-ST-4: Section-Level Extraction Status Tracking

**As an** editor
**I want to** see which sections have been AI-extracted and which haven't
**So that** I can track extraction progress and know what work remains.

**Acceptance Criteria:**

- The book page view shows an "Extraction Status" overlay on each section thumbnail: "Extracted" (green), "Pending" (gray), "Failed" (red)
- A page-level summary shows: "8/12 sections extracted" with a progress bar
- The book dashboard shows extraction stats: total sections, extracted count, pending count, failed count
- Clicking "Failed" sections opens a retry dialog
- The section list in the book console is filterable by extraction status (ALL, EXTRACTED, PENDING, FAILED)
- Extraction status is derived from the presence of `AITextExtraction` document for the section
- Failed extractions are logged with error reason in `AITextExtraction.rawResponse`

**API:**

- `GET /api/books/{bookId}/stats` — add `extractionStats` field to `TranslationStats`
- Existing `GET /api/books/{bookId}/pages` returns extraction status per section

**Backend:**

- Aggregation pipeline counts sections with/without `AITextExtraction` documents
- `extractionStats` added to the `TranslationStats` computed entity

---

### US-ST-5: Batch Auto-Extract All Sections for a Book

**As an** editor
**I want to** trigger AI text extraction for all sections in a book with one click
**So that** I can prepare the entire book for translation without manually extracting each section.

**Acceptance Criteria:**

- The book console shows an "Extract All Sections" button (visible only when book has unextracted sections)
- Clicking the button shows a confirmation dialog: "This will extract text from 156 sections. Estimated cost: $1.28. Proceed?"
- Extraction runs as a background Celery task chain — one task per section, 5 concurrent
- Progress is displayed in real-time: "Extracting section 34/156..." with a progress bar
- Completed sections update their status overlay immediately (poll every 5s or WebSocket)
- If any section fails, the batch continues — failures are collected and shown in a summary at the end
- The summary shows: "154 extracted, 2 failed" with a "Retry Failed" button
- The "Extract All" button is disabled while a batch is in progress
- If a batch is already running, the button shows "Extraction in progress (34/156)" instead

**API:**

- `POST /api/books/{bookId}/extract` — trigger batch extraction for entire book
- `GET /api/books/{bookId}/extraction/status` — return batch progress

**Backend:**

- New Celery task `batch_extract_book` creates a chain of `extract_section_text` tasks
- Progress tracked in Redis: `{bookId}:extraction:progress` with fields `total`, `completed`, `failed`
- Redis key expires after 1 hour (TTL)
- Concurrency limited by Redis semaphore (max 5)

---

### US-ST-6: Configure AI Extraction Model and Thresholds

**As a** super admin
**I want to** configure which AI model is used for extraction and what confidence thresholds to apply
**So that** I can balance extraction quality vs. cost and adapt to different book types.

**Acceptance Criteria:**

- The admin settings page (`/admin/settings`) shows an "AI Extraction" section
- Configurable fields: model name (dropdown), confidence threshold (slider 0.0–1.0, default 0.7), max concurrent extractions (1–10, default 5), cost limit per book (in USD)
- Changes are saved to a `SystemConfig` MongoDB collection
- The confidence threshold determines the badge color in the UI: ≥ threshold = green, < threshold = red
- If confidence falls below threshold, the extraction is still saved but flagged for manual review
- Cost limit is enforced before batch extraction starts — if estimated cost exceeds limit, the batch is blocked with a warning
- Model changes take effect on the next extraction (no need to restart services)
- Admin can view extraction audit log: which model was used, cost per extraction, confidence scores

**API (new):**

- `GET /api/admin/settings/extraction` — fetch current config
- `PUT /api/admin/settings/extraction` — update config
- `GET /api/admin/extraction/audit` — fetch extraction audit log

**Backend:**

- New `SystemConfig` collection with `key` unique index
- Config is loaded into memory on startup and refreshed every 5 minutes
- Audit log stored in `AITextExtraction` collection (query by `model` and `confidence`)

---

## Implementation Priority

| Priority | Story                                                              | Effort | Impact                                                              |
| -------- | ------------------------------------------------------------------ | ------ | ------------------------------------------------------------------- |
| P0       | US-ST-1: AI Text Extraction for Sections                          | Large  | Foundation — all other stories depend on extracted text existing     |
| P0       | US-ST-3: Replace OCR with AI Text in Translation Flow             | Small  | Immediate translator UX improvement — works once extraction exists   |
| P1       | US-ST-2: AI Transliteration Between Indic Scripts                 | Medium | High — eliminates manual transliteration work                       |
| P1       | US-ST-4: Section-Level Extraction Status Tracking                 | Medium | High — visibility into extraction progress                          |
| P2       | US-ST-5: Batch Auto-Extract All Sections for a Book               | Medium | Medium — convenience, but single-section extraction works as fallback |
| P3       | US-ST-6: Configure AI Extraction Model and Thresholds             | Small  | Low — only needed after extraction is working in production          |

---

## Key Insights

1. **AI extraction is the foundation** — US-ST-1 must ship first. All other stories depend on `Section.aiExtractedText` being populated. The extraction task is a Celery job that can run async after sections are confirmed.

2. **Transliteration is separate from extraction** — they use different models (vision vs. script conversion). Keeping them in separate collections (`AITextExtraction` vs. `Transliteration`) keeps concerns clean and allows independent caching.

3. **Graceful fallback is essential** — every story must handle the case where AI extraction fails or is unavailable. OCR text remains the fallback; translators are never blocked by AI unavailability.

4. **Cost awareness matters** — AI extraction costs real money. US-ST-1 shows per-section estimates, US-ST-5 shows batch estimates, and US-ST-6 enforces configurable cost limits. This prevents accidental budget blowouts.

5. **Confidence scores drive UX** — the threshold configuration in US-ST-6 lets admins tune what counts as "good enough" for their books. Low-confidence extractions are flagged for review rather than silently accepted.

6. **Batch processing needs concurrency control** — the Redis semaphore (max 5 concurrent) prevents API rate limiting and keeps costs predictable. The progress tracking in Redis is lightweight and expires automatically.

---

## Related Files

- `specs/business-analysis/actors.md` — updated with AI Agent role and 3 new permissions
- `specs/business-analysis/data-model.md` — updated with AITextExtraction, Transliteration, Section.aiExtractedText, Translation.transliterationSource
- `specs/business-analysis/20260706-1200-translation-page-redesign.md` — previous translation UI redesign
