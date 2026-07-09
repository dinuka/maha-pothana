# Source Text Modifications — QA Test Plan

**Date:** 2026-07-06 13:00
**Author:** QA Agent
**Related BA:** `specs/business-analysis/20260706-1300-source-text-modifications.md`
**Related Architecture:** `specs/architecture/20260706-1300-source-text-modifications.md`
**Related UX:** `specs/ux/20260706-1300-source-text-modifications.md`
**Related UI Design:** `specs/ux/ui-design.md`

---

## 1. Scope

This test plan covers the Source Text Modifications feature: six user stories (US-ST-1 through US-ST-6) that introduce AI-powered text extraction, transliteration between Indic scripts, bidirectional sync, extraction status tracking, batch extraction, and admin configuration.

---

## 2. Test Environment Setup

### Prerequisites

- MongoDB running locally or in Docker (`docker compose -f infra/docker-compose.dev.yml up -d`)
- Redis running for caching, Celery, and semaphores
- MinIO running for S3 file storage
- LibreTranslate running for auto-translation
- OpenAI API key configured (`OPENAI_API_KEY` in `.env`)
- Next.js dev server on port 3000 (`pnpm dev`)
- FastAPI dev server on port 8000 (`cd apps/api && uvicorn app.main:app --reload`)
- Celery worker running (`cd apps/api && celery -A app.tasks.celery_app worker --loglevel=info`)
- Test user accounts: one Editor, one Translator, one Super Admin
- A book with sections already uploaded, processed, section-detected, and cropped

### Test Data Requirements

| Data                                              | Purpose                                | Setup                                        |
| ------------------------------------------------- | -------------------------------------- | -------------------------------------------- |
| Book with 10+ pages, 50+ sections, cropped images | Extraction, transliteration, batch ops | Upload PDF, detect sections, confirm, crop   |
| Sections with varied Indic script content         | Accuracy testing                       | Use Sinhala, Tamil, Devanagari source images |
| Sections with no text (blank images)              | Edge case for extraction               | Include blank/low-content page images        |
| Sections already AI-extracted                     | Cache, regeneration, status tracking   | Run extraction on subset of sections         |
| Section with failed extraction                    | Retry, error state testing             | Mock OpenAI API failure for specific section |
| OpenAI API key (test mode)                        | AI integration                         | Use test key or mock responses               |
| Multi-language book (si, ta)                      | Transliteration testing                | Set `translateLanguages: ["si", "ta"]`       |
| Admin config with custom thresholds               | US-ST-6 testing                        | Set via API or direct DB insert              |

### Test User Accounts

| User                  | Role        | Purpose                                             |
| --------------------- | ----------- | --------------------------------------------------- |
| editor@test.com       | EDITOR      | Trigger extraction, view status, configure settings |
| translator-a@test.com | TRANSLATOR  | Transliterate, translate, edit source text          |
| admin@test.com        | SUPER_ADMIN | Configure AI model, thresholds, cost limits         |

---

## 3. US-ST-1: AI Text Extraction for Sections

### 3.1 Single Section Extraction — API

| TC-ID  | Scenario                               | Steps                                                                             | Expected Result                                                                                            |
| ------ | -------------------------------------- | --------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| ST1-01 | Trigger extraction — success           | 1. `POST /api/sections/{sectionId}/extract` with valid section                    | 202: `{ taskId, sectionId, status: "queued" }`                                                             |
| ST1-02 | Trigger extraction — no cropped image  | 1. `POST /api/sections/{sectionId}/extract` for section without `croppedImageKey` | 422: `{ detail: "Section has no cropped image. Crop sections first." }`                                    |
| ST1-03 | Trigger extraction — already extracted | 1. Extract section 2. `POST` again for same section                               | 409: `{ sectionId, status: "completed", extractedText, confidence }` — idempotent, returns existing result |
| ST1-04 | Fetch extraction result — success      | 1. `GET /api/sections/{sectionId}/extraction` after extraction completes          | 200: `{ sectionId, extractedText, confidence, model, processingTimeMs, createdAt }`                        |
| ST1-05 | Fetch extraction result — not found    | 1. `GET /api/sections/{sectionId}/extraction` for unextracted section             | 404: `{ detail: "No extraction found for this section" }`                                                  |
| ST1-06 | Extraction returns correct text        | 1. Use section with known Sinhala text 2. Extract 3. Compare                      | `aiExtractedText` matches expected text (character-level accuracy)                                         |
| ST1-07 | Extraction returns valid confidence    | 1. Extract section 2. Check response                                              | `confidence` is float between 0.0 and 1.0                                                                  |
| ST1-08 | Extraction records model used          | 1. Extract section 2. Check `AITextExtraction` document                           | `model` field set to configured model (default "gpt-4o")                                                   |
| ST1-09 | Extraction records processing time     | 1. Extract section 2. Check response                                              | `processingTimeMs` is positive integer                                                                     |
| ST1-10 | Extraction stores raw response         | 1. Extract section 2. Check `AITextExtraction.rawResponse`                        | Raw OpenAI API response stored for debugging                                                               |

### 3.2 Single Section Extraction — Celery Task

| TC-ID  | Scenario                                   | Steps                                                           | Expected Result                                                                     |
| ------ | ------------------------------------------ | --------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| ST1-11 | Task acquires Redis semaphore              | 1. Trigger extraction 2. Check Redis key `extraction:semaphore` | Semaphore acquired before API call                                                  |
| ST1-12 | Task releases Redis semaphore              | 1. Trigger extraction 2. Wait for completion                    | Semaphore released after task completes                                             |
| ST1-13 | Task updates Section.aiExtractedText       | 1. Trigger extraction 2. Wait for completion 3. Fetch section   | `Section.aiExtractedText` populated with extracted text                             |
| ST1-14 | Task creates AITextExtraction document     | 1. Trigger extraction 2. Check `ai_text_extractions` collection | Document exists with sectionId, text, confidence, model, timestamps                 |
| ST1-15 | Task handles OpenAI timeout                | 1. Mock OpenAI API to timeout (30s) 2. Trigger extraction       | Task retries up to 3 times with exponential backoff                                 |
| ST1-16 | Task handles OpenAI 500 error              | 1. Mock OpenAI API to return 500 2. Trigger extraction          | Error logged, extraction marked FAILED, section retains OCR text                    |
| ST1-17 | Task handles OpenAI rate limit             | 1. Mock OpenAI API to return 429 2. Trigger extraction          | Task waits and retries; semaphore prevents this from happening in practice          |
| ST1-18 | Task handles empty response                | 1. Mock OpenAI to return empty text 2. Trigger extraction       | Extraction saved with empty text, confidence = 0.0, marked FAILED                   |
| ST1-19 | Task handles image too large               | 1. Use section with >20MB cropped image 2. Trigger extraction   | Image resized before API call, extraction proceeds                                  |
| ST1-20 | Task handles network error                 | 1. Mock network failure 2. Trigger extraction                   | Task retries up to 3 times, then marks FAILED                                       |
| ST1-21 | Extraction is idempotent — re-run replaces | 1. Extract section (result A) 2. Re-extract section (result B)  | Previous `AITextExtraction` replaced; `Section.aiExtractedText` updated to result B |

