# maha-pothana

## Repo structure

```
apps/web      — Next.js App Router, port 3000
apps/api      — FastAPI + Celery backend, port 8000
infra/        — Docker Compose (dev + production), nginx config, Dockerfiles
packages/ui   — @repo/ui (shared React components, named exports via "./*" → "./src/*.tsx")
packages/eslint-config — @repo/eslint-config (flat config, ESLint 9)
packages/typescript-config — @repo/typescript-config
```

## Commands (run from root)

| Command                                                | Effect                                           |
| ------------------------------------------------------ | ------------------------------------------------ |
| `pnpm dev`                                             | Start all dev servers (web:3000)                 |
| `pnpm build`                                           | Build all packages & apps                        |
| `pnpm lint`                                            | Turbo lint (strict: `--max-warnings 0`)          |
| `pnpm check-types`                                     | Turbo typecheck (`next typegen && tsc --noEmit`) |
| `pnpm format`                                          | Prettier across `**/*.{ts,tsx,md}`               |
| `pnpm --filter=web <script>`                           | Run script for a single app/package              |
| `pnpm --filter=web test`                               | Run Vitest unit tests (33 tests across 6 files)  |
| `docker compose -f infra/docker-compose.dev.yml up -d` | Start infra only (MongoDB, Redis, MinIO)         |
| `docker compose -f infra/docker-compose.yml up -d`     | Start all services (production — build first)    |
| `docker compose -f infra/docker-compose.yml down`      | Stop all services                                |

### API backend

```bash
# Run API directly (requires MongoDB + Redis running)
cd apps/api && uvicorn app.main:app --reload --port 8000

# Run backend tests
cd apps/api && python -m pytest tests/ -v

# Start celery worker
cd apps/api && celery -A app.tasks.celery_app worker --loglevel=info
```

## Key facts

- **Package manager**: pnpm (not npm/yarn). Use `pnpm add` / `pnpm remove`.
- **Internal deps**: use `workspace:*` protocol (e.g. `"@repo/ui": "workspace:*"`).
- **Frontend tests**: Vitest v4 with `@vitejs/plugin-react` + jsdom. Run via `pnpm --filter=web test`. 33 unit tests across 6 files.
- **Backend tests**: pytest + pytest-asyncio + httpx. Run via `python -m pytest apps/api/tests/ -v`.
- **ESLint 9 flat config** — `eslint.config.js`/`.mjs`, not `.eslintrc.*`.
- **ESLint pinned to 9.x** because `eslint-plugin-react` doesn't support ESLint 10 yet.
- **CSS Modules**: page-level styles use `*.module.css`.
- **Environment files** (`.env*`) are gitignored and not committed. See `.env.example`.
- **No CI** workflows exist (no `.github/`).

## Backend conventions (apps/api)

- **Python 3.12+**, FastAPI with Motor (async MongoDB), Celery + Redis, MinIO S3
- **Module layout**: `app/config.py` → settings, `app/db/` → client + indexes, `app/schemas/` → Pydantic v2 models, `app/api/` → routers, `app/services/` → business logic, `app/tasks/` → Celery tasks
- **Tests**: pytest + `@pytest.mark.asyncio`, `httpx.AsyncClient` with `ASGITransport`, mock `motor.motor_asyncio.AsyncIOMotorDatabase` via `unittest.mock.AsyncMock`
- **Database**: Motor raw driver (no Beanie ODM), `AsyncIOMotorDatabase` injected via `Depends(get_db)`
- **Celery tasks**: use `run_async()` helper for async Motor calls in sync Celery workers
- **S3 layout**: `books/{bookId}/original.pdf`, `books/{bookId}/pages/{pageNum}.png`, `books/{bookId}/sections/{sectionId}.png`, `books/{bookId}/finalized.pdf`
- **API auth**: middleware decodes JWT Bearer token into `request.state.user_id`; public routes under `/api/auth/...` bypass auth
- **No `function` keyword**, use `async def`, type hints required

## Component conventions (packages/ui)

- Use `turbo gen react-component` to scaffold new components.
- Components use **named exports** (`export const Button = ...`), not `export default`.
- Internal package exports: `@repo/ui/button` (not `@repo/ui` barrel).

## Coding style

Follow `~/.claude/CLAUDE.md` conventions (in user home, not repo). Key rules from there:

- Arrow functions, no `function` keyword.
- `const`/`let`, no `var`.
- `import`, no `require`.
- PascalCase for components, camelCase for utils/variables.
- Named exports unless file name matches export name (then default export).
- Avoid `any`, use destructuring, minimize optional chaining on mandatory fields.
- Folder names: camelCase for generic, kebab-case for page routes.
