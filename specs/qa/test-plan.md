# Maha Pothana — Test Plan

## Scope

This test plan covers the core features of the Maha Pothana book translation platform. Since no test framework is configured, testing is manual and scenario-based.

## Test Categories

### 1. Authentication & Authorization

| TC-ID | Scenario | Steps | Expected Result |
|-------|----------|-------|-----------------|
| AUTH-01 | Google SSO login | 1. Click "Sign in with Google" 2. Select Google account 3. Allow permissions | Redirected to dashboard. User created with EDITOR + TRANSLATOR roles. |
| AUTH-02 | First-time login flow | 1. Login with new Google account | User record created, both roles assigned, onboarding shown |
| AUTH-03 | Returning user login | 1. Login with existing Google account | Dashboard shown with existing roles and data |
| AUTH-04 | Super Admin role management | 1. Login as super admin 2. Navigate to Admin > Users 3. Change user role 4. User refreshes | Role change visible on user's next page load |
| AUTH-05 | Role-based nav visibility | 1. Login as Editor-only 2. Login as Translator-only | Editor sees Books/Upload; Translator sees Translate only |
| AUTH-06 | Unauthenticated access | 1. Visit any protected route without login | Redirected to login page |
| AUTH-07 | Invalid Google token | 1. Use expired/revoked Google token | Error message shown, login failed |

### 2. Book Upload

| TC-ID | Scenario | Steps | Expected Result |
|-------|----------|-------|-----------------|
| UPLOAD-01 | Upload valid PDF | 1. Fill title/author/source language/target languages 2. Select valid PDF 3. Click Upload | Progress bar shown, then redirect to book console |
| UPLOAD-02 | Duplicate book detection | 1. Upload same file twice | Error: "This book has already been uploaded" + link to existing |
| UPLOAD-03 | Invalid file type | 1. Select non-PDF file | Error: "Please upload a valid PDF" |
| UPLOAD-04 | Missing required fields | 1. Leave title/author/source language/target languages empty 2. Click Upload | Validation errors shown on empty fields |
| UPLOAD-05 | Large file upload | 1. Upload 500MB+ PDF | Progress bar works, no timeout, redirect on success |
| UPLOAD-06 | Cancel upload | 1. Start upload 2. Click Cancel | Upload cancelled, file not saved |
| UPLOAD-07 | Editor-only access | 1. Login as translator 2. Navigate to /books/new | 403 or hidden from nav |
| UPLOAD-08 | Multiple target languages | 1. Select 2+ target languages 2. Upload | Book shows both languages in metadata |

### 3. Page Processing

| TC-ID | Scenario | Steps | Expected Result |
|-------|----------|-------|-----------------|
| PAGE-01 | Auto page splitting | 1. Upload book 2. Wait for processing | All pages extracted, numbered 1..N, status shows "Ready" |
| PAGE-02 | Failed page split | 1. Upload corrupted PDF | Error shown, book status = FAILED, retry option |
| PAGE-03 | View page list | 1. Open book console | Page list shows all pages with status badges |
| PAGE-04 | Select page to edit | 1. Click a page in sidebar | Page image loaded in viewer |
| PAGE-05 | Original page number display | 1. Upload book with roman-numbered pages 2. View page list | Pages show original labels (i, ii, 1, 1b) alongside sequential numbers |

### 4. Section Detection & Editing

| TC-ID | Scenario | Steps | Expected Result |
|-------|----------|-------|-----------------|
| SECT-01 | Trigger section detection | 1. Open page 2. Click "Detect Sections" | Rectangles appear overlaid on page image with type labels |
| SECT-02 | Drag section rectangle | 1. Select a rectangle 2. Drag to new position | Rectangle moves, coordinates update in sidebar |
| SECT-03 | Resize section rectangle | 1. Select rectangle 2. Drag corner handle | Rectangle resizes, dimensions update |
| SECT-04 | Delete section | 1. Select rectangle 2. Press Delete key or click trash | Rectangle removed. Undo available. |
| SECT-05 | Add new section | 1. Click "Add Section" 2. Click-drag on canvas | New rectangle created with default type "Paragraph" |
| SECT-06 | Change section type | 1. Select rectangle 2. Change type dropdown | Rectangle color updates to match type |
| SECT-07 | Confirm sections | 1. Click "Confirm All" | Sections saved to MongoDB. Page status = SECTIONS_CONFIRMED |
| SECT-08 | Undo/Redo | 1. Make edits 2. Ctrl+Z / Ctrl+Shift+Z | Actions undo/redo correctly |
| SECT-09 | Detection failure | 1. Open page with unclear image 2. Click "Detect" | Error shown with "Retry" button |
| SECT-10 | Re-edit confirmed sections | 1. Open page with confirmed sections 2. Modify | Changes save on re-confirm |
| SECT-11 | Section cropping after confirm | 1. Confirm sections 2. Wait for processing | Each section gets a cropped image stored in S3. Section document has `croppedImageKey` |

### 5. Translation

