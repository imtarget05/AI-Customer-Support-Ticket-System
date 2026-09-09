"""Application settings, read from environment variables with dev defaults."""

import os
from dataclasses import dataclass, field


def _split_origins(raw: str) -> list[str]:
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./supportdesk.db")
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "720"))
    ai_provider: str = os.getenv("AI_PROVIDER", "stub")
    ai_model: str = os.getenv("AI_MODEL", "gpt-4o-mini")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    cors_origins: list[str] = field(
        default_factory=lambda: _split_origins(
            os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
        )
    )


settings = Settings()
