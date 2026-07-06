# Source Text Modifications — Technical Architecture

**Date:** 2026-07-06 13:00
**Author:** Architecture Agent
**Epic Reference:** Epic 1 — Book Upload & Processing, Epic 4 — Translation
**Related BA:** `specs/business-analysis/20260706-1300-source-text-modifications.md`

---

## 1. Scope

Introduce AI-powered text extraction and bidirectional transliteration for Indic scripts. Covers 6 user stories: US-ST-1 through US-ST-6. Replaces Tesseract OCR as the primary source text with GPT-4o Vision, and adds script-to-script transliteration between Indic languages.

---

## 2. Key Technical Decisions

| Decision | Choice | Rationale |
| --- | --- | --- |
| AI provider (text extraction) | **OpenAI GPT-4o Vision API** | Best-in-class OCR for Indic scripts; handles complex ligatures/conjuncts that Tesseract fails on; API is simple (base64 image → text); cost is ~$0.005 per section image |
| AI provider (transliteration) | **OpenAI GPT-4o (text-only)** | Same model family, no separate integration needed; prompt-based transliteration is accurate for Indic scripts; ~$0.001 per call |
| Extraction trigger | **On demand (editor-initiated)** | Editors control when to extract; avoids wasting API calls on unused sections; batch mode available for bulk extraction |
| Transliteration trigger | **On demand (translator-initiated)** | Translator clicks "Transliterate" per section; avoids generating transliterations for sections that may never be translated |
| Failure fallback | **Keep OCR text** | If AI extraction fails, `originalText` remains the source; translators are never blocked; error logged in `AITextExtraction.rawResponse` |
| Caching | **MongoDB collections** | `AITextExtraction` (one per section, unique) and `Transliteration` (one per section+targetScript, unique); cache-first lookup before API call |
| Concurrency control | **Redis semaphore** | Max 5 concurrent AI API calls; prevents rate limiting and cost spikes |
| Cost control | **Per-book cost limit** | Configurable in admin settings; estimated cost shown before batch execution; enforced server-side |

---

## 3. AI Provider Integration

### 3.1 Text Extraction — GPT-4o Vision

**Endpoint:** `POST https://api.openai.com/v1/chat/completions`
**Model:** `gpt-4o`
**Input:** Base64-encoded section image (cropped PNG from MinIO)
**Output:** Extracted text + confidence score

**Prompt template:**

```
You are an expert OCR system for Indic scripts. Extract ALL text from this image.
Return ONLY the extracted text, preserving line breaks. Do not add any explanation.
If the image contains no text, return exactly: [NO_TEXT]
```

**Confidence extraction:** Use a second GPT-4o call (text-only) to score the extraction:

```
Rate the quality of this OCR extraction on a scale of 0.0 to 1.0.
Consider: character accuracy, completeness, script correctness.
Return ONLY a number between 0.0 and 1.0.

Image text: {extracted_text}
```

**Cost:** ~$0.005 per section (Vision input ~1000 tokens + text output ~500 tokens)

### 3.2 Transliteration — GPT-4o Text

**Endpoint:** `POST https://api.openai.com/v1/chat/completions`
**Model:** `gpt-4o`
**Input:** Source text string
**Output:** Transliterated text in target script

**Prompt template:**

```
Transliterate the following {source_script} text into {target_script} script.
Perform letter-for-letter script conversion, NOT semantic translation.
Preserve word boundaries. Return ONLY the transliterated text.

Text: {source_text}
```

**Cost:** ~$0.001 per call (text-only, ~200 tokens input + ~200 tokens output)

---

## 4. API Contract

### 4.1 POST /api/sections/{sectionId}/extract

Triggers AI text extraction for a single section.

**Response (202):**

```json
{
  "taskId": "celery-task-id",
  "sectionId": "507f1f77bcf86cd799439015",
  "status": "queued"
}
```

**Response (409):** Already extracted (idempotent — returns existing result)

