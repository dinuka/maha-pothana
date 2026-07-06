# Translation Page Redesign — QA Test Plan

**Date:** 2026-07-06 12:00
**Author:** QA Agent
**Related BA:** `specs/business-analysis/20260706-1200-translation-page-redesign.md`
**Related Architecture:** `specs/architecture/20260706-1200-translation-page-redesign.md`
**Related UX:** `specs/ux/20260706-1200-translation-page-redesign.md`

---

## 1. Scope

This test plan covers the Translation Page Redesign feature: six user stories (US-TR-1 through US-TR-6) that transform the minimal `/translate` page into a full-featured translation console with history, statistics, filtering, source text side-by-side, and auto-save drafts.

---

## 2. Test Environment Setup

### Prerequisites

- MongoDB running locally or in Docker (`docker compose -f infra/docker-compose.dev.yml up -d`)
- Redis running for caching and Celery
- MinIO running for S3 file storage
- LibreTranslate running for auto-translation
- Next.js dev server on port 3000 (`pnpm dev`)
- FastAPI dev server on port 8000 (`cd apps/api && uvicorn app.main:app --reload`)
- Test user accounts: one Editor, one Translator, one Super Admin
- A book with sections already uploaded, processed, and section-detected

### Test Data Requirements

| Data | Purpose | Setup |
| --- | --- | --- |
| Book with 10+ pages, 50+ sections | History, stats, filters | Upload PDF, run detection, confirm sections |
| 2 target languages (si, ta) | Language filter, per-language stats | Set `translateLanguages: ["si", "ta"]` on book |
| 3+ translators with submissions | Translator stats, history | Create translations via API or UI |
| Mix of approved/rejected/pending translations | Status filters, stats accuracy | Approve some, reject some via editor UI |
| Draft in TranslationDrafts collection | Draft load, expiry | POST to `/api/translations/draft` |
| Empty book (0 sections) | Edge case | Upload book, skip section detection |
| Book with all sections translated | Empty state edge case | Translate all sections |

### Test User Accounts

| User | Role | Purpose |
| --- | --- | --- |
| editor@test.com | EDITOR | Stats tab, approve/reject, translator stats |
| translator-a@test.com | TRANSLATOR | History, draft, translate |
| translator-b@test.com | TRANSLATOR | History isolation, concurrent drafts |
| admin@test.com | SUPER_ADMIN | Full access to all features |

---

## 3. US-TR-1: Translation History

### 3.1 History Tab Rendering

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR1-01 | History tab visible | 1. Login as translator 2. Navigate to `/translate` | Three tabs visible: Translate, History, Stats (Stats hidden for translator) |
| TR1-02 | History tab loads on click | 1. Click "History" tab | History list loads with translations sorted by most recent first |
| TR1-03 | History item displays correctly | 1. Click History tab 2. Inspect first item | Shows: section thumbnail, page number, section order, translated text snippet (≤80 chars), status badge, timestamp |
| TR1-04 | Status badges correct colors | 1. View history items | APPROVED = green pill, REJECTED = red pill, PENDING = amber pill |
| TR1-05 | Status badges include icons | 1. View history items | APPROVED shows checkmark, PENDING shows clock, REJECTED shows X |
| TR1-06 | Translated text truncated at 80 chars | 1. View item with long translation | Text snippet shows first 80 chars + ellipsis if longer |

### 3.2 History Pagination / Infinite Scroll

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR1-07 | Initial page loads 20 items | 1. Open History tab 2. Count items | 20 items displayed (or fewer if less exist) |
| TR1-08 | Scroll triggers next page | 1. Scroll to bottom of history list | Loading indicator appears, next batch of items appended |
| TR1-09 | Cursor-based pagination works | 1. Scroll through 3 pages of history | Items are contiguous, no duplicates, no gaps |
| TR1-10 | End of history reached | 1. Scroll through all history items | "End of history" message or spinner disappears, no more fetches |
| TR1-11 | Loading indicator during fetch | 1. Scroll to trigger next page | Bouncing dots or spinner shown at bottom of list while loading |
| TR1-12 | Empty history shows empty state | 1. Login as translator with no submissions 2. Click History | "No translations yet — start translating!" with link to Translate tab |

### 3.3 History Item Interaction

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR1-13 | Click history item navigates | 1. Click a history item | Navigates to `/translate?section={sectionId}` with that section loaded |
| TR1-14 | Click history item loads section | 1. Click an APPROVED history item | Section image and approved translation displayed |
| TR1-15 | History item shows reviewer name | 1. View APPROVED/REJECTED item | Shows "Reviewed by {editorName}" beneath status badge |
| TR1-16 | History item shows translator name (editor view) | 1. Login as editor 2. View history | Each item shows translator name |

