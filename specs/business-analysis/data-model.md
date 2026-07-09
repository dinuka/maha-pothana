# Maha Pothana — Data Model

## Database: MongoDB

MongoDB is used instead of PostgreSQL. Relationships use document references (ObjectId) rather than foreign keys. Embedded documents are used where appropriate for read performance.

## Entities

### User

| Field     | Type      | Notes                               |
| --------- | --------- | ----------------------------------- |
| \_id      | ObjectId  | PK                                  |
| googleId  | string    | Google SSO subject ID, unique index |
| email     | string    | Unique index                        |
| name      | string    |                                     |
| avatarUrl | string    | Google profile photo                |
| roles     | string[]  | SUPER_ADMIN, EDITOR, TRANSLATOR     |
| createdAt | timestamp |                                     |
| updatedAt | timestamp |                                     |

### Book

| Field              | Type      | Notes                                             |
| ------------------ | --------- | ------------------------------------------------- |
| \_id               | ObjectId  | PK                                                |
| title              | string    |                                                   |
| author             | string    |                                                   |
| sourceLanguage     | string    | Original book language                            |
| translateLanguages | string[]  | Target languages for translation                  |
| description        | text      |                                                   |
| fileKey            | string    | S3 key for original PDF                           |
| fileHash           | string    | SHA256 for duplicate detection                    |
| thumbnailKey       | string    | S3 key for thumbnail                              |
| translatorCount    | int       | Default 1, configurable by editor                 |
| ownerId            | ObjectId  | Ref → User                                        |
| status             | string    | UPLOADING, PROCESSING, READY, BUILDING, COMPLETED |
| createdAt          | timestamp |                                                   |
| updatedAt          | timestamp |                                                   |

Indexes: `{ ownerId: 1 }`, `{ fileHash: 1 }`, `{ title: "text", author: "text" }`

### BookEditor

| Field     | Type      | Notes      |
| --------- | --------- | ---------- |
| \_id      | ObjectId  | PK         |
| bookId    | ObjectId  | Ref → Book |
| userId    | ObjectId  | Ref → User |
| createdAt | timestamp |            |

Index: `{ bookId: 1, userId: 1 }` unique

### Page

| Field              | Type      | Notes                                                     |
| ------------------ | --------- | --------------------------------------------------------- |
| \_id               | ObjectId  | PK                                                        |
| bookId             | ObjectId  | Ref → Book                                                |
| pageNumber         | int       | Sequential (1..N)                                         |
| originalPageNumber | string    | Original page label (e.g. "i", "(II)", "1", "1b")         |
| imageKey           | string    | S3 key for page image                                     |
| thumbnailKey       | string    | S3 key for page thumbnail (generated during split)        |
| width              | int       | Image width in px                                         |
| height             | int       | Image height in px                                        |
| status             | string    | PENDING, PROCESSING, SECTIONS_CONFIRMED, DETECTION_FAILED |
| createdAt          | timestamp |                                                           |
| updatedAt          | timestamp |                                                           |

Index: `{ bookId: 1, pageNumber: 1 }`

**API Response Transient Fields** (computed on read, not stored in DB):

| Field        | Type   | Notes                                                                 |
| ------------ | ------ | --------------------------------------------------------------------- |
| imageUrl     | string | Presigned S3 URL for the page image (derived from `imageKey`)         |
| thumbnailUrl | string | Presigned S3 URL for the page thumbnail (derived from `thumbnailKey`) |
| sections     | array  | Embedded section list for the page (fetched from sections collection) |

### Section

| Field               | Type      | Notes                                                          |
| ------------------- | --------- | -------------------------------------------------------------- |
| \_id                | ObjectId  | PK                                                             |
| pageId              | ObjectId  | Ref → Page                                                     |
| sectionOrder        | int       | Order within the page                                          |
| type                | string    | HEADER, PARAGRAPH, FOOTNOTE, IMAGE_CAPTION, PAGE_NUMBER, OTHER |
| x                   | float     | Position in px (relative to page image)                        |
| y                   | float     | Position in px                                                 |
| width               | float     | Width in px                                                    |
| height              | float     | Height in px                                                   |
| originalText        | text      | OCR/text extracted from image                                  |
| aiExtractedText     | text?     | AI-extracted text (higher accuracy than OCR for Indic scripts) |
| croppedImageKey     | string    | S3 key for the cropped section image                           |
| detectionConfidence | float     | ML detection confidence score (0.0–1.0), if available          |
| createdAt           | timestamp |                                                                |
| updatedAt           | timestamp |                                                                |