```json
{
  "sectionId": "507f1f77bcf86cd799439015",
  "status": "completed",
  "extractedText": "माता सर्व देवताओं की...",
  "confidence": 0.94
}
```

**Response (422):** Section has no cropped image

```json
{
  "detail": "Section has no cropped image. Crop sections first."
}
```

**Pydantic Schema:**

```python
class ExtractResponse(BaseModel):
    taskId: str | None = None
    sectionId: str
    status: str  # "queued" | "completed" | "failed"
    extractedText: str | None = None
    confidence: float | None = None
```

### 4.2 POST /api/books/{bookId}/pages/{pageNum}/extract

Batch extracts all sections on a page.

**Response (202):**

```json
{
  "taskId": "celery-batch-task-id",
  "bookId": "507f1f77bcf86cd799439010",
  "pageNum": 3,
  "totalSections": 5,
  "estimatedCost": 0.025,
  "status": "queued"
}
```

### 4.3 POST /api/books/{bookId}/extract

Batch extracts ALL sections in a book (US-ST-5).

**Response (202):**

```json
{
  "taskId": "celery-batch-task-id",
  "bookId": "507f1f77bcf86cd799439010",
  "totalSections": 156,
  "estimatedCost": 1.28,
  "status": "queued"
}
```

**Response (409):** Batch already in progress

```json
{
  "bookId": "507f1f77bcf86cd799439010",
  "status": "in_progress",
  "completed": 34,
  "total": 156,
  "failed": 0
}
```

### 4.4 GET /api/sections/{sectionId}/extraction

Fetches the extraction result for a section.

**Response (200):**

```json
{
  "sectionId": "507f1f77bcf86cd799439015",
  "extractedText": "माता सर्व देवताओं की...",
  "confidence": 0.94,
  "model": "gpt-4o",
  "processingTimeMs": 2340,
  "createdAt": "2026-07-06T13:00:00Z"
}
```

**Response (404):** Not yet extracted

```json
{
  "detail": "No extraction found for this section"
}
```

### 4.5 POST /api/sections/{sectionId}/transliterate

Generates a transliteration for a section's source text.

**Query Parameters:**

| Param | Type | Required | Notes |
| --- | --- | --- | --- |
| `targetScript` | string | Yes | Target script name (e.g. "sinhala", "devanagari", "tamil") |

**Response (200):** Cached result

```json
{
  "sectionId": "507f1f77bcf86cd799439015",
  "sourceText": "माता सर्व देवताओं की",
  "transliteratedText": "මාතා සර්ව දේවතාවුන්ගේ",
  "sourceScript": "devanagari",
  "targetScript": "sinhala",
  "confidence": 0.91,
  "model": "gpt-4o",
  "cached": true
}
```

**Response (202):** New computation queued

```json
{
  "sectionId": "507f1f77bcf86cd799439015",
  "status": "queued",
  "taskId": "celery-task-id"
}
```

**Response (422):** No source text available

```json
{
  "detail": "No source text available. Run AI extraction first."
}
```

### 4.6 GET /api/sections/{sectionId}/transliterations

Fetches all cached transliterations for a section.

**Response (200):**

```json
{
  "sectionId": "507f1f77bcf86cd799439015",
  "transliterations": [
    {
      "targetScript": "sinhala",
      "transliteratedText": "මාතා සර්ව දේවතාවුන්ගේ",
      "confidence": 0.91,
      "model": "gpt-4o",
      "createdAt": "2026-07-06T13:00:00Z"
    }
  ]
}
```

### 4.7 PUT /api/sections/{sectionId}/source-text

Updates the source text (AI-extracted or OCR) and triggers re-transliteration (US-ST-3 bidirectional sync).

**Request Body:**

```json
{
  "text": "माता सर्व देवताओं की श्रेष्ठता",
  "source": "ai"
}
```

**Response (200):**

```json
{
  "sectionId": "507f1f77bcf86cd799439015",
  "updatedText": "माता सर्व देवताओं की श्रेष्ठता",
  "source": "ai"
}
```