### 3.3 Confidence Score and Badge

| TC-ID  | Scenario                          | Steps                                                         | Expected Result                                        |
| ------ | --------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------ |
| ST1-22 | High confidence badge (green)     | 1. Section with confidence ≥ 0.9 2. View source text panel    | Green badge: `[AI Extracted] 94% ●`                    |
| ST1-23 | Medium confidence badge (yellow)  | 1. Section with confidence ≥ 0.7 and < 0.9 2. View panel      | Yellow badge: `[AI Extracted] 78% ●`                   |
| ST1-24 | Low confidence badge (red)        | 1. Section with confidence < 0.7 2. View panel                | Red badge: `[AI Extracted] 45% ●`                      |
| ST1-25 | Badge uses configurable threshold | 1. Set admin threshold to 0.8 2. Section with confidence 0.85 | Badge shows yellow (below 0.9 but above 0.8 threshold) |
| ST1-26 | OCR fallback badge (gray)         | 1. Section without AI extraction 2. View panel                | Gray badge: `[OCR] ●`                                  |
| ST1-27 | Extraction in-progress badge      | 1. Trigger extraction 2. Immediately view panel               | Blue animated badge: `[Extracting...] ●○○`             |

### 3.4 Editor UI — Extract Button

| TC-ID  | Scenario                                            | Steps                                                   | Expected Result                                                                                              |
| ------ | --------------------------------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| ST1-28 | Extract button visible to editors                   | 1. Login as editor 2. Section without AI extraction     | "Extract Text" button visible below source text panel                                                        |
| ST1-29 | Extract button hidden from translators              | 1. Login as translator 2. Section without AI extraction | "Extract Text" button NOT visible                                                                            |
| ST1-30 | Extract button triggers extraction                  | 1. Click "Extract Text" 2. Check API call               | `POST /api/sections/{id}/extract` called                                                                     |
| ST1-31 | Extract button replaced by Regenerate after success | 1. Section already extracted 2. View panel              | "Regenerate" button shown instead of "Extract Text"                                                          |
| ST1-32 | Regenerate shows confirmation dialog                | 1. Click "Regenerate"                                   | Dialog: "Re-extract text from this section image? This will replace the current AI text." [Cancel] [Confirm] |
| ST1-33 | Regenerate cancel does nothing                      | 1. Click "Regenerate" 2. Click Cancel                   | No API call, existing extraction unchanged                                                                   |
| ST1-34 | Regenerate confirm triggers re-extraction           | 1. Click "Regenerate" 2. Confirm                        | `POST /api/sections/{id}/extract` called, previous result replaced                                           |

### 3.5 Side-by-Side Comparison

| TC-ID  | Scenario                           | Steps                                                | Expected Result                                          |
| ------ | ---------------------------------- | ---------------------------------------------------- | -------------------------------------------------------- |
| ST1-35 | Editor sees both texts             | 1. Login as editor 2. Section with AI extraction     | Both OCR text and AI text visible in section detail view |
| ST1-36 | Toggle shows AI text               | 1. Click "Show AI text" toggle                       | AI-extracted text displayed, labeled "AI Extracted"      |
| ST1-37 | Toggle shows OCR text              | 1. Click "Show OCR text" toggle                      | Original OCR text displayed, labeled "OCR"               |
| ST1-38 | Toggle defaults to AI text         | 1. Section with AI extraction 2. View panel          | AI text shown by default                                 |
| ST1-39 | Translator sees active source only | 1. Login as translator 2. Section with AI extraction | Only AI text shown by default (no toggle for translator) |

---

## 4. US-ST-2: AI Transliteration Between Indic Scripts

### 4.1 Transliteration API

| TC-ID  | Scenario                                  | Steps                                                                                                     | Expected Result                                                                      |
| ------ | ----------------------------------------- | --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| ST2-01 | Generate transliteration — success        | 1. `POST /api/sections/{sectionId}/transliterate?targetScript=sinhala`                                    | 200 or 202: transliteration result or queued task                                    |
| ST2-02 | Generate transliteration — cached         | 1. Generate transliteration 2. `POST` again same section+script                                           | 200: `{ ..., cached: true }` — no new API call to OpenAI                             |
| ST2-03 | Generate transliteration — no source text | 1. `POST /api/sections/{sectionId}/transliterate` for section with no `aiExtractedText` or `originalText` | 422: `{ detail: "No source text available. Run AI extraction first." }`              |
| ST2-04 | Fetch cached transliterations             | 1. `GET /api/sections/{sectionId}/transliterations`                                                       | 200: array of transliterations with targetScript, text, confidence, model, createdAt |
| ST2-05 | Fetch transliterations — empty            | 1. `GET /api/sections/{sectionId}/transliterations` for section with no transliterations                  | 200: `{ sectionId, transliterations: [] }`                                           |
| ST2-06 | Transliteration matches source text       | 1. Use known Devanagari source text 2. Transliterate to Sinhala                                           | Transliterated text is correct letter-for-letter conversion                          |
| ST2-07 | Transliteration preserves word boundaries | 1. Transliterate multi-word source text                                                                   | Spaces preserved in transliterated output                                            |
| ST2-08 | Transliteration returns confidence        | 1. Generate transliteration 2. Check response                                                             | `confidence` is float between 0.0 and 1.0                                            |
| ST2-09 | Transliteration returns model used        | 1. Generate transliteration 2. Check response                                                             | `model` field set to "gpt-4o"                                                        |

### 4.2 Transliteration — Celery Task

| TC-ID  | Scenario                                 | Steps                                                                    | Expected Result                                                         |
| ------ | ---------------------------------------- | ------------------------------------------------------------------------ | ----------------------------------------------------------------------- |
| ST2-10 | Task checks cache before API call        | 1. Create `Transliteration` document manually 2. Trigger transliteration | Task returns cached result, no OpenAI API call                          |
| ST2-11 | Task determines source script from book  | 1. Book with `sourceLanguage: "devanagari"` 2. Transliterate             | Source script set to "devanagari" automatically                         |
| ST2-12 | Task saves to Transliteration collection | 1. Generate transliteration 2. Check `transliterations` collection       | Document exists with sectionId, sourceScript, targetScript, text, model |
| ST2-13 | Task handles OpenAI API error            | 1. Mock OpenAI failure 2. Trigger transliteration                        | Task retries up to 3 times, then fails gracefully                       |
| ST2-14 | Regenerating overwrites previous result  | 1. Generate transliteration A 2. Regenerate → result B                   | Previous Transliteration document replaced with result B                |

### 4.3 Transliteration UI