**API Response Transient Fields** (computed on read):

| Field           | Type   | Notes                                                                           |
| --------------- | ------ | ------------------------------------------------------------------------------- |
| croppedImageUrl | string | Presigned S3 URL for the cropped section image (derived from `croppedImageKey`) |

Index: `{ pageId: 1, sectionOrder: 1 }`

### SectionEditHistory (optional — for undo/redo support)

| Field     | Type      | Notes                                              |
| --------- | --------- | -------------------------------------------------- |
| \_id      | ObjectId  | PK                                                 |
| pageId    | ObjectId  | Ref → Page                                         |
| editorId  | ObjectId  | Ref → User                                         |
| action    | string    | CREATE, UPDATE, DELETE, TYPE_CHANGE, MOVE          |
| snapshot  | object    | Snapshot of affected section(s) at point of action |
| timestamp | timestamp |                                                    |

Index: `{ pageId: 1, timestamp: -1 }`

### Translation

| Field                  | Type      | Notes                                                                            |
| ---------------------- | --------- | -------------------------------------------------------------------------------- |
| \_id                   | ObjectId  | PK                                                                               |
| sectionId              | ObjectId  | Ref → Section                                                                    |
| translatorId           | ObjectId  | Ref → User                                                                       |
| translatedText         | string    | The translated text in the target language                                       |
| exactLetterTranslation | string?   | Letter-for-letter transliteration (AI-generated or manual, e.g. "माता" → "මාතා") |
| transliterationSource  | string?   | Source of transliteration: "ai" or "manual"                                      |
| isApproved             | boolean   |                                                                                  |
| approvedBy             | ObjectId? | Ref → User (editor who approved)                                                 |
| createdAt              | timestamp |                                                                                  |
| updatedAt              | timestamp |                                                                                  |

Indexes: `{ sectionId: 1, translatorId: 1 }` unique, `{ sectionId: 1, isApproved: 1 }`

### AITextExtraction

Stores the result of AI-powered text extraction from section images. Used to improve OCR quality for Indic scripts where traditional OCR (Tesseract) produces poor results.

| Field            | Type      | Notes                                            |
| ---------------- | --------- | ------------------------------------------------ |
| \_id             | ObjectId  | PK                                               |
| sectionId        | ObjectId  | Ref → Section                                    |
| extractedText    | text      | AI-extracted text content                        |
| confidence       | float     | Model confidence score (0.0–1.0)                 |
| model            | string    | Model identifier (e.g. "gpt-4o", "indic-ocr-v2") |
| processingTimeMs | int       | Time taken for extraction in milliseconds        |
| rawResponse      | object?   | Full model response for debugging/audit          |
| createdAt        | timestamp |                                                  |

Index: `{ sectionId: 1 }` unique

### Transliteration

Stores AI-generated transliterations (letter-for-letter script conversion) between Indic scripts. Attached to a Translation document.

| Field              | Type      | Notes                                                 |
| ------------------ | --------- | ----------------------------------------------------- |
| \_id               | ObjectId  | PK                                                    |
| translationId      | ObjectId  | Ref → Translation                                     |
| sourceText         | string    | Original text in source script                        |
| transliteratedText | string    | Converted text in target script                       |
| sourceScript       | string    | Source script (e.g. "devanagari", "tamil", "bengali") |
| targetScript       | string    | Target script (e.g. "sinhala", "tamil", "devanagari") |
| confidence         | float     | Model confidence score (0.0–1.0)                      |
| model              | string    | Model identifier (e.g. "indic-transliterate-v1")      |
| createdAt          | timestamp |                                                       |

Index: `{ translationId: 1 }` unique

### Comment

| Field     | Type      | Notes                                   |
| --------- | --------- | --------------------------------------- |
| \_id      | ObjectId  | PK                                      |
| sectionId | ObjectId  | Ref → Section                           |
| authorId  | ObjectId  | Ref → User                              |
| parentId  | ObjectId? | Ref → Comment (nullable, for threading) |
| content   | string    |                                         |
| createdAt | timestamp |                                         |

