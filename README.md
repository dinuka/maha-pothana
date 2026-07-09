# Maha Pothana

A collaborative book translation platform. Translators work on sections of digitized book pages to produce translated versions in target languages.

## Tech Stack

| Layer       | Technology                                           |
| ----------- | ---------------------------------------------------- |
| Frontend    | Next.js 16 (App Router), TypeScript 6                |
| Backend     | FastAPI, Python 3.12+, Motor (async MongoDB), Celery |
| Database    | MongoDB 7                                            |
| Cache/Queue | Redis 7                                              |
| Storage     | MinIO (S3-compatible)                                |
| Translation | OpenRouter (LLM-based)                               |
| Auth        | NextAuth v5 + Google OAuth                           |
| UI          | CSS Modules, Konva.js (section annotation)           |
| Monorepo    | Turborepo + pnpm                                     |

## Project Structure

```
apps/web        — Next.js frontend (port 3000)
apps/api        — FastAPI backend (port 8000)
infra/          — Docker Compose (dev + production), nginx config, Dockerfiles
packages/ui     — @repo/ui shared React components
packages/eslint-config — ESLint 9 flat config
packages/typescript-config — Shared TS configs
```

## Getting Started

### Prerequisites

- Node.js 22+, pnpm
- Python 3.12+
- Docker + Docker Compose (for backend services)

### Environment

Copy `.env.example` to `.env` and fill in the values:

```sh
cp .env.example .env
```

Required: `AUTH_GOOGLE_ID`, `AUTH_GOOGLE_SECRET`, `AUTH_SECRET`.

See `.env.example` for all available variables.

### Dev Environment — Infra in Docker, Apps Natively

Start infrastructure only (MongoDB, Redis, MinIO):

```sh
docker compose -f infra/docker-compose.dev.yml up -d
```

Run apps natively with hot-reload:

```sh
pnpm install
pnpm dev          # → http://localhost:3000
```

For the backend:

```sh
cd apps/api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Production — Everything in Docker

```sh
docker compose -f infra/docker-compose.yml build
docker compose -f infra/docker-compose.yml up -d
```

This starts: nginx (port 80), Next.js, FastAPI, Celery worker, MongoDB, Redis, MinIO.

## Commands

| Command                                                                | Description                               |
| ---------------------------------------------------------------------- | ----------------------------------------- |
| `pnpm dev`                                                             | Start frontend dev server                 |
| `pnpm build`                                                           | Build all packages & apps                 |
| `pnpm lint`                                                            | Lint (strict: `--max-warnings 0`)         |
| `pnpm check-types`                                                     | TypeScript type checking                  |
| `pnpm format`                                                          | Prettier formatting                       |
| `pnpm --filter=web test`                                               | Run frontend unit tests (33 Vitest tests) |
| `cd apps/api && python -m pytest tests/ -v`                            | Run backend tests (41 pytest tests)       |
| `cd apps/api && celery -A app.tasks.celery_app worker --loglevel=info` | Start Celery worker                       |

## Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → APIs & Services → Credentials
3. Create an OAuth 2.0 Client ID (Web application)
4. **Authorized JavaScript origins**: `http://localhost:3000`
5. **Authorized redirect URIs**: `http://localhost:3000/api/auth/callback/google`
6. Copy the Client ID and Client Secret to `.env`