### 3.4 History Role-Based Access

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR1-17 | Translator sees own history only | 1. Login as translator-a 2. Open History | Only translator-a's translations shown |
| TR1-18 | Editor sees all translations | 1. Login as editor 2. Open History | All translators' translations shown |
| TR1-19 | Translator cannot filter by other translator | 1. Login as translator-a 2. Attempt to add `translatorId` param for translator-b | API returns 403 or ignores param, still shows only own history |

### 3.5 History Empty and Error States

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR1-20 | Empty state — no translations | 1. Book with sections but no translations 2. Open History | Empty state with illustration, message, and "Start Translating" CTA |
| TR1-21 | Empty state — filters exclude all | 1. Set filters to language that has no translations | Empty state: "No translations match your filters" with "Clear Filters" button |
| TR1-22 | Error state — API failure | 1. Mock API to return 500 2. Open History | "Failed to load history. [Retry]" message |
| TR1-23 | Error state — network failure | 1. Disconnect network 2. Open History | Graceful error with retry option |

### 3.6 History Real-Time Updates

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR1-24 | Badge updates on approve | 1. Translator submits (PENDING) 2. Editor approves 3. Translator views History | Badge changes from PENDING to APPROVED without manual refresh |
| TR1-25 | Badge updates on reject | 1. Translator submits (PENDING) 2. Editor rejects 3. Translator views History | Badge changes from PENDING to REJECTED |
| TR1-26 | React Query refetch on focus | 1. Open History 2. Switch to another tab 3. Switch back | Data refetched automatically (stale-while-revalidate) |

---

## 4. US-TR-2: Book Stats Dashboard

### 4.1 Stats Tab Visibility

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR2-01 | Stats tab visible to editors | 1. Login as editor 2. Navigate to `/translate` | Stats tab visible in tab bar |
| TR2-02 | Stats tab hidden from translators | 1. Login as translator 2. Navigate to `/translate` | Stats tab NOT visible in tab bar |
| TR2-03 | Stats tab visible to super admin | 1. Login as super admin 2. Navigate to `/translate` | Stats tab visible |

### 4.2 Stats Card Rendering

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR2-04 | Stats tab loads on click | 1. Login as editor 2. Click Stats tab | Stats dashboard loads with progress bar and numbers |
| TR2-05 | Total sections correct | 1. View stats card | `totalSections` matches actual section count for the book |
| TR2-06 | Translated sections correct | 1. View stats card | `translatedSections` matches sections with at least one approved translation |
| TR2-07 | Pending sections correct | 1. View stats card | `pendingSections` matches sections with no approved translation |
| TR2-08 | In-progress sections correct | 1. View stats card | `inProgressSections` matches sections with submitted but unapproved translations |
| TR2-09 | Translation percent correct | 1. View stats card | Percentage = `translatedSections / totalSections * 100` |
| TR2-10 | Progress bar visual matches data | 1. View progress bar | Bar fill width matches the percentage shown |
| TR2-11 | Progress bar animated on load | 1. Click Stats tab | Bar fills with 600ms ease-out animation |

### 4.3 Per-Language Breakdown

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR2-12 | Per-language cards render | 1. Book with 2 target languages 2. View Stats | Two language cards shown (Sinhala, Tamil) |
| TR2-13 | Per-language stats correct | 1. View language card | Each card shows correct total, translated, percent for that language |
| TR2-14 | Single language — no breakdown | 1. Book with 1 target language 2. View Stats | Language breakdown section hidden or shows single card |

### 4.4 Per-Page Breakdown

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR2-15 | Page grid renders | 1. View Stats tab | Grid shows one cell per page with color coding |
| TR2-16 | Green cells = 100% translated | 1. View page grid | Pages with all sections approved show green |
| TR2-17 | Yellow cells = partially translated | 1. View page grid | Pages with some (not all) sections approved show yellow |
| TR2-18 | Gray cells = not started | 1. View page grid | Pages with no translations show gray |
| TR2-19 | Percentage shown below cells | 1. View page grid | Each cell shows percentage text below the color indicator |
| TR2-20 | Click page cell filters history | 1. Click a page cell in grid | History tab opens with page filter applied |

### 4.5 Stats Refresh

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR2-21 | Stats refresh every 30s | 1. Open Stats tab 2. Submit a translation from another tab 3. Wait 30s | Stats update automatically without manual refresh |
| TR2-22 | React Query staleTime works | 1. Open Stats 2. Wait 15s 3. Switch tab and back | Data is still from cache (not refetched, less than 30s) |
| TR2-23 | Stats tab focused refetch | 1. Open Stats 2. Switch to Translate tab 3. Editor approves translation 4. Switch back to Stats | Data refetched on tab focus |

