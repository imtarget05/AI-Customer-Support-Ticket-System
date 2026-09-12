"""FastAPI application entry point: uvicorn app.main:app"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api import auth, dashboard, tickets, webhooks
from app.api.ai import router as ai_router
from app.api.metrics import router as metrics_router
from app.config import settings
from app.database import Base, engine

logger = logging.getLogger(__name__)
_schema_setup_failed = False


def _run_schema_setup() -> None:
    global _schema_setup_failed
    try:
        if settings.alembic_migrate:
            from alembic.config import Config
            from alembic import command

            alembic_cfg = Config(str(Path(__file__).resolve().parent.parent / "alembic.ini"))
            command.upgrade(alembic_cfg, "head")
        else:
            Base.metadata.create_all(bind=engine)
    except Exception as exc:
        _schema_setup_failed = True
        logger.error("Database startup failed: %s", type(exc).__name__)


_run_schema_setup()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    engine.dispose()


def _database_ready() -> bool:
    if _schema_setup_failed:
        return False
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


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
    app.include_router(webhooks.router)
    app.include_router(ai_router)
    app.include_router(metrics_router, prefix="/api", tags=["metrics"])

    app.include_router(dashboard.router)

    @app.get("/api/health")
    def health() -> Any:
        if _database_ready():
            return {"status": "ok"}
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "database": "unavailable"},
        )

    @app.get("/")
    def root() -> dict:
        return {"title": app.title, "version": app.version}

    return app


app = create_app()