**Behavior:**
- If `source` is `"ai"`, updates `Section.aiExtractedText`
- If `source` is `"ocr"`, updates `Section.originalText`
- Invalidates any cached transliterations for this section (they become stale)

### 4.8 GET /api/books/{bookId}/extraction/status

Returns batch extraction progress (US-ST-5).

**Response (200):**

```json
{
  "bookId": "507f1f77bcf86cd799439010",
  "totalSections": 156,
  "extracted": 120,
  "pending": 34,
  "failed": 2,
  "inProgress": false
}
```

### 4.9 GET /api/admin/settings/extraction

Fetches AI extraction configuration (US-ST-6).

**Response (200):**

```json
{
  "model": "gpt-4o",
  "confidenceThreshold": 0.7,
  "maxConcurrent": 5,
  "costLimitPerBook": 5.0,
  "enabled": true
}
```

### 4.10 PUT /api/admin/settings/extraction

Updates AI extraction configuration.

**Request Body:**

```json
{
  "model": "gpt-4o",
  "confidenceThreshold": 0.8,
  "maxConcurrent": 3,
  "costLimitPerBook": 10.0
}
```

---

## 5. Backend Architecture

### 5.1 New Service Module — `app/services/ai_text.py`

```
app/services/ai_text.py
├── extract_text(image_data: bytes) → AITextResult
│   # Sends cropped image to GPT-4o Vision, returns extracted text + confidence
├── transliterate_text(source_text: str, source_script: str, target_script: str) → TransliterationResult
│   # Sends text to GPT-4o for script conversion
├── estimate_extraction_cost(section_count: int) → float
│   # Returns estimated USD cost for batch extraction
└── get_model_config() → dict
    # Reads from SystemConfig collection, falls back to defaults
```

**`AITextResult` dataclass:**

```python
@dataclass
class AITextResult:
    text: str
    confidence: float
    model: str
    processing_time_ms: int
    raw_response: dict | None = None
```

**`TransliterationResult` dataclass:**

```python
@dataclass
class TransliterationResult:
    transliterated_text: str
    source_script: str
    target_script: str
    confidence: float
    model: str
    raw_response: dict | None = None
```

### 5.2 Updated Service Module — `app/services/translate.py`

The existing `auto_translate` function is updated to prefer AI-extracted text:

```python
async def auto_translate(text: str, source_lang: str = "auto", target_lang: str = "en") -> str | None:
    # unchanged — receives the best available text from the caller
```

The Celery task that calls `auto_translate` checks `aiExtractedText` first, falls back to `originalText`.

### 5.3 New Celery Tasks

**`app/tasks/extract_section_text.py`**

```python
@celery_app.task(bind=True, max_retries=3)
def extract_section_text(self, section_id: str):
    # 1. Fetch section from MongoDB
    # 2. Download cropped image from MinIO (section.croppedImageKey)
    # 3. Acquire Redis semaphore (max 5 concurrent)
    # 4. Call ai_text.extract_text(image_data)
    # 5. Save to AITextExtraction collection
    # 6. Update Section.aiExtractedText
    # 7. Release semaphore
    # 8. On failure: log error, set extraction status to FAILED
```

**`app/tasks/batch_extract_book.py`**

```python
@celery_app.task(bind=True)
def batch_extract_book(self, book_id: str):
    # 1. Count total unextracted sections for the book
    # 2. Estimate cost via ai_text.estimate_extraction_cost()
    # 3. Check cost limit from SystemConfig
    # 4. Create chain of extract_section_text tasks (max 5 concurrent via semaphore)
    # 5. Track progress in Redis: {bookId}:extraction:progress
    # 6. On completion: update progress, log summary
```

**`app/tasks/transliterate_section.py`**