### 4.6 Stats Caching

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR2-24 | Redis cache populated | 1. GET `/api/books/{id}/stats` 2. Check Redis | Key `stats:book:{bookId}` exists with 30s TTL |
| TR2-25 | Cache hit on second request | 1. GET stats 2. GET stats again within 30s | Second request served from cache (check response time or Redis logs) |
| TR2-26 | Cache invalidated on translation | 1. GET stats 2. Submit translation 3. GET stats | Cache miss — fresh aggregation performed |

### 4.7 Stats Empty and Error States

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR2-27 | Empty book stats | 1. Book with 0 sections 2. View Stats | Shows 0/0 with 0% progress, or "No sections to translate" message |
| TR2-28 | No translations yet | 1. Book with sections, no translations 2. View Stats | Shows 0% translated, all sections pending |
| TR2-29 | Error state | 1. Mock API to return 500 2. Open Stats | "Failed to load statistics. [Retry]" message |

---

## 5. US-TR-3: Translator Performance Stats

### 5.1 Translator Stats Table

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR3-01 | Translator table renders | 1. Login as editor 2. Open Stats tab | Translator performance table visible below page breakdown |
| TR3-02 | Table shows correct columns | 1. Inspect table headers | Columns: Name, Assigned, Approved, Rejected, Rate, Avg Time |
| TR3-03 | Default sort by approval rate | 1. View table | Rows sorted by approval rate descending (highest first) |
| TR3-04 | Click column header sorts | 1. Click "Name" header | Table sorts alphabetically by name. Click again = reverse sort |
| TR3-05 | Click any column sorts | 1. Click "Assigned", "Approved", "Rejected", "Rate", "Avg Time" | Each column sorts ascending/descending on click |
| TR3-06 | Sort indicator visible | 1. Click a column header | Arrow or indicator shows sort direction |

### 5.2 Translator Stats Accuracy

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR3-07 | totalAssigned correct | 1. View translator row | Matches number of sections translator has worked on |
| TR3-08 | approvedCount correct | 1. View translator row | Matches number of translations with `isApproved = true` |
| TR3-09 | rejectedCount correct | 1. View translator row | Matches number of translations rejected |
| TR3-10 | pendingCount correct | 1. View translator row | Matches translations awaiting review |
| TR3-11 | approvalRate correct | 1. View translator row | = `approved / (approved + rejected) * 100`, rounded to 1 decimal |
| TR3-12 | avgTurnaroundHours correct | 1. View translator row | = average of (translation.createdAt - section.createdAt) for approved translations |
| TR3-13 | lastActiveAt correct | 1. View translator row | Shows ISO timestamp of most recent translation |

### 5.3 Translator Zero-Submission Edge Case

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR3-14 | Zero submissions shows "No activity" | 1. Translator assigned but no submissions 2. View Stats | Row shows "—" for all metrics, or "No activity" label |
| TR3-15 | Zero approved AND rejected shows null rate | 1. Translator with only pending submissions 2. View Stats | Approval rate shows "—" not 0% or NaN |

### 5.4 Translator Row Expand

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR3-16 | Click row expands activity | 1. Click translator row | Row expands to show last 10 translation submissions |
| TR3-17 | Expanded activity shows details | 1. View expanded row | Each entry shows: status icon, page/section, text snippet, timestamp |
| TR3-18 | Click row again collapses | 1. Click expanded row | Row collapses back to summary |
| TR3-19 | Expand animation smooth | 1. Click row to expand | 300ms height animation with content fade-in |

### 5.5 Translator Stats Role-Based Access

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR3-20 | Translator cannot see other translators' stats | 1. Login as translator 2. Attempt to access `/api/books/{id}/translators/stats` | API returns 403 Forbidden |
| TR3-21 | Translator cannot see Stats tab | 1. Login as translator 2. Navigate to `/translate` | Stats tab not visible in tab bar |
| TR3-22 | Editor sees all translators | 1. Login as editor 2. View Stats | All translators for the book shown |

---

## 6. US-TR-4: Filters

### 6.1 Filter Controls Rendering

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR4-01 | Filter bar visible on Translate tab | 1. Open `/translate` | Filter controls visible above tab bar |
| TR4-02 | Language dropdown populated | 1. View filter bar | Dropdown shows all `translateLanguages` from the book |
| TR4-03 | Language filter hidden for single language | 1. Book with 1 target language 2. View filters | Language dropdown not shown |
| TR4-04 | Page filter populated | 1. View filter bar | Page dropdown shows "All" + list of page numbers |
| TR4-05 | Status filter options | 1. View filter bar | Status dropdown shows: ALL, PENDING, APPROVED, REJECTED |
| TR4-06 | Clear filters button visible | 1. View filter bar | "Clear" button visible (may be disabled if all defaults) |

