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

| TC-ID   | Scenario                       | Steps                                                  | Expected Result                                                                        |
| ------- | ------------------------------ | ------------------------------------------------------ | -------------------------------------------------------------------------------------- |
| SECT-01 | Trigger section detection      | 1. Open page 2. Click "Detect Sections"                | Rectangles appear overlaid on page image with type labels                              |
| SECT-02 | Drag section rectangle         | 1. Select a rectangle 2. Drag to new position          | Rectangle moves, coordinates update in sidebar                                         |
| SECT-03 | Resize section rectangle       | 1. Select rectangle 2. Drag corner handle              | Rectangle resizes, dimensions update                                                   |
| SECT-04 | Delete section                 | 1. Select rectangle 2. Press Delete key or click trash | Rectangle removed. Undo available.                                                     |
| SECT-05 | Add new section                | 1. Click "Add Section" 2. Click-drag on canvas         | New rectangle created with default type "Paragraph"                                    |
| SECT-06 | Change section type            | 1. Select rectangle 2. Change type dropdown            | Rectangle color updates to match type                                                  |
| SECT-07 | Confirm sections               | 1. Click "Confirm All"                                 | Sections saved to MongoDB. Page status = SECTIONS_CONFIRMED                            |
| SECT-08 | Undo/Redo                      | 1. Make edits 2. Ctrl+Z / Ctrl+Shift+Z                 | Actions undo/redo correctly                                                            |
| SECT-09 | Detection failure              | 1. Open page with unclear image 2. Click "Detect"      | Error shown with "Retry" button                                                        |
| SECT-10 | Re-edit confirmed sections     | 1. Open page with confirmed sections 2. Modify         | Changes save on re-confirm                                                             |
| SECT-11 | Section cropping after confirm | 1. Confirm sections 2. Wait for processing             | Each section gets a cropped image stored in S3. Section document has `croppedImageKey` |

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

#### 5a. Auto-Load & Tab System

| TC-ID     | Scenario                            | Steps                                                                 | Expected Result                                                              |
| --------- | ----------------------------------- | --------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| TRANS-A01 | Auto-load first section on mount    | 1. Open `/translate` 2. Wait for mount                                | First untranslated section loaded automatically (no "Next" click needed)     |
| TRANS-A02 | Auto-load respects filters          | 1. Set lang=si, page=3 2. Reload page                                 | First section matching si + page=3 loaded                                    |
| TRANS-A03 | Tab bar renders with 3 tabs         | 1. Login as editor 2. Open `/translate`                               | Translate, History, Stats tabs visible                                       |
| TRANS-A04 | Translator sees 2 tabs              | 1. Login as translator 2. Open `/translate`                           | Translate and History tabs only (Stats hidden)                                |
| TRANS-A05 | Default tab is Translate            | 1. Open `/translate` without `?tab=` param                            | Translate tab active by default                                              |
| TRANS-A06 | Tab switch updates URL              | 1. Click History tab                                                   | URL updates to `?tab=history`                                                |
| TRANS-A07 | Tab state survives reload           | 1. Click History tab 2. Reload page                                   | History tab remains active                                                   |
| TRANS-A08 | Stats tab editor-only                | 1. Login as translator 2. Try to navigate to `?tab=stats`             | Stats tab not shown, URL param ignored or redirected to translate tab        |

#### 5b. Source Text Side-by-Side

| TC-ID     | Scenario                            | Steps                                                                 | Expected Result                                                              |
| --------- | ----------------------------------- | --------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| TRANS-S01 | Source text panel visible            | 1. Open Translate tab with section loaded                             | Two-column layout: image+source left, editor right                           |
| TRANS-S02 | Source text labeled                  | 1. Inspect source text panel                                          | Header shows "Source Text" with icon                                         |
| TRANS-S03 | Source text read-only                | 1. Try to click/type in source text panel                             | No cursor, no editing possible                                               |
| TRANS-S04 | Missing original text fallback       | 1. Section with empty `originalText` 2. Open Translate                | Message: "Original text not available — use the image above"                 |
| TRANS-S05 | Mobile stacked layout                | 1. View on <768px viewport                                            | Stacked: image, source text, then editor                                     |
| TRANS-S06 | Auto-translation prefills editor     | 1. Section with auto-translation from LibreTranslate                  | Translation textarea pre-filled with auto-translated text                    |
| TRANS-S07 | Edit original text link (editor)     | 1. Login as editor 2. View source text panel                          | "Edit original text" link visible, navigates to page editor                  |
| TRANS-S08 | No edit link for translator          | 1. Login as translator 2. View source text panel                      | "Edit original text" link NOT visible                                        |