```python
@celery_app.task(bind=True, max_retries=3)
def transliterate_section(self, section_id: str, target_script: str):
    # 1. Check cache: Transliteration collection for section+targetScript
    # 2. If cached, return cached result
    # 3. Fetch section's aiExtractedText (or originalText as fallback)
    # 4. Determine source_script from book's sourceLanguage
    # 5. Call ai_text.transliterate_text()
    # 6. Save to Transliteration collection
    # 7. Return result
```

### 5.4 Updated Celery Task — `app/tasks/crop_sections.py`

After cropping completes, optionally trigger extraction (configurable):

```python
# At end of _crop_sections(), after all sections are cropped:
if settings.auto_extract_after_crop:
    for sec in sections:
        extract_section_text.delay(str(sec["_id"]))
```

### 5.5 New API Router — `app/api/extraction.py`

Routes for extraction and transliteration endpoints:

```python
router = APIRouter(prefix="/api", tags=["extraction"])

@router.post("/sections/{section_id}/extract", status_code=202)
@router.post("/books/{book_id}/pages/{pageNum}/extract", status_code=202)
@router.post("/books/{book_id}/extract", status_code=202)
@router.get("/sections/{section_id}/extraction")
@router.post("/sections/{section_id}/transliterate", status_code=200)
@router.get("/sections/{section_id}/transliterations")
@router.put("/sections/{section_id}/source-text")
@router.get("/books/{book_id}/extraction/status")
```

### 5.6 New API Router — `app/api/admin_settings.py`

Routes for admin configuration (US-ST-6):

```python
router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/settings/extraction")
@router.put("/settings/extraction")
@router.get("/extraction/audit")
```

### 5.7 Updated Schema — `app/schemas/section.py`

```python
class SectionResponse(BaseModel):
    id: str
    page: PageRef
    sectionOrder: int
    type: str = "PARAGRAPH"
    x: float = 0
    y: float = 0
    width: float = 100
    height: float = 50
    originalText: str | None = None
    aiExtractedText: str | None = None  # NEW
    croppedImageKey: str | None = None
    extractionStatus: str | None = None  # NEW: "extracted" | "pending" | "failed"
    createdAt: datetime | None = None


class NextSectionResponse(BaseModel):
    id: str
    type: str
    originalText: str | None = None
    aiExtractedText: str | None = None  # NEW
    autoTranslatedText: str | None = None
    pageNumber: int
    bookTitle: str
    book: BookRef
    croppedImageUrl: str | None = None
```

### 5.8 New Schemas

**`app/schemas/extraction.py`:**

```python
class ExtractResponse(BaseModel):
    taskId: str | None = None
    sectionId: str
    status: str
    extractedText: str | None = None
    confidence: float | None = None

class ExtractionResultResponse(BaseModel):
    sectionId: str
    extractedText: str
    confidence: float
    model: str
    processingTimeMs: int
    createdAt: datetime

class BatchExtractResponse(BaseModel):
    taskId: str
    bookId: str
    totalSections: int
    estimatedCost: float
    status: str

class ExtractionStatusResponse(BaseModel):
    bookId: str
    totalSections: int
    extracted: int
    pending: int
    failed: int
    inProgress: bool

class TransliterateResponse(BaseModel):
    sectionId: str
    sourceText: str
    transliteratedText: str
    sourceScript: str
    targetScript: str
    confidence: float
    model: str
    cached: bool

class SourceTextUpdate(BaseModel):
    text: str
    source: str  # "ai" | "ocr"
```

**`app/schemas/admin.py`:**

```python
class ExtractionConfigResponse(BaseModel):
    model: str
    confidenceThreshold: float
    maxConcurrent: int
    costLimitPerBook: float
    enabled: bool

class ExtractionConfigUpdate(BaseModel):
    model: str | None = None
    confidenceThreshold: float | None = None
    maxConcurrent: int | None = None
    costLimitPerBook: float | None = None
    enabled: bool | None = None
```

---

## 6. Data Flow Diagrams

### 6.1 Single Section Extraction

