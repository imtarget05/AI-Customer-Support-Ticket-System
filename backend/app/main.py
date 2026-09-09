"""FastAPI application entry point: uvicorn app.main:app"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, dashboard, tickets
from app.api.ai import router as ai_router
from app.config import settings
from app.database import Base, engine

# Dev-grade schema creation. Production path: manage with Alembic (deferred, see plan).
Base.metadata.create_all(bind=engine)


def create_app() -> FastAPI:
    app = FastAPI(title="SupportDesk API", version="0.1.0")
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
    app.include_router(dashboard.router)

    @app.get("/api/health", tags=["meta"])
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
