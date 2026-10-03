from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import dashboard, institutions, reports, scores, taxonomy
from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Replaces the deprecated @app.on_event("startup") hook.
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    # Session 10: driven by ALLOWED_ORIGINS env var (comma-separated) so
    # the Render deployment can point at the Vercel URL without a code
    # change. Falls back to the Vite dev server for local development.
    allow_origins=settings.allowed_origin_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(institutions.router)
app.include_router(taxonomy.router)
app.include_router(reports.router)
app.include_router(scores.router)
app.include_router(dashboard.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}