| TC-ID  | Scenario                                    | Steps                                                                                | Expected Result                                                     |
| ------ | ------------------------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------- |
| ST2-15 | Transliterate button visible with AI text   | 1. Section with `aiExtractedText` 2. View transliteration panel                      | "Generate with AI" button visible                                   |
| ST2-16 | Transliterate button hidden without AI text | 1. Section without `aiExtractedText` 2. View panel                                   | Button NOT visible                                                  |
| ST2-17 | Click triggers generation                   | 1. Click "Generate with AI"                                                          | Spinner shown, `POST /api/sections/{id}/transliterate` called       |
| ST2-18 | Result pre-fills exact letter field         | 1. Generation completes                                                              | `exactLetterTranslation` field pre-filled with transliterated text  |
| ST2-19 | Spinner shown during generation             | 1. Click generate 2. Check panel state                                               | `[Generating...] ●○○` badge, "Generating transliteration..." text   |
| ST2-20 | Cached result shown immediately             | 1. Section with cached transliteration 2. Load section                               | Transliteration pre-filled, green `[AI Generated] ●` badge          |
| ST2-21 | Regenerate button for cached                | 1. Section with cached transliteration 2. View panel                                 | "Regenerate" button visible below transliteration                   |
| ST2-22 | Manual edit marks as manual                 | 1. Edit pre-filled transliteration text 2. Check `Translation.transliterationSource` | Source changed to "manual"                                          |
| ST2-23 | Manual entry from empty                     | 1. Transliteration unavailable 2. Type transliteration manually                      | `[Manual] ●` badge shown, `transliterationSource: "manual"`         |
| ST2-24 | Failure shows manual prompt                 | 1. Transliteration API fails 2. View panel                                           | "Transliteration unavailable — enter manually" message, empty field |

### 4.4 Transliteration Caching

| TC-ID  | Scenario                        | Steps                                                  | Expected Result                                    |
| ------ | ------------------------------- | ------------------------------------------------------ | -------------------------------------------------- |
| ST2-25 | Cache hit returns immediately   | 1. Generate transliteration 2. Load same section again | Transliteration pre-filled from cache, no API call |
| ST2-26 | Cache per section+language pair | 1. Generate for Sinhala 2. Generate for Tamil          | Two separate Transliteration documents created     |
| ST2-27 | Regenerate overwrites cache     | 1. Generate transliteration 2. Regenerate              | Previous cache entry replaced, new result stored   |

---

## 5. US-ST-3: Replace OCR Text with AI Extracted Text

### 5.1 Translation Editor — Source Text Display

| TC-ID  | Scenario                           | Steps                                                       | Expected Result                                   |
| ------ | ---------------------------------- | ----------------------------------------------------------- | ------------------------------------------------- |
| ST3-01 | AI text shown as primary           | 1. Section with `aiExtractedText` 2. Open translate tab     | AI-extracted text displayed in source text panel  |
| ST3-02 | Fallback to OCR when no AI text    | 1. Section without `aiExtractedText` 2. Open translate tab  | OCR text (`originalText`) displayed               |
| ST3-03 | Toggle switches between AI and OCR | 1. Section with AI text 2. Click "Show OCR text" toggle     | OCR text displayed, labeled "OCR"                 |
| ST3-04 | Toggle defaults to AI text         | 1. Section with AI text 2. View panel                       | AI text shown, toggle set to "Show OCR text"      |
| ST3-05 | Label shows which text is active   | 1. View source text panel                                   | Label: "AI Extracted" or "OCR" clearly visible    |
| ST3-06 | Empty AI text falls back to OCR    | 1. Section with `aiExtractedText: ""` 2. Open translate tab | OCR text displayed, no empty panel                |
| ST3-07 | Failed extraction shows OCR        | 1. Section with failed extraction 2. Open translate tab     | OCR text displayed with "Extraction failed" badge |

### 5.2 Auto-Translation Uses AI Text

| TC-ID  | Scenario                                     | Steps                                                          | Expected Result                                       |
| ------ | -------------------------------------------- | -------------------------------------------------------------- | ----------------------------------------------------- |
| ST3-08 | Auto-translation uses AI text                | 1. Section with `aiExtractedText` 2. Check auto-translation    | LibreTranslate called with AI-extracted text, not OCR |
| ST3-09 | Auto-translation falls back to OCR           | 1. Section without `aiExtractedText` 2. Check auto-translation | LibreTranslate called with `originalText`             |
| ST3-10 | Auto-translation uses AI text when OCR empty | 1. Section with AI text but empty `originalText`               | Auto-translation uses AI text                         |

### 5.3 Sections API Returns Both Texts

| TC-ID  | Scenario                                   | Steps                              | Expected Result                                                             |
| ------ | ------------------------------------------ | ---------------------------------- | --------------------------------------------------------------------------- |
| ST3-11 | Next section returns both fields           | 1. `GET /api/sections/next`        | Response includes both `originalText` and `aiExtractedText`                 |
| ST3-12 | Section response includes extractionStatus | 1. `GET /api/sections/{sectionId}` | `extractionStatus` field present: "extracted" / "pending" / "failed" / null |

---

## 6. US-ST-4: Section-Level Extraction Status Tracking

### 6.1 Status Overlay on Section Thumbnails

| TC-ID  | Scenario                              | Steps                                                | Expected Result                                   |
| ------ | ------------------------------------- | ---------------------------------------------------- | ------------------------------------------------- |
| ST4-01 | Extracted section shows green overlay | 1. Section with `AITextExtraction` 2. View book page | Green "Extracted" badge on section thumbnail      |
| ST4-02 | Pending section shows gray overlay    | 1. Section without `AITextExtraction` 2. View page   | Gray "Pending" badge on section thumbnail         |
| ST4-03 | Failed section shows red overlay      | 1. Section with failed extraction 2. View page       | Red "Failed" badge on section thumbnail           |
| ST4-04 | Click Failed opens retry dialog       | 1. Click "Failed" badge on section                   | Retry dialog opens with "Retry Extraction" option |

### 6.2 Page-Level Progress

| TC-ID  | Scenario                            | Steps                                          | Expected Result                                  |
| ------ | ----------------------------------- | ---------------------------------------------- | ------------------------------------------------ |
| ST4-05 | Page summary shows extraction count | 1. View page with mixed extraction states      | "8/12 sections extracted" with progress bar      |
| ST4-06 | Progress bar reflects actual counts | 1. Extract 3 of 6 sections 2. View page        | Progress bar shows 50%, "3/6 sections extracted" |
| ST4-07 | All extracted — full bar            | 1. All sections on page extracted 2. View page | "6/6 sections extracted", full progress bar      |

### 6.3 Book Dashboard Stats

| TC-ID  | Scenario                           | Steps                                                        | Expected Result                                                       |
| ------ | ---------------------------------- | ------------------------------------------------------------ | --------------------------------------------------------------------- |
| ST4-08 | Stats API includes extractionStats | 1. `GET /api/books/{bookId}/stats`                           | `extractionStats` field with total, extracted, pending, failed counts |
| ST4-09 | Stats counts are accurate          | 1. Book with 50 sections, 30 extracted, 15 pending, 5 failed | Stats match: total=50, extracted=30, pending=15, failed=5             |
| ST4-10 | Stats update after extraction      | 1. Extract a pending section 2. Re-fetch stats               | Extracted count increments, pending decrements                        |

### 6.4 Filter by Extraction Status