```
┌──────────────┐  POST /api/sections/{id}/extract  ┌──────────┐
│  Editor      │ ─────────────────────────────────→  │ FastAPI  │
│  clicks      │ ←─────────────────────────────────  │          │
│  "Extract"   │     { taskId, status: "queued" }    └──────────┘
└──────────────┘                                         │
        │                                                 │
        │  Celery: extract_section_text(section_id)       │
        │ ┌───────────────────────────────────────────┐   │
        │ │ 1. Fetch section from MongoDB             │   │
        │ │ 2. Download cropped image from MinIO      │   │
        │ │ 3. Acquire Redis semaphore (max 5)        │   │
        │ │ 4. POST to OpenAI GPT-4o Vision API       │   │
        │ │ 5. Score confidence via GPT-4o text call   │   │
        │ │ 6. Save AITextExtraction document          │   │
        │ │ 7. Update Section.aiExtractedText          │   │
        │ │ 8. Release semaphore                       │   │
        │ └───────────────────────────────────────────┘   │
        │                                                 │
        │  Frontend polls GET /api/sections/{id}/extraction│
        │  → Shows confidence badge (green/yellow/red)     │
```

### 6.2 Batch Book Extraction

```
┌──────────────┐  POST /api/books/{id}/extract  ┌──────────┐
│  Editor      │ ──────────────────────────────→  │ FastAPI  │
│  clicks      │ ←──────────────────────────────  │          │
│  "Extract All"│   { taskId, estimatedCost }     └──────────┘
└──────────────┘                                       │
        │                                               │
        │  Celery: batch_extract_book(book_id)          │
        │ ┌─────────────────────────────────────────┐   │
        │ │ 1. Count unextracted sections            │   │
        │ │ 2. Estimate cost, check limit            │   │
        │ │ 3. Create task chain (5 concurrent)      │   │
        │ │ 4. Progress → Redis {bookId}:extraction  │   │
        │ └─────────────────────────────────────────┘   │
        │                                               │
        │  Frontend polls GET /api/books/{id}/extraction/status
        │  → Progress bar: "34/156 sections..."          │
```

### 6.3 Transliteration Flow

```
┌──────────────┐  POST /api/sections/{id}/transliterate  ┌──────────┐
│  Translator  │ ───────────────────────────────────────→  │ FastAPI  │
│  clicks      │ ←───────────────────────────────────────  │          │
│  "Transliterate"│   { transliteratedText, cached }       └──────────┘
└──────────────┘                                              │
        │                                                      │
        │  Check cache: Transliteration collection             │
        │  If cached → return immediately                      │
        │  If not → Celery: transliterate_section              │
        │ ┌────────────────────────────────────────────┐      │
        │ │ 1. Fetch section.aiExtractedText           │      │
        │ │ 2. POST to OpenAI GPT-4o (text-only)      │      │
        │ │ 3. Save Transliteration document            │      │
        │ │ 4. Return result                            │      │
        │ └────────────────────────────────────────────┘      │
        │                                                      │
        │  Frontend pre-fills exactLetterTranslation field     │
        │  Translator can edit before submitting               │
```

### 6.4 Bidirectional Source Text Sync

```
┌──────────────┐  PUT /api/sections/{id}/source-text  ┌──────────┐
│  User        │ ────────────────────────────────────→  │ FastAPI  │
│  edits       │ ←────────────────────────────────────  │          │
│  source text │     { updatedText, source }            └──────────┘
└──────────────┘                                           │
        │                                                   │
        │  1. Update Section.aiExtractedText or originalText│
        │  2. Invalidate cached Transliterations            │
        │  3. Return updated text                           │
        │                                                   │
        │  Frontend:                                         │
        │  - If source text changed → show "Transliterate"  │
        │    button again (cache invalidated)                │
        │  - Auto-translation re-triggered on next submit   │
```

---

## 7. Frontend Component Architecture

### 7.1 Updated Component Tree — TranslateTab