### 6.2 Filter Application

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR4-07 | Language filter applies immediately | 1. Select "Sinhala" from language dropdown | Next section fetched with `language=si` param |
| TR4-08 | Page filter applies immediately | 1. Select page 5 from dropdown | Next section fetched with `page=5` param |
| TR4-09 | Status filter applies immediately | 1. Select "APPROVED" from status dropdown | Next section fetched with `status=approved` param |
| TR4-10 | Filters compose (AND logic) | 1. Select language=si, page=3, status=PENDING | API called with all three params, only matching sections returned |

### 6.3 URL Param Persistence

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR4-11 | Filters persist in URL | 1. Select lang=si, page=3 2. Check URL bar | URL shows `?lang=si&page=3` |
| TR4-12 | URL params survive page reload | 1. Set filters 2. Reload page | Filters restored from URL, same sections shown |
| TR4-13 | Filters are shareable | 1. Copy URL with filters 2. Open in new browser/tab | Filters applied, same view shown |
| TR4-14 | Tab param independent | 1. Set filters on Translate tab 2. Switch to History tab | History tab has its own filter state |

### 6.4 Clear Filters

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR4-15 | Clear filters resets to defaults | 1. Set lang=si, page=3, status=PENDING 2. Click Clear | All filters reset to "All", URL params cleared |
| TR4-16 | Clear button disabled when defaults | 1. All filters at default 2. Inspect Clear button | Button is disabled or hidden |

### 6.5 Filters on History Tab

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR4-17 | History tab has independent filters | 1. Set lang=si on Translate 2. Switch to History 3. Set lang=ta | History shows ta results, Translate still has si filter |
| TR4-18 | History filters affect history results | 1. On History tab, set status=APPROVED | Only approved translations shown |
| TR4-19 | History filters persist in URL | 1. Set filters on History tab 2. Check URL | URL shows `?tab=history&lang=ta&status=approved` |

### 6.6 Filter Edge Cases

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR4-20 | No sections match filters | 1. Set filters that match nothing 2. Click Next | Empty state: "No sections match your filters" with Clear Filters CTA |
| TR4-21 | Book changes reset filters | 1. Set filters on Book A 2. Switch to Book B | Filters reset to defaults for new book |
| TR4-22 | Invalid URL params handled | 1. Navigate to `?lang=xyz&page=-1` | Invalid params ignored, defaults used, no crash |

---

## 7. US-TR-5: Source Text Side-by-Side

### 7.1 Source Text Panel

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR5-01 | Source text panel visible | 1. Open Translate tab with section loaded | Left column: section image. Right column: source text panel + translation editor |
| TR5-02 | Source text labeled "Source Text" | 1. Inspect source text panel | Header shows "Source Text" with document icon |
| TR5-03 | Original text displayed | 1. Section has `originalText` populated | Text shown in read-only panel with gray background |
| TR5-04 | Source text is read-only | 1. Try to click/type in source text panel | No cursor, no editing possible |
| TR5-05 | Source text above or below image | 1. View source text panel | Original text positioned logically (above editor, below section image) |

### 7.2 Missing Original Text Fallback

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR5-06 | Empty originalText fallback | 1. Section with empty `originalText` 2. Open Translate | Message: "Original text not available — use the image above" |
| TR5-07 | Section image still visible with no text | 1. Same as above | Cropped section image still displayed in left column |
| TR5-08 | Null originalText fallback | 1. Section with `originalText: null` 2. Open Translate | Same fallback message shown |

### 7.3 Side-by-Side Layout

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR5-09 | Desktop layout side-by-side | 1. View on >1024px viewport | Two-column layout: image+source left, editor right |
| TR5-10 | Tablet layout collapsible | 1. View on 768–1024px viewport | Side-by-side with collapsible image panel |
| TR5-11 | Mobile layout stacked | 1. View on <768px viewport | Stacked: image on top, source text, then translation editor |
| TR5-12 | Section image zoomable | 1. Click +/- zoom buttons below image | Image scales 50%–300%, zoom % displayed |
| TR5-13 | Auto-translated text prefills editor | 1. Section with auto-translation from LibreTranslate | Translation textarea pre-filled with auto-translated text |