| TC-ID  | Scenario               | Steps                             | Expected Result                                           |
| ------ | ---------------------- | --------------------------------- | --------------------------------------------------------- |
| ST4-11 | Filter option visible  | 1. Open book console section list | Extraction status filter: ALL, EXTRACTED, PENDING, FAILED |
| ST4-12 | Filter by EXTRACTED    | 1. Select "EXTRACTED" filter      | Only extracted sections shown                             |
| ST4-13 | Filter by PENDING      | 1. Select "PENDING" filter        | Only unextracted sections shown                           |
| ST4-14 | Filter by FAILED       | 1. Select "FAILED" filter         | Only failed sections shown                                |
| ST4-15 | Clear filter shows all | 1. Apply filter 2. Clear          | All sections shown                                        |

### 6.5 Batch Extraction Progress API

| TC-ID  | Scenario                             | Steps                                          | Expected Result                                                     |
| ------ | ------------------------------------ | ---------------------------------------------- | ------------------------------------------------------------------- |
| ST4-16 | GET extraction status returns counts | 1. `GET /api/books/{bookId}/extraction/status` | `{ bookId, totalSections, extracted, pending, failed, inProgress }` |
| ST4-17 | inProgress flag accurate             | 1. Trigger batch extraction 2. Check status    | `inProgress: true` during extraction                                |
| ST4-18 | inProgress false when idle           | 1. No batch running 2. Check status            | `inProgress: false`                                                 |

---

## 7. US-ST-5: Batch Auto-Extract All Sections

### 7.1 Batch Extraction API

| TC-ID  | Scenario                            | Steps                                                 | Expected Result                                                           |
| ------ | ----------------------------------- | ----------------------------------------------------- | ------------------------------------------------------------------------- |
| ST5-01 | Trigger batch — success             | 1. `POST /api/books/{bookId}/extract`                 | 202: `{ taskId, bookId, totalSections, estimatedCost, status: "queued" }` |
| ST5-02 | Trigger batch — already in progress | 1. Trigger batch 2. `POST` again                      | 409: `{ bookId, status: "in_progress", completed, total, failed }`        |
| ST5-03 | Estimated cost returned             | 1. Trigger batch 2. Check response                    | `estimatedCost` matches `sectionCount * 0.007`                            |
| ST5-04 | Page-level batch extraction         | 1. `POST /api/books/{bookId}/pages/{pageNum}/extract` | 202: extracts all sections on that page                                   |

### 7.2 Batch Extraction — Celery Task

| TC-ID  | Scenario                              | Steps                                                              | Expected Result                                        |
| ------ | ------------------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------ |
| ST5-05 | Task creates chain of extract tasks   | 1. Trigger batch 2. Check Celery logs                              | Individual `extract_section_text` tasks created        |
| ST5-06 | Concurrency limited to 5              | 1. Trigger batch with 20 sections 2. Monitor concurrent tasks      | Max 5 concurrent extractions (Redis semaphore)         |
| ST5-07 | Progress tracked in Redis             | 1. Trigger batch 2. Check Redis key `{bookId}:extraction:progress` | Fields: total, completed, failed                       |
| ST5-08 | Progress updates incrementally        | 1. Trigger batch 2. Poll progress                                  | `completed` field increments as sections finish        |
| ST5-09 | Individual failure doesn't stop batch | 1. One section's extraction fails 2. Batch continues               | Remaining sections processed, failed count incremented |
| ST5-10 | Redis key expires after 1 hour        | 1. Trigger batch 2. Wait 1 hour (or mock TTL)                      | Redis key auto-deleted                                 |
| ST5-11 | Cost limit enforced                   | 1. Set cost limit to $0.50 2. Book with 100 sections (est. $0.70)  | Batch blocked: cost exceeds limit                      |

### 7.3 Batch Extraction — UI

| TC-ID  | Scenario                                | Steps                                                  | Expected Result                                                                     |
| ------ | --------------------------------------- | ------------------------------------------------------ | ----------------------------------------------------------------------------------- |
| ST5-12 | Extract All button visible              | 1. Book with unextracted sections 2. View book console | "Extract All Sections" button visible                                               |
| ST5-13 | Extract All hidden when all extracted   | 1. All sections extracted 2. View console              | Button NOT visible                                                                  |
| ST5-14 | Confirmation dialog shows cost          | 1. Click "Extract All"                                 | Dialog: "This will extract text from 156 sections. Estimated cost: $1.28. Proceed?" |
| ST5-15 | Confirmation proceeds on confirm        | 1. Click "Proceed" in dialog                           | Batch extraction triggered, progress indicator shown                                |
| ST5-16 | Confirmation cancelled                  | 1. Click "Cancel" in dialog                            | No extraction triggered                                                             |
| ST5-17 | Progress bar during batch               | 1. Trigger batch 2. View console                       | "Extracting section 34/156..." with progress bar                                    |
| ST5-18 | Section status updates in real-time     | 1. Trigger batch 2. Watch section thumbnails           | Status overlays update as sections complete (poll every 5s)                         |
| ST5-19 | Button disabled during batch            | 1. Batch in progress 2. Check button state             | "Extract All Sections" button disabled                                              |
| ST5-20 | Button shows progress when batch active | 1. Batch in progress 2. Check button text              | Button shows "Extraction in progress (34/156)"                                      |
| ST5-21 | Summary after batch completes           | 1. Batch completes 2. View summary                     | "154 extracted, 2 failed" with "Retry Failed" button                                |
| ST5-22 | Retry Failed re-runs failed sections    | 1. Click "Retry Failed"                                | Only failed sections re-extracted                                                   |
| ST5-23 | Retry Failed hidden when no failures    | 1. Batch completes with 0 failures                     | "Retry Failed" button NOT shown                                                     |

---

## 8. US-ST-6: Configure AI Extraction Model and Thresholds

### 8.1 Admin Settings API

| TC-ID  | Scenario                         | Steps                                                                       | Expected Result                                                                 |
| ------ | -------------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| ST6-01 | GET extraction config            | 1. `GET /api/admin/settings/extraction`                                     | 200: `{ model, confidenceThreshold, maxConcurrent, costLimitPerBook, enabled }` |
| ST6-02 | PUT update config                | 1. `PUT /api/admin/settings/extraction` with `{ confidenceThreshold: 0.8 }` | 200: config updated                                                             |
| ST6-03 | GET config after update          | 1. Update config 2. GET config                                              | Returned values match updates                                                   |
| ST6-04 | Config persisted in SystemConfig | 1. Update config 2. Check MongoDB `system_config` collection                | Key-value document exists with correct values                                   |

### 8.2 Admin Settings — UI

