# Developer Agent — Configuration Improvements

## Current Problem

The developer agent only generates code within existing workspace boundaries. When asked to implement a full-stack application, it defaults to only the frontend because:

1. No backend workspace exists to extend
2. AGENTS.md only describes frontend structure
3. Task prompts lack a comprehensive deliverable checklist
4. Agent has no Python/Docker tool context by default

## Required Fixes

### 1. Update AGENTS.md

Add a "Full Stack Layout" section to AGENTS.md:

```
## Full Stack Layout

```

apps/web — Next.js App Router (port 3000)
apps/api — FastAPI Python backend (port 8000)
docker/ — Docker Compose + service configs
docker-compose.yml — mongodb, redis, minio, libretranslate, nginx, api, celery
nginx/ — Reverse proxy config (port 80)

```

## Backend conventions (apps/api)
- Python 3.12+, FastAPI, Motor (async MongoDB), Celery
- Models in `apps/api/models/` — Beanie/MongoEngine ODM documents
- Routes in `apps/api/routes/` — one file per resource
- Tasks in `apps/api/tasks/` — Celery task definitions
- Services in `apps/api/services/` — S3, LibreTranslate wrappers
- Use `pip` / `uv` for dependencies, not pnpm

## Infrastructure conventions
- Docker Compose at `docker/docker-compose.yml`
- All services (mongodb, redis, minio, libretranslate, nginx) defined there
- API depends on mongodb + redis + minio
- Celery worker depends on redis + mongodb + minio
- Frontend (apps/web) communicates via nginx reverse proxy
```

### 2. Add Prompt Template for Full-Stack Tasks

The developer agent prompt should include this checklist:

```
## Full-Stack Deliverable Checklist

Before writing any code, enumerate all deliverables:

### Frontend (apps/web)
- [ ] Next.js pages & layouts
- [ ] Auth config (NextAuth)
- [ ] Middleware
- [ ] Components
- [ ] API client library
- [ ] Tests (Vitest + Playwright)

### Backend (apps/api)
- [ ] FastAPI app entry point
- [ ] MongoDB models (Motor/Beanie)
- [ ] REST API routes
- [ ] Celery task definitions
- [ ] S3 service layer (MinIO)
- [ ] LibreTranslate integration
- [ ] Auth token validation middleware
- [ ] File upload endpoint
- [ ] Requirements.txt / pyproject.toml

### Infrastructure (docker/)
- [ ] docker-compose.yml (mongodb, redis, minio, libretranslate, nginx, api, celery)
- [ ] Nginx config (reverse proxy, static files, API routing)
- [ ] Dockerfile for API
- [ ] Dockerfile for Celery worker
- [ ] .env.example with all service URLs

### Tests
- [ ] Unit tests (Vitest for frontend)
- [ ] E2E test specs (Playwright scenarios)

### Verification
- [ ] `pnpm build` passes
- [ ] `pnpm lint` passes (--max-warnings 0)
- [ ] `pnpm check-types` passes
- [ ] Docker Compose starts all services
- [ ] Frontend can reach backend API
```

### 3. Configure Global Agent Instructions

Add to the agent's global configuration (opencode.json or CLAUDE.md):

```json
{
  "developer": {
    "fullStackPrompt": "Always check AGENTS.md for the full stack layout before implementing. Generate code for ALL workspaces (frontend, backend, infrastructure) unless explicitly told otherwise. Run through the Full-Stack Deliverable Checklist before writing any code."
  }
}
```

### 4. Workspace Setup Checklist

When starting a new monorepo project, the initial prompt should:

1. Define all workspaces in `pnpm-workspace.yaml` upfront (including `apps/api`)
2. Set up AGENTS.md with the full stack layout before any development begins
3. Create stub directories for every anticipated component
4. Make the first developer task "scaffold all workspaces and infra" rather than "implement feature X"

### 5. Agent Model Recommendations

- Use a model with strong Python/Docker knowledge for backend generation
- Provide the agent with the architecture doc and data model doc inline in the task prompt
- If using a subagent, split into two parallel agents: one for frontend, one for backend+infra