| TC-ID | Scenario | Steps | Expected Result |
|-------|----------|-------|-----------------|
| TRANS-01 | Get next section | 1. Open Translate page 2. Click "Next Section" | Random untranslated section displayed with auto-translated text |
| TRANS-02 | Submit translation | 1. Enter translated text 2. Click Save | "Translation saved" toast. Section removed from queue. |
| TRANS-03 | Submit with exact letter | 1. Enter translated text 2. Enter exact letter transliteration 3. Click Save | Both fields saved. Section shows exact letter field on review. |
| TRANS-04 | Empty queue | 1. Translate all assigned sections 2. Click "Next" | "All sections translated!" message |
| TRANS-05 | Page context viewing | 1. Open a section 2. Click "View Full Page" | Full page shown with section highlighted |
| TRANS-06 | Navigate to adjacent pages | 1. Click "Previous Page" / "Next Page" | Adjacent page loaded, context updated. Page labels show `originalPageNumber`. |
| TRANS-07 | Zoom in/out | 1. Click + / - zoom buttons | Image scales, zoom % updates. Reset works. |
| TRANS-08 | Skip section | 1. Click "Skip" | Next section loaded. Skipped section returns to pool. |
| TRANS-09 | Add comment | 1. Type comment 2. Click Post | Comment appears with name + timestamp |
| TRANS-10 | Threaded replies | 1. Click "Reply" on existing comment 2. Type 3. Post | Nested reply shown under parent |
| TRANS-11 | Multiple translators per section | 1. Set translator count to 2 2. Two translators each translate same section | Both saved. Section complete only after N submissions. |
| TRANS-12 | See own pending translation | 1. Submit translation 2. Re-open section | "My previous submission" panel shows own pending translation. Edit allowed. |
| TRANS-13 | Cannot see others' pending translations | 1. Translator A submits 2. Translator B opens same section | Translator B does not see Translator A's pending translation |
| TRANS-14 | See others' approved translation | 1. Editor approves A's translation 2. Translator B reopens section | Translator B sees A's approved translation and can comment |

### 6. Book Organization & Publishing

| TC-ID | Scenario | Steps | Expected Result |
|-------|----------|-------|-----------------|
| ORG-01 | Reorder pages | 1. Drag page in list to new position | Page order updated |
| ORG-02 | Delete page | 1. Click delete on page 2. Confirm | Page removed. Sections cascade deleted. |
| ORG-03 | Filter by status | 1. Click "Completed" filter | Only completed pages shown |
| ORG-04 | Sort by progress | 1. Select sort by "Progress %" | Pages sorted ascending/descending |
| ORG-05 | Review translations | 1. Open section with translations 2. View side-by-side | All N translations shown with translator info. Exact letter field shown if provided. |
| ORG-06 | Approve multiple translations | 1. Click "Approve" on Translation A 2. Click "Approve" on Translation B | Both marked approved with star badges |
| ORG-07 | Reject a translation | 1. Click "Reject" on a translation | Translation marked with strikethrough + "Rejected" badge |
| ORG-08 | Reject all translations | 1. Click "Reject All" | Section re-enters translation pool. Message: "All translations rejected. Translators will need to resubmit." |
| ORG-09 | Editor override translation | 1. Type own translation 2. Click "Write your own" | Editor's version saved as approved translation |
| ORG-10 | Resubmit after rejection | 1. Editor rejects all 2. Translator opens section again | Section appears in queue for re-translation |
| ORG-11 | Build finalized book | 1. Click "Build" 2. Wait for processing | Book build status: BUILDING → COMPLETED. Download link appears. |
| ORG-12 | Download finalized book | 1. Click Download | PDF downloaded using original page numbers for labels |
| ORG-13 | Rebuild book | 1. Make changes 2. Click "Build" again | New PDF overwrites previous in S3 |

### 7. Team Management

| TC-ID | Scenario | Steps | Expected Result |
|-------|----------|-------|-----------------|
| TEAM-01 | Invite translator | 1. Search user by email 2. Send invite | User appears in invited list with PENDING status |
| TEAM-02 | Accept invitation | 1. Login as invited user 2. Navigate to books | Book appears in "Assigned to me" |
| TEAM-03 | Block translator | 1. Click "Block" on translator | Translator removed from book access. Existing translations preserved. |
| TEAM-04 | Unblock translator | 1. Click "Unblock" | Translator regains access to book |

### 8. Edge Cases & Error Handling

| TC-ID | Scenario | Steps | Expected Result |
|-------|----------|-------|-----------------|
| EDGE-01 | Concurrent translation save | 2 translators save same section simultaneously | No data loss. Both saves succeed. |
| EDGE-02 | Network failure during upload | 1. Upload file 2. Disconnect network mid-upload | Upload fails. User can retry from where it left off. |
| EDGE-03 | Browser tab close during section editing | 1. Edit sections 2. Close tab without confirming | Changes not saved. User warned before close (beforeunload). |
| EDGE-04 | Empty book (0 pages) | 1. Upload empty PDF | Error: "Book has no pages" |
| EDGE-05 | Very large page count (10000+) | 1. Upload 10000+ page book | Pages process asynchronously. Paginated page list. |
| EDGE-06 | Section with no text detected | 1. Blank page image 2. Detect sections | No sections found. "No sections detected" message. |
| EDGE-07 | MongoDB connection failure | 1. Stop MongoDB 2. Try to upload book | Graceful error: "Database connection failed. Please try again." |
| EDGE-08 | Section crop failure | 1. Confirm sections with invalid coordinates 2. Wait for crop task | Error logged. Section remains without cropped image. Retry option. |

## Regression Checklist

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