| TC-ID  | Scenario                        | Steps                                                    | Expected Result                                  |
| ------ | ------------------------------- | -------------------------------------------------------- | ------------------------------------------------ |
| ST6-05 | Admin settings page accessible  | 1. Login as super admin 2. Navigate to `/admin/settings` | AI Extraction section visible                    |
| ST6-06 | Model dropdown populated        | 1. View settings                                         | Dropdown shows available models (e.g., "gpt-4o") |
| ST6-07 | Confidence threshold slider     | 1. View settings                                         | Slider from 0.0 to 1.0, default 0.7              |
| ST6-08 | Max concurrent slider           | 1. View settings                                         | Slider from 1 to 10, default 5                   |
| ST6-09 | Cost limit input                | 1. View settings                                         | USD input field, default $5.00                   |
| ST6-10 | Save changes                    | 1. Modify settings 2. Click Save                         | Settings saved, success toast shown              |
| ST6-11 | Validation — invalid threshold  | 1. Set threshold to > 1.0 or < 0.0 2. Save               | Validation error shown                           |
| ST6-12 | Validation — invalid concurrent | 1. Set max concurrent to 0 or > 10 2. Save               | Validation error shown                           |

### 8.3 Config Effects on Extraction

| TC-ID  | Scenario                                 | Steps                                                                | Expected Result                                             |
| ------ | ---------------------------------------- | -------------------------------------------------------------------- | ----------------------------------------------------------- |
| ST6-13 | Confidence threshold affects badge color | 1. Set threshold to 0.8 2. Section with confidence 0.85              | Badge shows yellow (below 0.9 but above 0.8 threshold)      |
| ST6-14 | Low confidence flagged for review        | 1. Set threshold to 0.8 2. Section with confidence 0.6               | Extraction saved but flagged for manual review              |
| ST6-15 | Cost limit blocks batch                  | 1. Set cost limit to $0.10 2. Book with 50 sections (est. $0.35)     | Batch blocked with warning                                  |
| ST6-16 | Model change takes effect immediately    | 1. Change model from "gpt-4o" to "gpt-4o-mini" 2. Trigger extraction | New model used (check `AITextExtraction.model`)             |
| ST6-17 | Max concurrent affects semaphore         | 1. Set max concurrent to 3 2. Trigger batch                          | Only 3 concurrent extractions at a time                     |
| ST6-18 | Disabled extraction blocks triggers      | 1. Set `enabled: false` 2. Click "Extract Text"                      | Extraction blocked with message "AI extraction is disabled" |

### 8.4 Audit Log

| TC-ID  | Scenario                           | Steps                                  | Expected Result                                                 |
| ------ | ---------------------------------- | -------------------------------------- | --------------------------------------------------------------- |
| ST6-19 | Audit log endpoint                 | 1. `GET /api/admin/extraction/audit`   | Returns list of extraction records with model, cost, confidence |
| ST6-20 | Audit log filterable by model      | 1. GET audit with `?model=gpt-4o`      | Only gpt-4o extractions returned                                |
| ST6-21 | Audit log filterable by confidence | 1. GET audit with `?minConfidence=0.9` | Only high-confidence extractions returned                       |

---

## 9. Bidirectional Sync — Source Text ↔ Transliteration

### 9.1 Source Text Edit → Transliteration Invalidation

| TC-ID   | Scenario                               | Steps                                                                                  | Expected Result                                                                |
| ------- | -------------------------------------- | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| SYNC-01 | Edit source text invalidates cache     | 1. Load section with cached transliteration 2. Edit source text 3. Wait 500ms debounce | `PUT /api/sections/{id}/source-text` called, transliteration cache invalidated |
| SYNC-02 | Regenerate button appears after edit   | 1. Edit source text 2. Check transliteration panel                                     | "Regenerate" button pulses/appears on transliteration panel                    |
| SYNC-03 | Source text saved via debounce         | 1. Type in source text panel 2. Stop typing 3. Wait 500ms                              | API call made with updated text                                                |
| SYNC-04 | Debounce resets on continued typing    | 1. Type 2. Wait 300ms 3. Type more 4. Wait 500ms                                       | Single API call with final text                                                |
| SYNC-05 | Source text update failure shows toast | 1. Mock API failure 2. Edit source text                                                | "Failed to save source text changes" toast shown                               |

### 9.2 Transliteration Edit → No Source Text Change

| TC-ID   | Scenario                                    | Steps                                                                     | Expected Result                  |
| ------- | ------------------------------------------- | ------------------------------------------------------------------------- | -------------------------------- |
| SYNC-06 | Edit transliteration does not modify source | 1. Edit transliteration text 2. Check source text panel                   | Source text unchanged            |
| SYNC-07 | Manual transliteration marked as manual     | 1. Edit transliteration text 2. Check `Translation.transliterationSource` | Source changed to "manual"       |
| SYNC-08 | Manual edit does not trigger API call       | 1. Edit transliteration 2. Monitor network                                | No `PUT` to source-text endpoint |

### 9.3 No Infinite Loops

| TC-ID   | Scenario                                         | Steps                                                                       | Expected Result                                                   |
| ------- | ------------------------------------------------ | --------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| SYNC-09 | Source → transliteration invalidation is one-way | 1. Edit source text 2. Wait for invalidation 3. Check transliteration panel | Transliteration shows "Regenerate" but does NOT auto-update       |
| SYNC-10 | Rapid edits don't create loop                    | 1. Rapidly edit source text 10 times                                        | Only last edit triggers API call (debounce), no cascading updates |

### 9.4 Concurrent Edits

| TC-ID   | Scenario                                    | Steps                                                                      | Expected Result                                                                        |
| ------- | ------------------------------------------- | -------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| SYNC-11 | Two users edit source text simultaneously   | 1. User A edits source 2. User B edits source (different text)             | Last write wins. No data corruption.                                                   |
| SYNC-12 | Concurrent source and transliteration edits | 1. User A edits source text 2. User B edits transliteration simultaneously | Both saved independently. Source triggers invalidation. Transliteration marked manual. |

---

## 10. Layout and Responsive Design

### 10.1 Desktop Layout (>1024px)

| TC-ID  | Scenario                  | Steps                            | Expected Result                                                         |
| ------ | ------------------------- | -------------------------------- | ----------------------------------------------------------------------- |
| LAY-01 | Two-row four-panel layout | 1. View translate tab on desktop | Top row: image + source text. Bottom row: transliteration + translation |
| LAY-02 | Top row side-by-side      | 1. View top row                  | Image 50% width left, source text 50% width right                       |
| LAY-03 | Bottom row side-by-side   | 1. View bottom row               | Exact letter 50% left, translation editor 50% right                     |

### 10.2 Shared Zoom

| TC-ID  | Scenario                      | Steps                                       | Expected Result                                              |
| ------ | ----------------------------- | ------------------------------------------- | ------------------------------------------------------------ |
| LAY-04 | Zoom in scales image and text | 1. Click + zoom button                      | Image scales, source text font size increases proportionally |
| LAY-05 | Zoom out scales both          | 1. Click − zoom button                      | Image scales down, font size decreases proportionally        |
| LAY-06 | Reset zoom restores 100%      | 1. Zoom to 200% 2. Click ⟳                  | Both image and text return to 100%                           |
| LAY-07 | Zoom range 50%–300%           | 1. Zoom to minimum 2. Zoom to maximum       | Min 50%, max 300% enforced                                   |
| LAY-08 | Font scales proportionally    | 1. Zoom to 150% 2. Measure source text font | Font size = 14px × 1.5 = 21px                                |
| LAY-09 | Image drag-to-pan at any zoom | 1. Zoom to 200% 2. Drag image               | Image pans smoothly, all areas reachable                     |
| LAY-10 | Zoom controls below image     | 1. View layout                              | Controls: [−] {zoom}% [+] [⟳] positioned below image         |