#### 5c. Translation History (US-TR-1)

| TC-ID     | Scenario                            | Steps                                                                 | Expected Result                                                              |
| --------- | ----------------------------------- | --------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| TRANS-H01 | History tab renders list             | 1. Click History tab                                                  | List of past translations shown, sorted most recent first                    |
| TRANS-H02 | History item fields                  | 1. Inspect first history item                                         | Shows: thumbnail, page number, section order, text snippet (≤80 chars), status badge, timestamp |
| TRANS-H03 | Status badge colors                  | 1. View history items                                                 | APPROVED=green, REJECTED=red, PENDING=amber                                  |
| TRANS-H04 | Infinite scroll loads more           | 1. Scroll to bottom of history list                                   | Next batch of items appended, loading indicator shown                        |
| TRANS-H05 | Cursor-based pagination              | 1. Scroll through 3 pages of history                                  | Items contiguous, no duplicates, no gaps                                     |
| TRANS-H06 | End of history                       | 1. Scroll through all items                                           | No more fetches, list ends                                                   |
| TRANS-H07 | Empty history state                  | 1. Translator with no submissions 2. Open History                     | "No translations yet — start translating!" with link to Translate tab        |
| TRANS-H08 | Click item navigates to section      | 1. Click a history item                                               | Navigates to `/translate?section={sectionId}`                                |
| TRANS-H09 | Translator sees own history only     | 1. Login as translator-a 2. Open History                              | Only translator-a's translations shown                                       |
| TRANS-H10 | Editor sees all history              | 1. Login as editor 2. Open History                                    | All translators' translations shown                                          |
| TRANS-H11 | Badge updates on approve             | 1. Translator submits 2. Editor approves 3. Translator views History  | Badge changes from PENDING to APPROVED                                       |
| TRANS-H12 | History filters independent          | 1. Set lang=si on Translate 2. Switch to History 3. Set lang=ta       | History shows ta, Translate still has si                                     |

#### 5d. Translation Statistics (US-TR-2)

| TC-ID     | Scenario                            | Steps                                                                 | Expected Result                                                              |
| --------- | ----------------------------------- | --------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| TRANS-T01 | Stats tab editor-only                | 1. Login as translator 2. Open `/translate`                           | Stats tab NOT visible                                                        |
| TRANS-T02 | Stats card renders                   | 1. Login as editor 2. Click Stats tab                                 | Progress bar, approved/pending/in-progress/total counts shown               |
| TRANS-T03 | Progress bar matches data            | 1. View progress bar                                                  | Bar fill width matches percentage displayed                                  |
| TRANS-T04 | Per-language breakdown               | 1. Multi-language book 2. View Stats                                  | Language cards shown with correct per-language stats                         |
| TRANS-T05 | Per-page grid                        | 1. View Stats tab                                                     | Color-coded cells: green=100%, yellow=partial, gray=0%                      |
| TRANS-T06 | Stats refresh every 30s              | 1. Open Stats 2. Submit translation from another tab 3. Wait 30s      | Stats update automatically                                                   |
| TRANS-T07 | Stats cached in Redis                | 1. GET stats 2. GET stats again within 30s                            | Second request served from cache                                             |
| TRANS-T08 | Cache invalidated on translation      | 1. GET stats 2. Submit translation 3. GET stats                       | Fresh data returned                                                          |
| TRANS-T09 | Empty book stats                     | 1. Book with 0 sections 2. View Stats                                 | Shows 0/0, 0%                                                                |

