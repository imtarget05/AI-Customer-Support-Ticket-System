"""FastAPI application entry point: uvicorn app.main:app"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, dashboard, tickets
from app.api.ai import router as ai_router
from app.api.metrics import router as metrics_router
from app.config import settings
from app.database import Base, engine

# Schema management: dev/test uses create_all for convenience; production uses Alembic.
# Switch via ALEMBIC_MIGRATE=true to run `alembic upgrade head` on startup.
if os.getenv("ALEMBIC_MIGRATE", "").lower() in ("1", "true", "yes"):
    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config(str(Path(__file__).resolve().parent.parent / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")
else:
    Base.metadata.create_all(bind=engine)



@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    engine.dispose()

def create_app() -> FastAPI:
    app = FastAPI(title="SupportDesk API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth.router)
    app.include_router(tickets.router)
    app.include_router(ai_router)
    app.include_router(metrics_router, prefix="/api", tags=["metrics"])

    app.include_router(dashboard.router)

    @app.get("/api/health", tags=["meta"])
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/", tags=["meta"])
    def root() -> dict:
        return {"title": app.title, "version": app.version}

    return app


app = create_app()