### 10.3 Tablet Layout (768–1024px)

| TC-ID  | Scenario                                   | Steps                 | Expected Result                                                |
| ------ | ------------------------------------------ | --------------------- | -------------------------------------------------------------- |
| LAY-11 | Tablet side-by-side with collapsible image | 1. View on 768–1024px | Image panel collapsible, source text scrollable                |
| LAY-12 | Bottom row side-by-side                    | 1. View bottom row    | Transliteration and translation side-by-side with fixed height |

### 10.4 Mobile Layout (<768px)

| TC-ID  | Scenario                          | Steps             | Expected Result                             |
| ------ | --------------------------------- | ----------------- | ------------------------------------------- |
| LAY-13 | Mobile stacked layout             | 1. View on <768px | All four panels stacked vertically          |
| LAY-14 | Image full width, 240px height    | 1. View on mobile | Section image full width, fixed height      |
| LAY-15 | Source text below image           | 1. View on mobile | Source text panel below section image       |
| LAY-16 | Transliteration above translation | 1. View on mobile | Exact letter panel above translation editor |
| LAY-17 | Zoom controls overlay on mobile   | 1. View on mobile | Zoom controls inside image area as overlay  |
| LAY-18 | Source text fixed font on mobile  | 1. View on mobile | Font size fixed at 14px (no zoom scaling)   |

---

## 11. Backend API Test Cases

### 11.1 POST /api/sections/{sectionId}/extract

| TC-ID    | Scenario                 | Steps                                       | Expected Result          |
| -------- | ------------------------ | ------------------------------------------- | ------------------------ |
| API-ST01 | 202 on valid request     | 1. POST with valid section ID               | 202 with taskId          |
| API-ST02 | 409 on already extracted | 1. POST for extracted section               | 409 with existing result |
| API-ST03 | 422 on no cropped image  | 1. POST for section without croppedImageKey | 422 with error detail    |
| API-ST04 | 401 without auth         | 1. POST without Bearer token                | 401 Unauthorized         |

### 11.2 POST /api/books/{bookId}/pages/{pageNum}/extract

| TC-ID    | Scenario                  | Steps                                 | Expected Result                               |
| -------- | ------------------------- | ------------------------------------- | --------------------------------------------- |
| API-ST05 | 202 batch page extraction | 1. POST with valid bookId and pageNum | 202 with taskId, totalSections, estimatedCost |
| API-ST06 | 404 on invalid page       | 1. POST with nonexistent pageNum      | 404 error                                     |

### 11.3 POST /api/books/{bookId}/extract

| TC-ID    | Scenario                 | Steps                                                         | Expected Result                               |
| -------- | ------------------------ | ------------------------------------------------------------- | --------------------------------------------- |
| API-ST07 | 202 batch extraction     | 1. POST with valid bookId                                     | 202 with taskId, totalSections, estimatedCost |
| API-ST08 | 409 on in-progress batch | 1. Trigger batch 2. POST again                                | 409 with progress                             |
| API-ST09 | Cost limit blocked       | 1. Set cost limit 2. POST with estimated cost exceeding limit | 403 or 409 with warning                       |

### 11.4 GET /api/sections/{sectionId}/extraction

| TC-ID    | Scenario               | Steps                          | Expected Result               |
| -------- | ---------------------- | ------------------------------ | ----------------------------- |
| API-ST10 | 200 with extraction    | 1. GET for extracted section   | 200 with full extraction data |
| API-ST11 | 404 without extraction | 1. GET for unextracted section | 404 with detail               |

### 11.5 POST /api/sections/{sectionId}/transliterate

| TC-ID    | Scenario                 | Steps                                              | Expected Result       |
| -------- | ------------------------ | -------------------------------------------------- | --------------------- |
| API-ST12 | 200 cached result        | 1. POST for section with cached transliteration    | 200 with cached: true |
| API-ST13 | 202 new computation      | 1. POST for section without cached transliteration | 202 with taskId       |
| API-ST14 | 422 no source text       | 1. POST for section with no source text            | 422 with detail       |
| API-ST15 | 400 invalid targetScript | 1. POST with empty or invalid targetScript         | 400 Bad Request       |

### 11.6 GET /api/sections/{sectionId}/transliterations

| TC-ID    | Scenario                  | Steps                                           | Expected Result      |
| -------- | ------------------------- | ----------------------------------------------- | -------------------- |
| API-ST16 | 200 with transliterations | 1. GET for section with cached transliterations | 200 with array       |
| API-ST17 | 200 empty array           | 1. GET for section with no transliterations     | 200 with empty array |

### 11.7 PUT /api/sections/{sectionId}/source-text

| TC-ID    | Scenario                    | Steps                                        | Expected Result                                 |
| -------- | --------------------------- | -------------------------------------------- | ----------------------------------------------- |
| API-ST18 | 200 update AI text          | 1. PUT with `{ text, source: "ai" }`         | 200 with updatedText                            |
| API-ST19 | 200 update OCR text         | 1. PUT with `{ text, source: "ocr" }`        | 200 with updatedText                            |
| API-ST20 | Cache invalidated on update | 1. PUT source text 2. Check transliterations | Cached transliterations removed or marked stale |
| API-ST21 | 401 without auth            | 1. PUT without Bearer token                  | 401 Unauthorized                                |

### 11.8 GET /api/books/{bookId}/extraction/status

| TC-ID    | Scenario                | Steps                          | Expected Result                                                |
| -------- | ----------------------- | ------------------------------ | -------------------------------------------------------------- |
| API-ST22 | 200 with counts         | 1. GET extraction status       | 200 with totalSections, extracted, pending, failed, inProgress |
| API-ST23 | inProgress during batch | 1. Trigger batch 2. GET status | inProgress: true, completed increments                         |

### 11.9 GET /api/admin/settings/extraction

| TC-ID    | Scenario            | Steps            | Expected Result                                                               |
| -------- | ------------------- | ---------------- | ----------------------------------------------------------------------------- |
| API-ST24 | 200 config response | 1. GET as admin  | 200 with model, confidenceThreshold, maxConcurrent, costLimitPerBook, enabled |
| API-ST25 | 403 for non-admin   | 1. GET as editor | 403 Forbidden                                                                 |

### 11.10 PUT /api/admin/settings/extraction

| TC-ID    | Scenario           | Steps                                | Expected Result         |
| -------- | ------------------ | ------------------------------------ | ----------------------- |
| API-ST26 | 200 update config  | 1. PUT as admin with valid config    | 200 with updated config |
| API-ST27 | 422 invalid values | 1. PUT with confidenceThreshold: 2.0 | 422 Validation Error    |
| API-ST28 | 403 for non-admin  | 1. PUT as editor                     | 403 Forbidden           |

### 11.11 GET /api/admin/extraction/audit