#### 5e. Translator Performance Stats (US-TR-3)

| TC-ID     | Scenario                            | Steps                                                                 | Expected Result                                                              |
| --------- | ----------------------------------- | --------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| TRANS-P01 | Translator table renders             | 1. Login as editor 2. Open Stats tab                                  | Table with Name, Assigned, Approved, Rejected, Rate, Avg Time columns       |
| TRANS-P02 | Default sort by approval rate        | 1. View translator table                                              | Rows sorted by approval rate descending                                      |
| TRANS-P03 | Sort by any column                   | 1. Click "Name" header                                                | Table sorts by name. Click again = reverse sort                              |
| TRANS-P04 | Approval rate correct                | 1. View translator row                                                | = approved / (approved + rejected) * 100, rounded to 1 decimal               |
| TRANS-P05 | Zero submissions shows "No activity" | 1. Translator with no submissions 2. View Stats                       | Row shows "—" for metrics, not 0% or N/A                                    |
| TRANS-P06 | Click row expands activity           | 1. Click translator row                                               | Row expands to show last 10 submissions                                      |
| TRANS-P07 | Translator cannot see others' stats  | 1. Login as translator 2. Attempt `/api/books/{id}/translators/stats` | API returns 403 Forbidden                                                    |

#### 5f. Filters (US-TR-4)

| TC-ID     | Scenario                            | Steps                                                                 | Expected Result                                                              |
| --------- | ----------------------------------- | --------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| TRANS-F01 | Filter bar visible                   | 1. Open `/translate`                                                  | Language dropdown, page dropdown, status dropdown, clear button visible      |
| TRANS-F02 | Language filter hidden single lang   | 1. Book with 1 target language 2. View filters                        | Language dropdown not shown                                                  |
| TRANS-F03 | Filter applies immediately          | 1. Select lang=si                                                     | Next section fetched with `language=si`                                      |
| TRANS-F04 | Filters compose (AND logic)          | 1. Select lang=si, page=3, status=PENDING                             | API called with all three params                                             |
| TRANS-F05 | Filters persist in URL               | 1. Set lang=si, page=3 2. Check URL                                   | URL shows `?lang=si&page=3`                                                 |
| TRANS-F06 | URL params survive reload            | 1. Set filters 2. Reload page                                         | Filters restored from URL                                                    |
| TRANS-F07 | Clear filters resets defaults        | 1. Set filters 2. Click Clear                                         | All filters reset, URL params cleared                                        |
| TRANS-F08 | History filters independent          | 1. Set lang=si on Translate 2. Switch to History 3. Set lang=ta       | History shows ta, Translate still has si                                     |
| TRANS-F09 | No match empty state                 | 1. Set filters matching nothing 2. Click Next                         | "No sections match your filters" with Clear Filters CTA                     |
| TRANS-F10 | Invalid URL params handled           | 1. Navigate to `?lang=xyz&page=-1`                                    | Invalid params ignored, defaults used, no crash                              |

#### 5g. Auto-save Drafts (US-TR-6)