### 7.4 Editor Role — Edit Original Text Link

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR5-14 | Editor sees "Edit original text" link | 1. Login as editor 2. Open Translate tab | Link visible below source text panel |
| TR5-15 | Link navigates to page editor | 1. Click "Edit original text" link | Navigates to `/books/{bookId}/pages/{pageNum}` |
| TR5-16 | Translator does not see edit link | 1. Login as translator 2. Open Translate tab | "Edit original text" link NOT visible |

---

## 8. US-TR-6: Auto-save Drafts

### 8.1 Draft Auto-Save Behavior

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR6-01 | Draft saves after 5s inactivity | 1. Type in translation textarea 2. Stop typing 3. Wait 5s | "Draft saved ✓" indicator appears briefly |
| TR6-02 | Draft does not save empty text | 1. Clear textarea 2. Wait 5s | No draft saved (empty text skipped) |
| TR6-03 | Draft debounce resets on typing | 1. Type 2. Wait 3s 3. Type again 4. Wait 5s | Draft saves only after final 5s of inactivity |
| TR6-04 | Draft indicator auto-dismisses | 1. Wait for draft save | "Draft saved ✓" appears, then fades out after ~2s |

### 8.2 Draft Load on Section Change

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR6-05 | Draft prefills textarea on load | 1. Save draft for section A 2. Navigate away 3. Return to section A | Translation textarea prefilled with draft text |
| TR6-06 | Draft loaded before auto-translation | 1. Section with auto-translation AND existing draft | Draft text takes priority over auto-translation |
| TR6-07 | No draft uses auto-translation | 1. Section with no draft 2. Auto-translation exists | Translation textarea prefilled with auto-translation |

### 8.3 Draft Delete on Submit

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR6-08 | Draft deleted after submission | 1. Save draft 2. Submit translation | Draft deleted from TranslationDrafts collection |
| TR6-09 | Draft not created if already translated | 1. Section already translated by this translator 2. Open section | No draft created, redirect to history or show existing translation |

### 8.4 Beforeunload Warning

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR6-10 | Unsaved changes warning | 1. Type translation 2. Try to close tab | Browser shows "You have unsaved changes" confirmation |
| TR6-11 | No warning when clean | 1. Open section 2. Don't type 3. Try to close tab | No warning shown |
| TR6-12 | No warning after draft saved | 1. Type 2. Wait for draft save 3. Close tab | No warning (draft is saved) |

### 8.5 Draft Expiry

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR6-13 | Draft expires after 24h | 1. Create draft 2. Manually set `createdAt` to 25h ago 3. GET draft | 404 — draft not found |
| TR6-14 | TTL index on translation_drafts | 1. Check MongoDB indexes on `translation_drafts` | TTL index on `createdAt` with expireAfterSeconds: 86400 |

### 8.6 Draft Isolation

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR6-15 | Drafts per-translator per-section | 1. Translator A saves draft for section X 2. Translator B opens section X | Translator B does NOT see Translator A's draft |
| TR6-16 | Unique compound index | 1. Check MongoDB indexes | Compound unique index on `{ sectionId: 1, translatorId: 1 }` |

### 8.7 Draft API Endpoints

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR6-17 | POST /api/translations/draft creates draft | 1. POST with `{ sectionId, translatedText }` | 200: `{ draftId, updatedAt }` |
| TR6-18 | POST /api/translations/draft upserts | 1. POST draft 2. POST again with same sectionId + different text | Draft updated, same draftId returned |
| TR6-19 | GET /api/translations/draft returns draft | 1. GET with `?sectionId=X` | 200: `{ draftId, translatedText, updatedAt }` |
| TR6-20 | GET /api/translations/draft — no draft | 1. GET with `?sectionId=nonexistent` | 404: `{ "detail": "No draft found" }` |
| TR6-21 | DELETE /api/translations/draft/{id} deletes | 1. DELETE a draft | 200: `{ "status": "deleted" }` |
| TR6-22 | DELETE /api/translations/draft/{id} — not found | 1. DELETE nonexistent draft | 404: `{ "detail": "Draft not found" }` |

### 8.8 Draft localStorage Fallback

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TR6-23 | localStorage fallback when API slow | 1. Mock draft API to delay 10s 2. Type translation | Draft saved to localStorage immediately, API call in background |
| TR6-24 | localStorage draft loaded on mount | 1. Save to localStorage 2. Reload page | Draft loaded from localStorage if API unavailable |

---

## 9. Backend API Test Cases