Index: `{ sectionId: 1, createdAt: 1 }`

## Computed / Transient Entities

These are not stored in MongoDB. They are assembled server-side from aggregation queries and returned as API response payloads.

### TranslationStats

Returned by `GET /api/books/{bookId}/stats`. Provides book-level translation progress.

| Field              | Type   | Notes                                                 |
| ------------------ | ------ | ----------------------------------------------------- |
| totalSections      | int    | Total sections across all pages                       |
| translatedSections | int    | Sections with at least one approved translation       |
| pendingSections    | int    | Sections with no approved translation                 |
| inProgressSections | int    | Sections with submitted translations awaiting review  |
| translationPercent | float  | `translatedSections / totalSections * 100`            |
| byLanguage         | object | Map of `{ language: { total, translated, percent } }` |
| byPage             | array  | Array of `{ pageNumber, total, translated, percent }` |

### TranslatorStats

Returned by `GET /api/translators/{userId}/stats`. Provides per-translator performance metrics scoped to a book.

| Field              | Type   | Notes                                                   |
| ------------------ | ------ | ------------------------------------------------------- |
| userId             | string | Translator user ID                                      |
| userName           | string | Display name                                            |
| totalAssigned      | int    | Sections this translator has worked on                  |
| approvedCount      | int    | Translations approved by an editor                      |
| rejectedCount      | int    | Translations rejected by an editor                      |
| pendingCount       | int    | Translations awaiting review                            |
| approvalRate       | float  | `approvedCount / (approvedCount + rejectedCount) * 100` |
| avgTurnaroundHours | float  | Average time from section assignment to submission      |
| lastActiveAt       | string | ISO timestamp of most recent translation activity       |

### TranslationHistoryItem

Returned by `GET /api/translations/history`. Provides a chronological log of translation activity for a book or translator.

| Field           | Type      | Notes                                                        |
| --------------- | --------- | ------------------------------------------------------------ |
| translationId   | string    | Translation document ID                                      |
| sectionId       | string    | Section that was translated                                  |
| pageNumber      | int       | Page number the section belongs to                           |
| sectionOrder    | int       | Order of the section within the page                         |
| translatorId    | string    | ID of the translator who submitted                           |
| translatorName  | string    | Display name of the translator                               |
| translatedText  | string    | The submitted translation text                               |
| action          | string    | SUBMITTED, APPROVED, REJECTED                                |
| performedBy     | string    | User ID who performed the action (editor for approve/reject) |
| performedByName | string    | Display name of the actor                                    |
| createdAt       | timestamp | When the translation was submitted or reviewed               |

### BookInvitation

| Field     | Type      | Notes                      |
| --------- | --------- | -------------------------- |
| \_id      | ObjectId  | PK                         |
| bookId    | ObjectId  | Ref → Book                 |
| userId    | ObjectId  | Ref → User                 |
| invitedBy | ObjectId  | Ref → User                 |
| status    | string    | PENDING, ACCEPTED, BLOCKED |
| createdAt | timestamp |                            |
| updatedAt | timestamp |                            |

Index: `{ bookId: 1, userId: 1 }` unique

### BookBuild

| Field     | Type      | Notes                       |
| --------- | --------- | --------------------------- |
| \_id      | ObjectId  | PK                          |
| bookId    | ObjectId  | Ref → Book                  |
| fileKey   | string    | S3 key for finalized PDF    |
| status    | string    | BUILDING, COMPLETED, FAILED |
| createdAt | timestamp |                             |
| updatedAt | timestamp |                             |

## S3 Storage Structure

```
books/{bookId}/original.pdf
books/{bookId}/thumbnail.png
books/{bookId}/pages/{pageNumber}.png
books/{bookId}/sections/{sectionId}.png     ← cropped section images
books/{bookId}/finalized.pdf
```

## Key Relationships

```
User ──< Book (owner)
User ──< BookEditor >── Book
User ──< Translation >── Section
User ──< Comment >── Section
User ──< BookInvitation >── Book
Book ──< Page
Page ──< Section
Section ──< Translation
Section ──< AITextExtraction
Section ──< Comment
Translation ──< Transliteration
Book ──< BookBuild
```