| TC-ID     | Scenario                            | Steps                                                                 | Expected Result                                                              |
| --------- | ----------------------------------- | --------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| TRANS-D01 | Draft saves after 5s inactivity      | 1. Type in textarea 2. Stop typing 3. Wait 5s                         | "Draft saved ✓" indicator appears briefly                                    |
| TRANS-D02 | Draft debounce resets on typing      | 1. Type 2. Wait 3s 3. Type again 4. Wait 5s                           | Draft saves only after final 5s of inactivity                                |
| TRANS-D03 | Draft does not save empty text       | 1. Clear textarea 2. Wait 5s                                          | No draft saved                                                               |
| TRANS-D04 | Draft prefills on section load       | 1. Save draft for section A 2. Return to section A                    | Translation textarea prefilled with draft text                               |
| TRANS-D05 | Draft deleted on submit              | 1. Save draft 2. Submit translation                                   | Draft deleted from TranslationDrafts collection                              |
| TRANS-D06 | Draft not created if already done    | 1. Section already translated by this translator 2. Open section      | No draft created                                                             |
| TRANS-D07 | Unsaved changes warning              | 1. Type translation 2. Try to close tab                               | Browser shows "You have unsaved changes" confirmation                        |
| TRANS-D08 | No warning when clean                | 1. Open section 2. Don't type 3. Close tab                            | No warning shown                                                             |
| TRANS-D09 | Draft expires after 24h              | 1. Create draft 2. Set createdAt to 25h ago 3. GET draft              | 404 — draft not found                                                        |
| TRANS-D10 | Drafts per-translator per-section    | 1. Translator A saves draft for section X 2. Translator B opens X     | B does NOT see A's draft                                                     |
| TRANS-D11 | POST draft creates                   | 1. POST `{ sectionId, translatedText }`                               | 200: `{ draftId, updatedAt }`                                                |
| TRANS-D12 | POST draft upserts                   | 1. POST draft 2. POST again same sectionId                            | Draft updated, same draftId                                                  |
| TRANS-D13 | GET draft returns                    | 1. Create draft 2. GET `?sectionId=X`                                 | Returns draft with text                                                      |
| TRANS-D14 | GET draft 404                        | 1. GET nonexistent section                                            | 404: `{ "detail": "No draft found" }`                                       |
| TRANS-D15 | DELETE draft success                 | 1. Create draft 2. DELETE by draftId                                  | 200: `{ "status": "deleted" }`                                               |
| TRANS-D16 | localStorage fallback                | 1. Mock API delay 10s 2. Type translation                             | Draft saved to localStorage immediately                                      |

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

### 8. AI Text Extraction (US-ST-1)

| TC-ID   | Scenario                             | Steps                                                                        | Expected Result                                                                          |
| ------- | ------------------------------------ | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| EXT-01  | Trigger extraction — success         | 1. Click "Extract Text" on section 2. Wait                                   | Extraction completes. AI text shown with confidence badge.                                |
| EXT-02  | Extraction — no cropped image        | 1. `POST /api/sections/{id}/extract` for section without croppedImageKey     | 422: "Section has no cropped image."                                                     |
| EXT-03  | Extraction — already extracted       | 1. Extract section 2. `POST` again                                           | 409: existing result returned (idempotent).                                               |
| EXT-04  | Fetch extraction result              | 1. `GET /api/sections/{id}/extraction` after completion                      | 200: extractedText, confidence, model, processingTimeMs                                  |
| EXT-05  | Extraction returns correct text      | 1. Section with known Sinhala text 2. Extract 3. Compare                     | `aiExtractedText` matches expected text                                                  |
| EXT-06  | Confidence score in range            | 1. Extract section 2. Check confidence                                       | Float between 0.0 and 1.0                                                                |
| EXT-07  | High confidence badge (green)        | 1. Section with confidence ≥ 0.9 2. View panel                               | Green badge: `[AI Extracted] 94% ●`                                                      |
| EXT-08  | Medium confidence badge (yellow)     | 1. Section with confidence ≥ 0.7 and < 0.9                                  | Yellow badge: `[AI Extracted] 78% ●`                                                     |
| EXT-09  | Low confidence badge (red)           | 1. Section with confidence < 0.7                                             | Red badge: `[AI Extracted] 45% ●`                                                        |
| EXT-10  | OCR fallback badge (gray)            | 1. Section without AI extraction                                             | Gray badge: `[OCR] ●`                                                                    |
| EXT-11  | Extract button visible (editor)      | 1. Login as editor 2. Section without AI text                                | "Extract Text" button visible                                                             |
| EXT-12  | Extract button hidden (translator)   | 1. Login as translator 2. Section without AI text                            | Button NOT visible                                                                        |
| EXT-13  | Regenerate shows confirmation        | 1. Click "Regenerate" on extracted section                                   | Dialog: "Re-extract text? This will replace current AI text."                            |
| EXT-14  | Regenerate replaces previous result  | 1. Extract section (result A) 2. Re-extract (result B)                       | Previous AITextExtraction replaced, Section.aiExtractedText updated to B                 |
| EXT-15  | Editor sees both texts               | 1. Login as editor 2. Section with AI extraction                             | Both OCR and AI text visible in section detail view                                      |
| EXT-16  | AI extraction failure — OpenAI error | 1. Mock OpenAI 500 2. Trigger extraction                                     | Task retries 3x, then marks FAILED, section retains OCR text                            |
| EXT-17  | Extraction semaphore (max 5)         | 1. Trigger 6 extractions simultaneously                                      | 5 run concurrently, 1 queued (Redis semaphore)                                           |
| EXT-18  | Extraction is idempotent             | 1. Extract section 2. Re-extract                                             | Previous result replaced, no duplicate documents                                         |
| EXT-19  | Batch page extraction                | 1. `POST /api/books/{id}/pages/{pageNum}/extract`                            | 202: all sections on page queued for extraction                                          |
| EXT-20  | Extraction in-progress indicator     | 1. Trigger extraction 2. Immediately view panel                              | Blue animated badge: `[Extracting...] ●○○`                                               |