```
TranslateTab
├── TranslateHeader (book title, page indicator, actions)
├── Body (2-column layout)
│   ├── LeftColumn
│   │   ├── SectionImageDisplay
│   │   │   ├── ZoomableImage (shared zoom state)
│   │   │   └── ZoomControls (zoom in/out/reset)
│   │   ├── SourceTextPanel (UPDATED)
│   │   │   ├── TextToggle ("AI Extracted" | "OCR")
│   │   │   ├── OriginalText (read-only, labeled)
│   │   │   ├── AIExtractedText (read-only, labeled)
│   │   │   ├── ConfidenceBadge (green ≥ 0.9, yellow ≥ 0.7, red < 0.7)
│   │   │   ├── ExtractButton (editors only, if not yet extracted)
│   │   │   └── EditLink (editors → /books/{id}/pages/{num})
│   │   └── MyPreviousSubmission (if exists)
│   └── RightColumn
│       ├── TranslationEditor
│       │   ├── TranslatedTextArea
│       │   ├── TransliterateButton (NEW — if aiExtractedText exists)
│       │   ├── ExactLetterInput (pre-filled from transliteration)
│       │   ├── DraftSaveIndicator
│       │   └── SubmitButton
│       └── ApprovedTranslation (if exists)
└── PageContextNav
```

### 7.2 Shared Zoom State

The image and source text share a single zoom level. Implemented via `useState` lifted to `TranslateTab`:

```typescript
const [zoom, setZoom] = useState(100)

// Both SectionImageDisplay and SourceTextPanel receive zoom as prop
<SectionImageDisplay zoom={zoom} onZoomChange={setZoom} />
<SourceTextPanel zoom={zoom} originalText={...} aiText={...} />
```

The source text panel scales its font size proportionally to the image zoom, keeping the visual relationship consistent.

### 7.3 Updated SourceTextPanel

```typescript
interface SourceTextPanelProps {
  originalText: string | null
  aiExtractedText: string | null
  extractionStatus: "extracted" | "pending" | "failed" | null
  confidence: number | null
  isEditor?: boolean
  bookId?: string
  pageNumber?: number
  zoom: number
  onExtract?: () => void  // editor-only
}
```

**Behavior:**
- Default view: shows AI text if available, otherwise OCR
- Toggle switches between AI and OCR views
- "Extract Text" button visible to editors when no AI extraction exists
- Confidence badge displayed next to the text label
- Font size scales with zoom: `fontSize: 14 * (zoom / 100)`

### 7.4 Transliteration Integration

The `ExactLetterInput` field in `TranslationEditor` is updated:

```typescript
interface TranslationEditorProps {
  // ... existing props
  aiExtractedText: string | null
  transliteration: TransliterationResult | null
  onTransliterate: (targetScript: string) => void
  isTransliterating: boolean
}
```

**Behavior:**
- "Transliterate" button appears when `aiExtractedText` exists and `exactLetterTranslation` is empty
- Clicking triggers `POST /api/sections/{id}/transliterate?targetScript={lang}`
- While loading, button shows spinner
- Result pre-fills `exactLetterTranslation` field
- Translator can edit the pre-filled value
- If transliteration fails, show "Transliteration unavailable — enter manually"

---

## 8. Caching Strategy

### 8.1 MongoDB Collections

| Collection | Key | TTL | Notes |
| --- | --- | --- | --- |
| `ai_text_extractions` | `{ sectionId: 1 }` unique | None | One extraction per section; idempotent (re-run replaces) |
| `transliterations` | `{ translationId: 1 }` unique | None | One transliteration per translation document |
| `system_config` | `{ key: 1 }` unique | None | Key-value config store |

### 8.2 Redis Keys

| Key Pattern | TTL | Purpose |
| --- | --- | --- |
| `{bookId}:extraction:progress` | 1 hour | Batch extraction progress (total, completed, failed) |
| `extraction:semaphore` | None | Redis semaphore for max 5 concurrent AI calls |
| `stats:book:{bookId}` | 30s | Existing stats cache (now includes extractionStats) |

### 8.3 Frontend Cache (React Query)