### 9.1 GET /api/books/{bookId}/stats

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| API-01 | Stats returns correct totals | 1. GET `/api/books/{id}/stats` with editor auth | `totalSections` = actual section count |
| API-02 | Stats by language correct | 1. GET stats for multi-language book | `byLanguage` object has correct keys and values |
| API-03 | Stats by page correct | 1. GET stats | `byPage` array has one entry per page with correct counts |
| API-04 | Stats cached in Redis | 1. GET stats 2. GET stats again | Second request served from cache |
| API-05 | Stats cache invalidated | 1. GET stats 2. Submit translation 3. GET stats | Fresh data returned |
| API-06 | Stats — 403 for translators | 1. GET stats with translator auth | 403 Forbidden |

### 9.2 GET /api/books/{bookId}/translators/stats

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| API-07 | Translator stats returns array | 1. GET `/api/books/{id}/translators/stats` | Returns array of translator stats objects |
| API-08 | Approval rate calculated correctly | 1. GET translator stats | `approvalRate = approved / (approved + rejected) * 100` |
| API-09 | Avg turnaround calculated | 1. GET translator stats | `avgTurnaroundHours` = avg(submitTime - sectionCreationTime) |
| API-10 | Zero submissions handled | 1. Translator with no submissions 2. GET stats | Shows zero counts, null rate, null turnaround |
| API-11 | Stats scoped to book | 1. GET stats for book A | Only translations from book A included |
| API-12 | 403 for translators | 1. GET with translator auth | 403 Forbidden |

### 9.3 GET /api/translations/history

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| API-13 | History returns paginated results | 1. GET `/api/translations/history?bookId=X&limit=20` | Returns `{ items: [...], nextCursor, hasMore }` |
| API-14 | History cursor pagination | 1. GET with cursor from first response | Returns next batch, no duplicates |
| API-15 | History filtered by translator | 1. GET with `translatorId=Y` | Only translator Y's translations returned |
| API-16 | History filtered by status | 1. GET with `status=approved` | Only approved translations returned |
| API-17 | History filtered by page | 1. GET with `page=3` | Only translations from page 3 returned |
| API-18 | History filtered by language | 1. GET with `language=si` | Only Sinhala translations returned |
| API-19 | History filters compose | 1. GET with multiple filters | All filters applied (AND logic) |
| API-20 | History — translator sees own only | 1. GET as translator without `translatorId` | Automatically scoped to authenticated user |
| API-21 | History — editor sees all | 1. GET as editor | All translations returned |
| API-22 | History limit max 50 | 1. GET with `limit=100` | Capped at 50 items |
| API-23 | History empty result | 1. GET with filters matching nothing | `{ items: [], nextCursor: null, hasMore: false }` |

### 9.4 Draft API Endpoints

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| API-24 | POST draft — create new | 1. POST `{ sectionId, translatedText }` | 200: `{ draftId, updatedAt }` |
| API-25 | POST draft — upsert existing | 1. POST draft 2. POST again same sectionId | Draft updated, same draftId |
| API-26 | POST draft — 422 invalid body | 1. POST without `sectionId` | 422 Validation Error |
| API-27 | GET draft — returns existing | 1. Create draft 2. GET `?sectionId=X` | Returns draft with text |
| API-28 | GET draft — 404 not found | 1. GET nonexistent section | 404: `{ "detail": "No draft found" }` |
| API-29 | DELETE draft — success | 1. Create draft 2. DELETE by draftId | 200: `{ "status": "deleted" }` |
| API-30 | DELETE draft — 404 not found | 1. DELETE nonexistent draftId | 404: `{ "detail": "Draft not found" }` |
| API-31 | Draft — 403 unauthorized | 1. POST draft without auth token | 401/403 Unauthorized |

### 9.5 Updated GET /api/sections/next

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| API-32 | Sections/next with bookId filter | 1. GET `/api/sections/next?bookId=X` | Only sections from book X returned |
| API-33 | Sections/next with language filter | 1. GET with `language=si` | Only sections from book with si in translateLanguages |
| API-34 | Sections/next with page filter | 1. GET with `page=3` | Only sections from page 3 |
| API-35 | Sections/next with status filter | 1. GET with `status=pending` | Only sections with no translation |
| API-36 | Sections/next filters compose | 1. GET with multiple filters | All filters applied |
| API-37 | Sections/next — 404 no results | 1. GET with filters matching nothing | 404: `{ "detail": "No sections available" }` |

---