### 9. AI Transliteration (US-ST-2)

| TC-ID   | Scenario                              | Steps                                                                           | Expected Result                                                                           |
| ------- | ------------------------------------- | ------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| TRNS-01 | Transliterate — success               | 1. Click "Generate with AI" on section with AI text 2. Wait                     | Transliteration generated, pre-fills exact letter field                                   |
| TRNS-02 | Transliterate — cached                | 1. Generate transliteration 2. Load same section again                          | Pre-filled from cache, no new OpenAI call                                                 |
| TRNS-03 | Transliterate — no source text        | 1. `POST /api/sections/{id}/transliterate` for section without text             | 422: "No source text available. Run AI extraction first."                                 |
| TRNS-04 | Transliteration matches source        | 1. Known Devanagari text 2. Transliterate to Sinhala                            | Correct letter-for-letter conversion                                                      |
| TRNS-05 | Transliteration preserves spaces      | 1. Transliterate multi-word text                                                | Word boundaries preserved in output                                                       |
| TRNS-06 | Spinner during generation             | 1. Click generate 2. Check panel                                                | `[Generating...] ●○○` badge, "Generating transliteration..." text                         |
| TRNS-07 | Failure shows manual prompt           | 1. Transliteration API fails                                                    | "Transliteration unavailable — enter manually"                                            |
| TRNS-08 | Manual edit marks as manual           | 1. Edit pre-filled transliteration 2. Check transliterationSource               | Source changed to "manual"                                                                |
| TRNS-09 | Regenerate button for cached          | 1. Section with cached transliteration 2. View panel                            | "Regenerate" button visible below transliteration                                         |
| TRNS-10 | Cache per section+language pair       | 1. Generate for Sinhala 2. Generate for Tamil                                   | Two separate Transliteration documents created                                           |
| TRNS-11 | Fetch cached transliterations         | 1. `GET /api/sections/{id}/transliterations`                                    | 200: array of transliterations with targetScript, text, confidence                       |
| TRNS-12 | OpenAI failure → retry                | 1. Mock OpenAI failure 2. Trigger transliteration                               | Task retries 3x, then fails gracefully                                                   |

### 10. Bidirectional Sync

