# Maha Pothana — Actors & Permissions

## Roles

| Role            | Description                                                                                            |
| --------------- | ------------------------------------------------------------------------------------------------------ |
| **Super Admin** | Full system access. Can modify any user's roles and permissions.                                       |
| **Editor**      | Can add books, manage pages/sections, assign translators, approve translations, build finalized books. |
| **Translator**  | Can view assigned sections, provide translations, add comments.                                        |
| **AI Agent**    | System-initiated role. Runs background tasks: text extraction, transliteration, auto-translation.      |

## Permissions Matrix

| Feature                                                   | Super Admin | Editor | Translator |
| --------------------------------------------------------- | :---------: | :----: | :--------: |
| Manage users & roles                                      |     ✅      |   ❌   |     ❌     |
| Upload books                                              |     ✅      |   ✅   |     ❌     |
| View book list                                            |     ✅      |   ✅   |     ✅     |
| Process pages (section detection)                         |     ✅      |   ✅   |     ❌     |
| View detected sections on canvas                          |     ✅      |   ✅   |     ❌     |
| Modify sections (drag/resize)                             |     ✅      |   ✅   |     ❌     |
| Delete sections                                           |     ✅      |   ✅   |     ❌     |
| Add new sections (draw tool)                              |     ✅      |   ✅   |     ❌     |
| Change section type                                       |     ✅      |   ✅   |     ❌     |
| Zoom in/out on page canvas                                |     ✅      |   ✅   |     ✅     |
| Undo/redo section edits                                   |     ✅      |   ✅   |     ❌     |
| Confirm & save sections                                   |     ✅      |   ✅   |     ❌     |
| Re-detect sections (re-run detection)                     |     ✅      |   ✅   |     ❌     |
| Translate sections                                        |     ✅      |   ❌   |     ✅     |
| View translation UI                                       |     ✅      |   ✅   |     ✅     |
| Approve/reject translations                               |     ✅      |   ✅   |     ❌     |
| Provide own translation (override)                        |     ✅      |   ✅   |     ❌     |
| Set translators per book                                  |     ✅      |   ✅   |     ❌     |
| Build finalized book                                      |     ✅      |   ✅   |     ❌     |
| Invite users to book                                      |     ✅      |   ✅   |     ❌     |
| Block translators from book                               |     ✅      |   ✅   |     ❌     |
| Add translator comments                                   |     ✅      |   ✅   |     ✅     |
| View translation history                                  |     ✅      |   ✅   |     ✅     |
| View translation statistics                               |     ✅      |   ✅   |     ❌     |
| View translator performance stats                         |     ✅      |   ✅   |     ❌     |
| Filter translations by language/page                      |     ✅      |   ✅   |     ✅     |
| **Filter & sort translation progress**                    |     ✅      |   ✅   |     ❌     |
| **Organize pages (reorder, add, delete)**                 |     ✅      |   ✅   |     ❌     |
| **Review translations (approve/reject, editor override)** |     ✅      |   ✅   |     ❌     |
| **Download finalized book**                               |     ✅      |   ✅   |     ✅     |
| Trigger AI text extraction                                |     ✅      |   ✅   |     ❌     |
| View AI extraction confidence score                       |     ✅      |   ✅   |     ✅     |
| Regenerate AI transliteration                             |     ✅      |   ✅   |     ❌     |

## Notes

- Every user is automatically assigned both **Editor** and **Translator** roles on signup
- Super Admin can later revoke or modify roles per user
- Editors can only manage books they own or are assigned to
- The page canvas editor (Konva-based) is available only to Editors and Super Admins
- Translators can view the page canvas only in read-only context (page context toggle in translation UI)
- "Download finalized book" is available to Translators so they can access the final published output