## 10. Frontend Component Test Cases

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| FE-01 | TranslatePage renders tab bar | 1. Render `<TranslatePage>` | Tab bar with Translate, History, Stats tabs rendered |
| FE-02 | TranslatePage default tab is Translate | 1. Render without `?tab=` param | Translate tab active by default |
| FE-03 | Tab switch updates URL | 1. Click History tab | URL updated to `?tab=history` |
| FE-04 | TranslateFilters renders all controls | 1. Render `<TranslateFilters>` with multi-language book | Language dropdown, page dropdown, status dropdown, clear button |
| FE-05 | TranslateFilters hides language for single lang | 1. Render with single language book | Language dropdown hidden |
| FE-06 | Filter change calls onChange | 1. Select language "si" | onChange called with `{ language: "si" }` |
| FE-07 | Clear filters resets state | 1. Set filters 2. Click Clear | All filters reset to defaults |
| FE-08 | HistoryTab renders history items | 1. Render with mock data | HistoryItem components rendered for each item |
| FE-09 | HistoryTab shows empty state | 1. Render with empty items array | Empty state with message and CTA |
| FE-10 | HistoryTab triggers infinite scroll | 1. Render with hasMore=true 2. Scroll to bottom | onScrollEnd callback fired |
| FE-11 | StatsTab renders progress bar | 1. Render with stats data | Progress bar with correct percentage |
| FE-12 | StatsTab renders language cards | 1. Render with multi-language stats | Language breakdown cards displayed |
| FE-13 | StatsTab renders page grid | 1. Render with page stats | Color-coded grid cells rendered |
| FE-14 | StatsTab renders translator table | 1. Render with translator stats | Table rows with correct data |
| FE-15 | StatsTab hides from non-editors | 1. Render with `userRole="TRANSLATOR"` | Stats tab not rendered |
| FE-16 | SourceTextPanel shows text | 1. Render with `originalText` | Text displayed in read-only panel |
| FE-17 | SourceTextPanel shows fallback | 1. Render with empty `originalText` | Fallback message displayed |
| FE-18 | useTranslationDraft hook saves draft | 1. Call `saveDraft` with text | POST /api/translations/draft called after debounce |
| FE-19 | useTranslationDraft hook loads draft | 1. Call with sectionId that has draft | Draft text loaded and returned |
| FE-20 | useTranslationDraft beforeunload | 1. Set isDirty=true 2. Trigger beforeunload | Event prevented, warning shown |

---

## 11. Integration / E2E Test Cases

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| E2E-01 | Full translation flow | 1. Login as translator 2. Open `/translate` 3. Auto-load section 4. Type translation 5. Submit | Section translated, next section loaded, history updated |
| E2E-02 | Translation with draft recovery | 1. Type translation 2. Wait for draft save 3. Close tab 4. Reopen | Draft loaded, textarea prefilled |
| E2E-03 | Editor approves → stats update | 1. Editor approves translation 2. View Stats tab | Approved count increments, progress bar updates |
| E2E-04 | Filter → next section → translate | 1. Set language=si, page=3 2. Click Next 3. Translate | Only Sinhala section from page 3 loaded, translated |
| E2E-05 | History → click item → view section | 1. Open History 2. Click an item | Section loaded in Translate tab with existing translation |
| E2E-06 | Stats → click page cell → history filtered | 1. Open Stats 2. Click page 5 cell | History tab opens with page=5 filter applied |
| E2E-07 | Stats → click translator → expand | 1. Open Stats 2. Click translator row | Row expands showing recent activity |
| E2E-08 | Concurrent translators — isolated drafts | 1. Translator A saves draft 2. Translator B opens same section | B does NOT see A's draft |
| E2E-09 | Auto-load → draft → submit → next | 1. Open `/translate` 2. Section auto-loads 3. Draft prefills 4. Edit 5. Submit | Draft deleted, next section auto-loads |
| E2E-10 | Mobile responsive — translate flow | 1. View on mobile viewport 2. Translate section | Stacked layout, all features functional |
| E2E-11 | Mobile responsive — history | 1. View on mobile 2. Open History | Card layout, infinite scroll works |
| E2E-12 | Mobile responsive — stats | 1. View on mobile 2. Open Stats | Single-column layout, all data visible |

---