| TC-ID   | Scenario                                      | Steps                                                                   | Expected Result                                                                        |
| ------- | --------------------------------------------- | ----------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| SYNC-01 | Edit source text invalidates cache            | 1. Edit source text 2. Wait 500ms debounce                              | `PUT /api/sections/{id}/source-text` called, transliteration cache invalidated          |
| SYNC-02 | Regenerate button appears after edit          | 1. Edit source text 2. Check transliteration panel                      | "Regenerate" button pulses/appears                                                     |
| SYNC-03 | Source text debounce works                    | 1. Type in source text 2. Wait 300ms 3. Type more 4. Wait 500ms         | Single API call with final text                                                        |
| SYNC-04 | Edit transliteration doesn't modify source    | 1. Edit transliteration text 2. Check source text panel                 | Source text unchanged                                                                  |
| SYNC-05 | Manual transliteration marked as manual       | 1. Edit transliteration 2. Check transliterationSource                   | Source changed to "manual"                                                             |
| SYNC-06 | No infinite loops                             | 1. Edit source text 2. Wait for invalidation 3. Check transliteration   | Transliteration shows "Regenerate" but does NOT auto-update                            |
| SYNC-07 | Rapid edits don't cascade                     | 1. Rapidly edit source text 10 times                                    | Only last edit triggers API (debounce), no cascading updates                           |
| SYNC-08 | Concurrent source edits — last write wins     | 1. User A edits source 2. User B edits source (different text)          | Last save wins, no data corruption                                                     |

### 11. Extraction Status Tracking (US-ST-4)

| TC-ID   | Scenario                              | Steps                                                                   | Expected Result                                                                     |
| ------- | ------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| STAT-01 | Extracted section — green overlay     | 1. Section with AITextExtraction 2. View book page                      | Green "Extracted" badge on section thumbnail                                        |
| STAT-02 | Pending section — gray overlay        | 1. Section without AITextExtraction 2. View page                        | Gray "Pending" badge                                                                |
| STAT-03 | Failed section — red overlay          | 1. Section with failed extraction 2. View page                          | Red "Failed" badge                                                                  |
| STAT-04 | Click Failed opens retry dialog       | 1. Click "Failed" badge                                                  | Retry dialog opens                                                                  |
| STAT-05 | Page-level extraction progress        | 1. View page with mixed extraction states                               | "8/12 sections extracted" with progress bar                                         |
| STAT-06 | Stats API includes extractionStats    | 1. `GET /api/books/{id}/stats`                                           | `extractionStats` with total, extracted, pending, failed                            |
| STAT-07 | Filter by extraction status           | 1. Open section list 2. Select "EXTRACTED" filter                       | Only extracted sections shown                                                        |
| STAT-08 | Batch extraction progress tracking    | 1. Trigger batch 2. `GET /api/books/{id}/extraction/status`              | `{ totalSections, extracted, pending, failed, inProgress }`                          |

### 12. Batch Auto-Extract (US-ST-5)

| TC-ID   | Scenario                              | Steps                                                                   | Expected Result                                                                     |
| ------- | ------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| BATCH-01 | Trigger batch — success               | 1. `POST /api/books/{id}/extract`                                       | 202: taskId, totalSections, estimatedCost                                           |
| BATCH-02 | Batch — already in progress           | 1. Trigger batch 2. `POST` again                                        | 409: in-progress status with completed/total counts                                 |
| BATCH-03 | Batch confirmation dialog             | 1. Click "Extract All" 2. Check dialog                                  | "This will extract 156 sections. Cost: $1.28. Proceed?"                             |
| BATCH-04 | Batch progress bar                    | 1. Trigger batch 2. View console                                         | "Extracting section 34/156..." with progress bar                                     |
| BATCH-05 | Batch — individual failure continues  | 1. One section fails during batch                                        | Remaining sections processed, failed count incremented                               |
| BATCH-06 | Batch summary — failures              | 1. Batch completes with 2 failures 2. View summary                       | "154 extracted, 2 failed" with "Retry Failed" button                                |
| BATCH-07 | Retry Failed re-runs failed sections  | 1. Click "Retry Failed"                                                  | Only failed sections re-extracted                                                    |
| BATCH-08 | Batch — cost limit enforced           | 1. Set cost limit $0.50 2. Book with 100 sections (est. $0.70)          | Batch blocked: cost exceeds limit                                                    |
| BATCH-09 | Button shows progress when active     | 1. Batch in progress 2. Check button text                                | "Extraction in progress (34/156)"                                                    |
| BATCH-10 | Button disabled during batch          | 1. Batch in progress 2. Check button state                               | "Extract All Sections" button disabled                                                |

