# Maha Pothana — Actors & Permissions

## Roles

| Role | Description |
|------|-------------|
| **Super Admin** | Full system access. Can modify any user's roles and permissions. |
| **Editor** | Can add books, manage pages/sections, assign translators, approve translations, build finalized books. |
| **Translator** | Can view assigned sections, provide translations, add comments. |

## Permissions Matrix

| Feature | Super Admin | Editor | Translator |
|---------|:-----------:|:------:|:----------:|
| Manage users & roles | ✅ | ❌ | ❌ |
| Upload books | ✅ | ✅ | ❌ |
| View book list | ✅ | ✅ | ✅ |
| Process pages (section detection) | ✅ | ✅ | ❌ |
| Modify sections (add/edit/delete) | ✅ | ✅ | ❌ |
| Translate sections | ✅ | ❌ | ✅ |
| View translation UI | ✅ | ✅ | ✅ |
| Approve/reject translations | ✅ | ✅ | ❌ |
| Provide own translation (override) | ✅ | ✅ | ❌ |
| Set translators per book | ✅ | ✅ | ❌ |
| Build finalized book | ✅ | ✅ | ❌ |
| Invite users to book | ✅ | ✅ | ❌ |
| Block translators from book | ✅ | ✅ | ❌ |
| Add translator comments | ✅ | ✅ | ✅ |

## Notes

- Every user is automatically assigned both **Editor** and **Translator** roles on signup
- Super Admin can later revoke or modify roles per user
- Editors can only manage books they own or are assigned to