## 12. Edge Cases and Error Handling

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| EDGE-TR-01 | Empty book (no sections) | 1. Book with 0 sections 2. Open `/translate` | Empty state: "No sections available" |
| EDGE-TR-02 | All sections translated | 1. All sections have approved translations 2. Open `/translate` | "All sections translated! Great work!" with link to History |
| EDGE-TR-03 | Concurrent auto-save and manual save | 1. Type translation 2. Immediately click Submit while auto-save in flight | Both requests succeed, no conflict, draft deleted |
| EDGE-TR-04 | Redis cache miss | 1. Flush Redis 2. GET stats | Fresh aggregation performed, result cached |
| EDGE-TR-05 | Redis unavailable | 1. Stop Redis 2. GET stats | Stats returned without caching (or graceful error) |
| EDGE-TR-06 | Network failure during auto-save | 1. Type translation 2. Disconnect network 3. Wait 5s | Auto-save fails silently, retry on next attempt, localStorage fallback |
| EDGE-TR-07 | Large history dataset (1000+) | 1. Translator with 1000+ translations 2. Open History | Infinite scroll works smoothly, no performance degradation |
| EDGE-TR-08 | Book with 100+ pages | 1. Book with 100 pages 2. View Stats page grid | Grid horizontally scrollable, all pages shown |
| EDGE-TR-09 | Section with very long originalText | 1. Section with 5000+ char originalText 2. Open Translate | Source text panel scrollable, no layout breakage |
| EDGE-TR-10 | Draft with very long text | 1. Type 10000+ chars 2. Wait for auto-save | Draft saves successfully, no truncation |
| EDGE-TR-11 | Multiple tabs same translator | 1. Open `/translate` in two tabs 2. Type in both | Each tab maintains its own state, no cross-tab interference |
| EDGE-TR-12 | Browser back/forward navigation | 1. Set filters 2. Navigate away 3. Browser back | Filters restored from URL |
| EDGE-TR-13 | Stats with zero translators | 1. Book with no translators assigned 2. View Stats | Translator table empty or "No translators assigned" message |
| EDGE-TR-14 | Draft for section that gets deleted | 1. Save draft 2. Section deleted by editor 3. Open section | 404 or "Section not found" — draft orphaned (TTL cleans up) |
| EDGE-TR-15 | Translation submit while section already approved | 1. Translator opens section 2. Editor approves another translation 3. Translator submits | Conflict handled gracefully — reject with message or allow override per role |

---

## 13. Accessibility Test Cases

| TC-ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| A11Y-01 | Tab bar keyboard navigation | 1. Tab to tab bar 2. Use arrow keys | Focus moves between tabs, Enter/Space activates |
| A11Y-02 | Tab ARIA attributes | 1. Inspect tab bar HTML | `role="tablist"`, each tab has `role="tab"`, `aria-selected`, `aria-controls` |
| A11Y-03 | Tab panel ARIA attributes | 1. Inspect tab panel HTML | `role="tabpanel"` with `aria-labelledby` pointing to tab |
| A11Y-04 | Progress bar ARIA | 1. Inspect progress bar | `role="progressbar"`, `aria-valuenow`, `aria-valuemin`, `aria-valuemax` |
| A11Y-05 | Auto-save indicator live region | 1. Wait for draft save | "Draft saved" announced via `aria-live="polite"` |
| A11Y-06 | History items keyboard accessible | 1. Tab to history items 2. Press Enter | Item activated, navigates to section |
| A11Y-07 | Filter dropdowns labeled | 1. Inspect filter HTML | Each `<select>` has associated `<label>` |
| A11Y-08 | Status badges have aria-label | 1. Inspect badge HTML | `aria-label="Approved"` / `aria-label="Pending"` etc. |
| A11Y-09 | Page grid cells labeled | 1. Inspect grid cells | `aria-label="Page 1: 100% complete"` |
| A11Y-10 | Focus management on tab switch | 1. Switch tabs | Focus moves to new tab panel content |
| A11Y-11 | Screen reader announcements | 1. Use screen reader 2. Load section | "Section loaded: Page 3, Section 2" announced |
| A11Y-12 | Color contrast meets WCAG AA | 1. Check all text elements | 4.5:1 contrast ratio for normal text |

---

## 14. Test Execution Summary

| Category | Test Count | Status |
| --- | --- | --- |
| US-TR-1: Translation History | 26 | Pending |
| US-TR-2: Book Stats Dashboard | 29 | Pending |
| US-TR-3: Translator Performance | 22 | Pending |
| US-TR-4: Filters | 22 | Pending |
| US-TR-5: Source Text Side-by-Side | 16 | Pending |
| US-TR-6: Auto-save Drafts | 24 | Pending |
| Backend API Tests | 37 | Pending |
| Frontend Component Tests | 20 | Pending |
| Integration / E2E Tests | 12 | Pending |
| Edge Cases & Error Handling | 15 | Pending |
| Accessibility Tests | 12 | Pending |
| **Total** | **235** | **Pending** |

---

## 15. Related Files

- `specs/business-analysis/20260706-1200-translation-page-redesign.md` — User stories
- `specs/architecture/20260706-1200-translation-page-redesign.md` — API contracts
- `specs/ux/20260706-1200-translation-page-redesign.md` — UX interactions
- `specs/qa/test-plan.md` — Updated master test plan