| TC-ID    | Scenario          | Steps                       | Expected Result                            |
| -------- | ----------------- | --------------------------- | ------------------------------------------ |
| API-ST29 | 200 audit log     | 1. GET as admin             | 200 with array of extraction audit records |
| API-ST30 | Filter by model   | 1. GET with `?model=gpt-4o` | Only gpt-4o records returned               |
| API-ST31 | 403 for non-admin | 1. GET as editor            | 403 Forbidden                              |

---

## 12. Frontend Component Test Cases

| TC-ID   | Scenario                                            | Steps                                                   | Expected Result                                                          |
| ------- | --------------------------------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------ |
| FE-ST01 | SourceTextPanel renders AI text                     | 1. Render with `aiExtractedText`                        | AI text displayed with confidence badge                                  |
| FE-ST02 | SourceTextPanel renders OCR fallback                | 1. Render without `aiExtractedText`                     | OCR text displayed with gray badge                                       |
| FE-ST03 | SourceTextPanel shows extracting state              | 1. Render with `extractionStatus: "pending"`            | "Extracting..." indicator shown, OCR text as fallback                    |
| FE-ST04 | SourceTextPanel shows failed state                  | 1. Render with `extractionStatus: "failed"`             | "Extraction failed" badge, Retry button                                  |
| FE-ST05 | SourceTextPanel extract button (editor)             | 1. Render with `isEditor=true`, no AI text              | "Extract Text" button visible                                            |
| FE-ST06 | SourceTextPanel extract button hidden (translator)  | 1. Render with `isEditor=false`                         | Extract button NOT rendered                                              |
| FE-ST07 | SourceTextPanel zoom scales font                    | 1. Render with `zoom=150`                               | Font size = 14 × 1.5 = 21px                                              |
| FE-ST08 | ExtractionStatusBadge green                         | 1. Render with confidence 0.94                          | Green badge with "94%"                                                   |
| FE-ST09 | ExtractionStatusBadge yellow                        | 1. Render with confidence 0.78                          | Yellow badge with "78%"                                                  |
| FE-ST10 | ExtractionStatusBadge red                           | 1. Render with confidence 0.45                          | Red badge with "45%"                                                     |
| FE-ST11 | ExtractionStatusBadge gray (OCR)                    | 1. Render without confidence                            | Gray "OCR" badge                                                         |
| FE-ST12 | TransliterateButton renders with AI text            | 1. Render with `aiExtractedText` present                | Button visible                                                           |
| FE-ST13 | TransliterateButton hidden without AI text          | 1. Render without `aiExtractedText`                     | Button NOT rendered                                                      |
| FE-ST14 | TransliterateButton loading state                   | 1. Render with `isTransliterating=true`                 | Spinner shown, button disabled                                           |
| FE-ST15 | TransliterateButton calls onTransliterate           | 1. Click button                                         | `onTransliterate` callback fired with targetScript                       |
| FE-ST16 | useExtraction hook polls status                     | 1. Mount hook with pending extraction                   | Polls `GET /api/sections/{id}/extraction` every 2s                       |
| FE-ST17 | useExtraction hook stops on completion              | 1. Polling in progress 2. Extraction completes          | Polling stops, data updated                                              |
| FE-ST18 | useTransliteration hook caches result               | 1. Fetch transliteration 2. Fetch again                 | Second fetch from React Query cache (staleTime: 60s)                     |
| FE-ST19 | useSourceTextSync debounces API call                | 1. Call `updateSourceText` rapidly                      | Only last call triggers API after 500ms                                  |
| FE-ST20 | useSourceTextSync invalidates transliteration cache | 1. Update source text                                   | Transliteration React Query cache invalidated                            |
| FE-ST21 | TranslateTab renders two-row layout                 | 1. Render TranslateTab                                  | Top row (image + source) and bottom row (translit + translation) present |
| FE-ST22 | TranslateTab shared zoom state                      | 1. Render TranslateTab 2. Zoom in                       | Both SectionImageDisplay and SourceTextPanel receive updated zoom        |
| FE-ST23 | TranslateTab integration — extraction flow          | 1. Render with section without AI text 2. Click Extract | Extraction triggered, status polls, panel updates                        |

---

## 13. Integration / E2E Test Cases

| TC-ID    | Scenario                                        | Steps                                                                                          | Expected Result                                              |
| -------- | ----------------------------------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| E2E-ST01 | Full extraction flow                            | 1. Login as editor 2. Open section without AI text 3. Click "Extract Text" 4. Wait             | Extraction completes, AI text shown with confidence badge    |
| E2E-ST02 | Full transliteration flow                       | 1. Section with AI text 2. Click "Generate with AI" 3. Wait                                    | Transliteration generated, pre-fills exact letter field      |
| E2E-ST03 | Extraction → Translation flow                   | 1. Extract text 2. Open translate tab 3. Check auto-translation                                | Auto-translation uses AI text                                |
| E2E-ST04 | Source text edit → transliteration invalidation | 1. Load section with cached transliteration 2. Edit source text 3. Check transliteration panel | Regenerate button appears, cache invalidated                 |
| E2E-ST05 | Batch extraction → status tracking              | 1. Click "Extract All" 2. Confirm 3. Watch progress                                            | Progress bar updates, section statuses change, summary shown |
| E2E-ST06 | Admin config → extraction behavior              | 1. Change threshold to 0.9 2. Extract section with confidence 0.85                             | Badge shows yellow (below new threshold)                     |
| E2E-ST07 | Transliteration → manual edit → submission      | 1. Generate transliteration 2. Edit result 3. Submit translation                               | TransliterationSource = "manual", translation submitted      |
| E2E-ST08 | Mobile responsive — extraction flow             | 1. View on mobile 2. Extract text                                                              | Stacked layout, extraction works, badge visible              |
| E2E-ST09 | Mobile responsive — transliteration             | 1. View on mobile 2. Generate transliteration                                                  | Stacked layout, transliteration panel functional             |
| E2E-ST10 | Concurrent extraction — semaphore               | 1. Trigger 6 extractions simultaneously                                                        | 5 run concurrently, 1 queued (semaphore limit)               |
| E2E-ST11 | Extraction failure → retry                      | 1. Mock API failure 2. Extract section 3. Retry                                                | First attempt fails, retry succeeds                          |
| E2E-ST12 | Full book extraction → translate → approve      | 1. Batch extract book 2. Translate sections 3. Approve                                         | All AI texts used, translations approved                     |

---

## 14. Edge Cases and Error Handling