| Query Key | staleTime | Notes |
| --- | --- | --- |
| `['extraction', sectionId]` | 0 | Always refetch (extraction may complete in background) |
| `['transliterations', sectionId]` | 60s | Cache transliterations for 1 minute |
| `['extractionStatus', bookId]` | 5s | Poll batch progress frequently during extraction |

---

## 9. Error Handling & Fallback

### 9.1 AI Extraction Failure

| Error | Handling |
| --- | --- |
| OpenAI API timeout (30s) | Retry up to 3 times with exponential backoff |
| OpenAI API rate limit (429) | Wait and retry; semaphore prevents this from happening |
| OpenAI API error (500, 503) | Log error, mark extraction as FAILED, keep OCR text |
| Invalid response (no text extracted) | Save empty text, confidence = 0.0, mark as FAILED |
| Image too large (>20MB) | Resize to fit within limit before sending |
| Network error | Retry up to 3 times |

**Fallback behavior:** Every extraction failure is non-fatal. The section retains its `originalText` (OCR). The UI shows "Extraction failed — using OCR text" with a retry button.

### 9.2 Transliteration Failure

| Error | Handling |
| --- | --- |
| No source text available | Return 422 with message "Run AI extraction first" |
| OpenAI API error | Return error message, leave exactLetterTranslation empty |
| Invalid source script detection | Default to book's `sourceLanguage` |

**Fallback behavior:** Translator sees "Transliteration unavailable — enter manually" and can type the transliteration by hand.

### 9.3 Batch Extraction Failure

- Individual section failures do NOT stop the batch
- Failed sections are logged in `AITextExtraction.rawResponse`
- Batch summary shows: "154 extracted, 2 failed"
- "Retry Failed" button re-runs extraction only for failed sections

---

## 10. Cost Considerations

### 10.1 Per-Call Costs (OpenAI GPT-4o)

| Operation | Input Tokens | Output Tokens | Cost (USD) |
| --- | --- | --- | --- |
| Text extraction (Vision) | ~1000 | ~500 | ~$0.005 |
| Confidence scoring | ~200 | ~10 | ~$0.001 |
| Transliteration | ~200 | ~200 | ~$0.001 |
| **Total per section** | | | **~$0.007** |

### 10.2 Batch Estimates

| Book Size | Sections | Extraction Cost | Transliteration Cost | Total |
| --- | --- | --- | --- | --- |
| Small (50 pages) | ~200 | $1.40 | $0.20 | $1.60 |
| Medium (200 pages) | ~800 | $5.60 | $0.80 | $6.40 |
| Large (500 pages) | ~2000 | $14.00 | $2.00 | $16.00 |

### 10.3 Cost Control Mechanisms

1. **Per-book cost limit** — configurable in admin settings (default $5.00)
2. **Pre-batch estimation** — shown to editor before confirming batch extraction
3. **Cost audit log** — `AITextExtraction.processingTimeMs` and model name tracked for cost analysis
4. **Semaphore** — max 5 concurrent calls prevents burst costs
5. **Caching** — cached results are free (no API call on re-run)

---

## 11. New Backend Files

| File | Purpose |
| --- | --- |
| `app/services/ai_text.py` | OpenAI Vision + GPT-4o integration for extraction and transliteration |
| `app/tasks/extract_section_text.py` | Celery task for single-section extraction |
| `app/tasks/batch_extract_book.py` | Celery task for batch extraction with progress tracking |
| `app/tasks/transliterate_section.py` | Celery task for transliteration |
| `app/api/extraction.py` | API routes for extraction and transliteration endpoints |
| `app/api/admin_settings.py` | API routes for admin configuration |
| `app/schemas/extraction.py` | Pydantic models for extraction/transliteration requests/responses |
| `app/schemas/admin.py` | Pydantic models for admin config |

### Updated Files

| File | Changes |
| --- | --- |
| `app/schemas/section.py` | Add `aiExtractedText`, `extractionStatus` to response models |
| `app/tasks/crop_sections.py` | Optionally trigger extraction after crop |
| `app/db/indexes.py` | Add indexes for `ai_text_extractions`, `transliterations`, `system_config` |
| `app/main.py` | Register new routers |