### 13. Admin Configuration (US-ST-6)

| TC-ID   | Scenario                              | Steps                                                                   | Expected Result                                                                     |
| ------- | ------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| ADMIN-01 | GET extraction config                 | 1. `GET /api/admin/settings/extraction`                                 | `{ model, confidenceThreshold, maxConcurrent, costLimitPerBook, enabled }`           |
| ADMIN-02 | PUT update config                     | 1. `PUT /api/admin/settings/extraction` with new values                 | Config updated, 200 response                                                        |
| ADMIN-03 | Config persisted in SystemConfig      | 1. Update config 2. Check MongoDB `system_config` collection            | Key-value document exists with correct values                                       |
| ADMIN-04 | Threshold affects badge color         | 1. Set threshold 0.8 2. Section with confidence 0.85                    | Badge shows yellow (below 0.9, above 0.8 threshold)                                |
| ADMIN-05 | Low confidence flagged for review     | 1. Set threshold 0.8 2. Section with confidence 0.6                     | Extraction saved but flagged for manual review                                       |
| ADMIN-06 | Cost limit blocks batch               | 1. Set cost limit $0.10 2. Book with 50 sections (est. $0.35)           | Batch blocked with warning                                                           |
| ADMIN-07 | Model change takes effect immediately | 1. Change model to "gpt-4o-mini" 2. Trigger extraction                  | New model used (check AITextExtraction.model)                                       |
| ADMIN-08 | Max concurrent affects semaphore      | 1. Set max concurrent 3 2. Trigger batch                                 | Only 3 concurrent extractions                                                       |
| ADMIN-09 | Disabled extraction blocks triggers   | 1. Set enabled=false 2. Click "Extract Text"                             | "AI extraction is disabled" message                                                  |
| ADMIN-10 | Audit log endpoint                    | 1. `GET /api/admin/extraction/audit`                                     | Array of extraction records with model, cost, confidence                             |
| ADMIN-11 | Admin settings page UI                | 1. Login as super admin 2. `/admin/settings`                             | AI Extraction section with model dropdown, threshold slider, cost input              |
| ADMIN-12 | Config — 403 for non-admin            | 1. GET/PUT settings as editor                                            | 403 Forbidden                                                                        |

### 14. Layout — Translation Page Redesign

| TC-ID   | Scenario                              | Steps                                                                   | Expected Result                                                                     |
| ------- | ------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| LAY-01  | Two-row four-panel layout             | 1. View translate tab on desktop                                         | Top row: image+source. Bottom row: translit+translation                             |
| LAY-02  | Shared zoom — image and text           | 1. Click + zoom button                                                   | Image scales, source text font scales proportionally (14px × zoom%)                 |
| LAY-03  | Zoom range 50%–300%                   | 1. Zoom to min 2. Zoom to max                                            | Min 50%, max 300% enforced                                                           |
| LAY-04  | Reset zoom restores 100%              | 1. Zoom to 200% 2. Click ⟳                                              | Both image and text return to 100%                                                   |
| LAY-05  | Mobile stacked layout                  | 1. View on <768px                                                       | All four panels stacked vertically                                                   |
| LAY-06  | Tablet side-by-side                    | 1. View on 768–1024px                                                   | Side-by-side with collapsible image panel                                            |
| LAY-07  | Image drag-to-pan at any zoom          | 1. Zoom to 200% 2. Drag image                                           | Image pans smoothly                                                                  |