| TC-ID     | Scenario                                | Steps                                                | Expected Result                                                                 |
| --------- | --------------------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------- |
| EDGE-ST01 | Section with no text in image           | 1. Blank image section 2. Extract                    | AI returns `[NO_TEXT]`, extraction marked FAILED, OCR retained                  |
| EDGE-ST02 | Section with mixed scripts              | 1. Image with Sinhala + English text 2. Extract      | All text extracted, confidence reflects quality                                 |
| EDGE-ST03 | OpenAI API key invalid                  | 1. Set invalid OPENAI_API_KEY 2. Trigger extraction  | Graceful error: "AI extraction unavailable", section retains OCR                |
| EDGE-ST04 | OpenAI API quota exceeded               | 1. Mock quota exceeded error 2. Trigger extraction   | Error logged, extraction FAILED, retry available                                |
| EDGE-ST05 | Redis unavailable for semaphore         | 1. Stop Redis 2. Trigger extraction                  | Extraction proceeds without concurrency limit (degraded mode) or graceful error |
| EDGE-ST06 | MongoDB unavailable for cache           | 1. Stop MongoDB 2. Trigger extraction                | Extraction proceeds, result not cached, or graceful error                       |
| EDGE-ST07 | Section with very long text             | 1. Section with 5000+ char text 2. Transliterate     | Transliteration handles long text, no truncation                                |
| EDGE-ST08 | Transliteration with unsupported script | 1. Request transliteration to unsupported script     | 400 Bad Request with clear error message                                        |
| EDGE-ST09 | Cost limit exactly equal to estimate    | 1. Set cost limit to $1.28 2. Book est. $1.28        | Batch allowed (equal, not exceeded)                                             |
| EDGE-ST10 | Batch extraction with 0 sections        | 1. Book with no sections 2. Trigger batch            | 422: "No sections to extract" or 0 totalSections                                |
| EDGE-ST11 | Extraction while book being deleted     | 1. Trigger extraction 2. Delete book simultaneously  | Graceful handling, no orphaned extraction records                               |
| EDGE-ST12 | Concurrent batch on same book           | 1. Trigger batch 2. Trigger another batch            | 409: batch already in progress                                                  |
| EDGE-ST13 | Network failure during batch            | 1. Trigger batch 2. Disconnect network               | In-progress sections complete (if possible), remaining fail gracefully          |
| EDGE-ST14 | Source text edit with only OCR text     | 1. Section with no AI text 2. Edit OCR text          | OCR text updated, no transliteration invalidation (nothing to invalidate)       |
| EDGE-ST15 | Transliterate before extraction         | 1. Click "Transliterate" on section without any text | 422 error, "Run AI extraction first" message shown                              |

---

## 15. Accessibility Test Cases

| TC-ID     | Scenario                                  | Steps                                          | Expected Result                                                   |
| --------- | ----------------------------------------- | ---------------------------------------------- | ----------------------------------------------------------------- |
| A11Y-ST01 | Source text panel ARIA                    | 1. Inspect source text panel                   | `role="region"`, `aria-label="Source text panel"`                 |
| A11Y-ST02 | Extraction status live region             | 1. Trigger extraction 2. Check DOM             | `aria-live="polite"` region announces "AI extraction in progress" |
| A11Y-ST03 | Confidence badge aria-label               | 1. Inspect badge                               | `aria-label="Confidence: 94 percent, high quality"`               |
| A11Y-ST04 | Extract button keyboard accessible        | 1. Tab to Extract button 2. Press Enter        | Extraction triggered                                              |
| A11Y-ST05 | Transliterate button keyboard accessible  | 1. Tab to button 2. Press Enter                | Transliteration triggered                                         |
| A11Y-ST06 | Source text textarea labeled              | 1. Inspect textarea                            | `<label>` or `aria-label="Source text"`                           |
| A11Y-ST07 | Transliteration input labeled             | 1. Inspect input                               | `<label>` or `aria-label="Exact letter transliteration"`          |
| A11Y-ST08 | Zoom controls ARIA                        | 1. Inspect zoom controls                       | `role="group"`, `aria-label="Zoom controls"`                      |
| A11Y-ST09 | Screen reader — extraction complete       | 1. Complete extraction with screen reader      | "AI extraction complete. Confidence: 94 percent." announced       |
| A11Y-ST10 | Screen reader — extraction failed         | 1. Failed extraction with screen reader        | "AI extraction failed. Using OCR text." announced                 |
| A11Y-ST11 | Screen reader — transliteration generated | 1. Generate transliteration with screen reader | "AI transliteration generated" announced                          |
| A11Y-ST12 | Color contrast on badges                  | 1. Check badge text contrast                   | WCAG AA compliant (4.5:1 for badge text)                          |

---

## 16. Test Data Requirements (Detailed)

### Sample Images

| Image                      | Content                         | Purpose                  |
| -------------------------- | ------------------------------- | ------------------------ |
| `sinhala_paragraph.png`    | Clear Sinhala paragraph text    | Happy path extraction    |
| `tamil_paragraph.png`      | Clear Tamil paragraph text      | Script-specific accuracy |
| `devanagari_paragraph.png` | Clear Devanagari paragraph text | Transliteration source   |
| `blank_page.png`           | No text content                 | Edge case: no text       |
| `mixed_script.png`         | Sinhala + English text          | Mixed script handling    |
| `noisy_image.png`          | Low-quality scan with artifacts | Confidence scoring       |
| `large_image.png`          | High-resolution (>20MB) section | Image resize handling    |
| `complex_ligatures.png`    | Indic conjunct characters       | Ligature accuracy        |

### Sample Texts

| Text                                           | Script             | Purpose                         |
| ---------------------------------------------- | ------------------ | ------------------------------- |
| `මාතාව සියලු දේවතාවුන්ගේ ගුණ ගීතය මෙසේ දැක්වේ` | Sinhala            | Source text for transliteration |
| `माता सर्व देवताओं की श्रेष्ठता`               | Devanagari         | Transliteration source          |
| `அனைத்து தெய்வங்களின் புகழ் பாடல்`             | Tamil              | Transliteration target          |
| `මාතා → माता, සියලු → सर्व`                    | Sinhala→Devanagari | Expected transliteration pairs  |

---

## 17. Test Execution Summary

| Category                             | Test Count | Status      |
| ------------------------------------ | ---------- | ----------- |
| US-ST-1: AI Text Extraction (single) | 39         | Pending     |
| US-ST-2: AI Transliteration          | 27         | Pending     |
| US-ST-3: Replace OCR with AI Text    | 12         | Pending     |
| US-ST-4: Extraction Status Tracking  | 18         | Pending     |
| US-ST-5: Batch Auto-Extract          | 23         | Pending     |
| US-ST-6: Admin Configuration         | 21         | Pending     |
| Bidirectional Sync                   | 12         | Pending     |
| Layout & Responsive Design           | 18         | Pending     |
| Backend API Tests                    | 31         | Pending     |
| Frontend Component Tests             | 23         | Pending     |
| Integration / E2E Tests              | 12         | Pending     |
| Edge Cases & Error Handling          | 15         | Pending     |
| Accessibility Tests                  | 12         | Pending     |
| **Total**                            | **263**    | **Pending** |

---

## 18. Related Files

- `specs/business-analysis/20260706-1300-source-text-modifications.md` — User stories (US-ST-1 through US-ST-6)
- `specs/architecture/20260706-1300-source-text-modifications.md` — API contracts, backend architecture
- `specs/ux/20260706-1300-source-text-modifications.md` — UX interactions, wireframes, state diagrams
- `specs/ux/ui-design.md` — Updated UI design (Translation Interface section)
- `specs/qa/test-plan.md` — Updated master test plan