---

## 12. New Frontend Files

| File | Purpose |
| --- | --- |
| `app/translate/components/ExtractionStatusBadge.tsx` | Confidence badge (green/yellow/red) |
| `app/translate/components/TransliterateButton.tsx` | Transliterate action with loading state |
| `lib/api/extraction.ts` | API client for extraction/transliteration endpoints |
| `hooks/useExtraction.ts` | Hook for polling extraction status |

### Updated Files

| File | Changes |
| --- | --- |
| `app/translate/TranslateTab.tsx` | Shared zoom state, extraction/transliteration integration |
| `app/translate/components/SourceTextPanel.tsx` | AI/OCR toggle, confidence badge, extract button |

---

## 13. Database Indexes

```python
# New indexes in db/indexes.py
await db.ai_text_extractions.create_index("sectionId", unique=True)
await db.transliterations.create_index("translationId", unique=True)
await db.system_config.create_index("key", unique=True)

# Updated stats aggregation includes extraction counts
# No new indexes needed — existing section/page indexes suffice
```

---

## 14. Implementation Order

| Phase | Stories | Backend | Frontend | Effort |
| --- | --- | --- | --- | --- |
| **Phase 1** | US-ST-1 | `ai_text.py`, `extract_section_text.py`, `extraction.py`, `extraction.py` schema | `ExtractionStatusBadge.tsx`, update `SourceTextPanel.tsx` | 2 days |
| **Phase 2** | US-ST-3 | Update `SectionResponse` schema, update `auto_translate` task | Update `TranslateTab.tsx` (AI/OCR toggle) | 0.5 days |
| **Phase 3** | US-ST-2 | `transliterate_section.py`, update `extraction.py` router | `TransliterateButton.tsx`, update `TranslationEditor` | 1 day |
| **Phase 4** | US-ST-4 | Update stats aggregation, `extractionStatus` field | Update book console with extraction overlay | 1 day |
| **Phase 5** | US-ST-5 | `batch_extract_book.py`, Redis progress tracking | Batch progress UI, "Extract All" button | 1.5 days |
| **Phase 6** | US-ST-6 | `admin_settings.py`, `system_config` collection | Admin settings page | 1 day |

**Total estimated effort: ~7 days**

---

## 15. Testing Strategy

### Backend Tests

| Test File | Covers |
| --- | --- |
| `tests/test_ai_text.py` | `extract_text()`, `transliterate_text()`, confidence scoring, error handling |
| `tests/test_extract_section.py` | Single extraction endpoint, idempotency, semaphore, retry logic |
| `tests/test_batch_extract.py` | Batch extraction, progress tracking, cost limit enforcement |
| `tests/test_transliterate.py` | Transliteration endpoint, cache hit/miss, fallback |
| `tests/test_admin_settings.py` | Config CRUD, default values |

### Frontend Tests

| Test File | Covers |
| --- | ---|
| `__tests__/SourceTextPanel.test.tsx` | AI/OCR toggle, confidence badge, extract button visibility |
| `__tests__/TransliterateButton.test.tsx` | Loading state, pre-fill, error state |
| `__tests__/TranslateTab.test.tsx` | Shared zoom, extraction integration |

---

## 16. Migration / Rollout Notes

- **No migration needed**: All new collections are additive; existing `Section` fields (`originalText`, `croppedImageKey`) remain unchanged.
- **New MongoDB collections**: `ai_text_extractions`, `transliterations`, `system_config` — created automatically on first insert or via `db/indexes.py`.
- **Environment variable**: Add `OPENAI_API_KEY` to `.env` and `.env.example`.
- **Feature flag**: Consider `ENABLE_AI_EXTRACTION` env var to gate the feature during rollout.
- **Backward compatibility**: All existing endpoints and behavior preserved. New fields are optional in responses.