### 15. Edge Cases & Error Handling

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
| EDGE-09 | OpenAI API key invalid                   | 1. Set invalid OPENAI_API_KEY 2. Trigger extraction                | Graceful error: "AI extraction unavailable", section retains OCR   |
| EDGE-10 | OpenAI quota exceeded                    | 1. Mock quota exceeded 2. Trigger extraction                       | Error logged, extraction FAILED, retry available                   |
| EDGE-11 | Redis unavailable for semaphore          | 1. Stop Redis 2. Trigger extraction                                | Extraction proceeds without concurrency limit or graceful error    |
| EDGE-12 | Section with very long text              | 1. Section with 5000+ char text 2. Transliterate                   | Transliteration handles long text, no truncation                  |
| EDGE-13 | Batch extraction with 0 sections         | 1. Book with no sections 2. Trigger batch                          | 422 or 0 totalSections                                            |
| EDGE-14 | Source text edit with only OCR text      | 1. Section with no AI text 2. Edit OCR text                        | OCR text updated, no transliteration invalidation                 |
| EDGE-15 | Transliterate before extraction          | 1. Click "Transliterate" on section without any text               | 422 error, "Run AI extraction first" shown                        |

<<<<<<< Updated upstream
=======
### 16. Page Editor — Concurrent Editing & Race Conditions

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

>>>>>>> Stashed changes
## Regression Checklist

### Core Platform
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
<<<<<<< Updated upstream
=======
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

### Translation Page Redesign
- [ ] Translation page auto-loads first section on mount
- [ ] Tab system renders correctly (Translate, History, Stats)
- [ ] Stats tab hidden from translators, visible to editors
- [ ] Source text panel shows original text side-by-side
- [ ] Missing original text shows fallback message
- [ ] Translation history shows correct items with status badges
- [ ] History infinite scroll loads more items via cursor pagination
- [ ] History click navigates to section
- [ ] Translator sees only own history; editor sees all
- [ ] Stats card shows correct totals and percentages
- [ ] Progress bar matches translation percentage
- [ ] Per-language breakdown correct for multi-language books
- [ ] Per-page grid color-coding matches actual progress
- [ ] Stats refresh every 30s via React Query
- [ ] Stats cached in Redis with 30s TTL
- [ ] Translator performance table renders with correct metrics
- [ ] Approval rate calculated correctly
- [ ] Translator row expand shows recent activity
- [ ] Filters apply immediately on selection
- [ ] Filters compose with AND logic
- [ ] Filter state persisted in URL query params
- [ ] Clear filters resets to defaults
- [ ] History tab filters independent from Translate tab
- [ ] Draft auto-saves after 5s inactivity
- [ ] Draft prefills textarea on section load
- [ ] Draft deleted on translation submission
- [ ] Drafts expire after 24h (TTL index)
- [ ] Drafts isolated per-translator per-section
- [ ] beforeunload warning for unsaved changes
- [ ] localStorage fallback when API unavailable

### Source Text Modifications (AI Extraction & Transliteration)
- [ ] AI extraction triggers successfully per-section and batch
- [ ] Extracted text saved to Section.aiExtractedText and AITextExtraction collection
- [ ] Confidence score displayed as badge (green/yellow/red)
- [ ] Extraction idempotent — re-run replaces previous result
- [ ] Extraction failure retains OCR text, shows error toast
- [ ] Batch extraction processes sections with max 5 concurrency (Redis semaphore)
- [ ] Batch progress tracked in Redis and displayed in UI
- [ ] Transliteration generates correctly for Indic scripts
- [ ] Transliteration cached per section+language pair
- [ ] Transliteration pre-fills exactLetterTranslation field
- [ ] Manual transliteration edit marked as "manual" source
- [ ] Source text edit invalidates transliteration cache (500ms debounce)
- [ ] Transliteration edit does NOT modify source text
- [ ] No infinite loops from bidirectional sync
- [ ] Translation editor shows AI text as primary when available
- [ ] Fallback to OCR text when AI extraction unavailable
- [ ] Auto-translation uses AI text (not OCR) when available
- [ ] Two-row four-panel layout renders correctly on desktop
- [ ] Shared zoom scales image and source text proportionally
- [ ] Mobile stacked layout works on <768px viewports
- [ ] Admin can configure model, threshold, concurrent limit, cost limit
- [ ] Cost limit enforced before batch extraction
- [ ] Extraction audit log available for admin review
- [ ] AI extraction disabled via config blocks all triggers
- [ ] OPENAI_API_KEY required in environment
>>>>>>> Stashed changes
