from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import jwt

from app.config import settings
from app.db.client import connect_db, close_db, get_db
from app.db.indexes import ensure_indexes
from app.api import auth, books, pages, sections, users


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


@app.get("/api/health")
async def health():
    return {"status": "ok"}
