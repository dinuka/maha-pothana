from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import jwt

from app.config import settings
from app.db.client import connect_db, close_db, get_db
from app.db.indexes import ensure_indexes
from app.api import auth, books, pages, sections, users
from app.api.books_stats import router as books_stats_router
from app.api.translations_history import router as translations_history_router
from app.api.translations_draft import router as translations_draft_router
from app.api.extraction import router as extraction_router

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = await connect_db()
    await ensure_indexes(db)
    yield
    await close_db()


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.nextjs_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/auth"):
        return await call_next(request)

    internal_key = request.headers.get("X-Internal-Api-Key", "")
    if internal_key and internal_key == settings.internal_api_key:
        request.state.user_id = request.headers.get("X-User-Id")
    else:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = jwt.decode(token, settings.auth_secret, algorithms=["HS256"])
                request.state.user_id = payload.get("sub")
            except jwt.PyJWTError:
                request.state.user_id = None
        else:
            request.state.user_id = None

    return await call_next(request)


app.include_router(auth.router)
app.include_router(books.router)
app.include_router(pages.router)
app.include_router(sections.router)
app.include_router(users.router)
app.include_router(books_stats_router)
app.include_router(translations_history_router)
app.include_router(translations_draft_router)
app.include_router(extraction_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
