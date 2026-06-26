Here's a comprehensive tech stack recommendation for Maha Pothana, driven by the key requirements: large file handling (1GB+ books, 10,000+ pages), community-based translation, offline-first local setup, and free AI models.Here's the reasoning for each choice:

Need to use mono repo for this.

**Frontend — Next.js 14 + Konva.js + shadcn/ui**
Next.js handles SSR well for the book listing and auth flows, and its App Router makes role-based layouts (editor vs translator views) clean. Konva.js is the standout choice here — it's a canvas library built for interactive rectangle manipulation, making the drag/resize/delete section annotation editor straightforward to build. shadcn/ui gives polished, accessible components fast.

**Backend — FastAPI + Celery + Redis**
FastAPI is ideal because page splitting, AI translation, and book building are all long-running async tasks — Celery workers handle these in the background without blocking the API. For a 10,000-page book, you don't want these running in a request cycle. Redis doubles as the Celery broker and session cache.

**Auth — NextAuth.js**
Has first-class Google SSO support and JWT-based sessions. The RBAC (editor/translator/super-admin) maps cleanly onto its callbacks.

**AI / Document Processing**
This is the most spec-specific layer. PyMuPDF (fitz) is the fastest Python library for splitting large PDFs into page images. LayoutParser (built on Detectron2) handles automatic section detection — headers, paragraphs, footnotes — as annotated bounding boxes, which maps exactly to your editable rectangle requirement. LibreTranslate is a fully free, self-hostable translation engine, satisfying the "free online models for AI only" constraint.

**Storage — MinIO + PostgreSQL**
MinIO is an S3-compatible object store that runs locally in Docker — a direct drop-in for the S3 bucket requirement, so you can move to real AWS S3 in production with zero code changes. PostgreSQL holds all relational data (books, users, sections, translations, approvals).

**Infrastructure — Docker Compose + Nginx**
A single `docker-compose.yml` brings up the entire stack locally: Next.js, FastAPI, Celery workers, PostgreSQL, Redis, MinIO, LibreTranslate, and Nginx as the reverse proxy. This satisfies the offline-first requirement completely.

The one external dependency at dev time is Google OAuth credentials — everything else runs 100% locally.
