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

| Field              | Type      | Notes                                             |
| ------------------ | --------- | ------------------------------------------------- |
| \_id               | ObjectId  | PK                                                |
| bookId             | ObjectId  | Ref → Book                                        |
| pageNumber         | int       | Sequential (1..N)                                 |
| originalPageNumber | string    | Original page label (e.g. "i", "(II)", "1", "1b") |
| imageKey           | string    | S3 key for page image                             |
| width              | int       | Image width in px                                 |
| height             | int       | Image height in px                                |
| status             | string    | PENDING, PROCESSING, SECTIONS_CONFIRMED           |
| createdAt          | timestamp |                                                   |
| updatedAt          | timestamp |                                                   |

Index: `{ bookId: 1, pageNumber: 1 }`

### Section

| Field           | Type      | Notes                                                          |
| --------------- | --------- | -------------------------------------------------------------- |
| \_id            | ObjectId  | PK                                                             |
| pageId          | ObjectId  | Ref → Page                                                     |
| sectionOrder    | int       | Order within the page                                          |
| type            | string    | HEADER, PARAGRAPH, FOOTNOTE, IMAGE_CAPTION, PAGE_NUMBER, OTHER |
| x               | float     | Position in px (relative to page image)                        |
| y               | float     | Position in px                                                 |
| width           | float     | Width in px                                                    |
| height          | float     | Height in px                                                   |
| originalText    | text      | OCR/text extracted from image                                  |
| croppedImageKey | string    | S3 key for the cropped section image                           |
| createdAt       | timestamp |                                                                |
| updatedAt       | timestamp |                                                                |

Index: `{ pageId: 1, sectionOrder: 1 }`

### Translation

| Field                  | Type      | Notes                                                                                        |
| ---------------------- | --------- | -------------------------------------------------------------------------------------------- |
| \_id                   | ObjectId  | PK                                                                                           |
| sectionId              | ObjectId  | Ref → Section                                                                                |
| translatorId           | ObjectId  | Ref → User                                                                                   |
| translatedText         | string    | The translated text in the target language                                                   |
| exactLetterTranslation | string?   | Optional: letter-for-letter transliteration (e.g. devanagari "माता" → Sinhala script "මාතා") |
| isApproved             | boolean   |                                                                                              |
| approvedBy             | ObjectId? | Ref → User (editor who approved)                                                             |
| createdAt              | timestamp |                                                                                              |
| updatedAt              | timestamp |                                                                                              |

Indexes: `{ sectionId: 1, translatorId: 1 }` unique, `{ sectionId: 1, isApproved: 1 }`

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
Section ──< Comment
Book ──< BookBuild
```
