"""Application settings, read from environment variables with dev defaults.

Loads `backend/.env` if present (stdlib parser, no dependency). Never commit
real credentials — `.env` is gitignored; `.env.example` documents the shape.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path


def _load_dotenv() -> None:
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv()


def _split_origins(raw: str) -> list[str]:
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./supportdesk.db")
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "720"))

    # --- AI provider: "stub" (offline) | "cloudflare" (Workers AI) | "openai" ---
    ai_provider: str = os.getenv("AI_PROVIDER", "stub")
    ai_model: str = os.getenv("AI_MODEL", "gpt-4o-mini")

    # Guardrail on unsafe LLM output: "reject" (return 502, keep ticket) default,
    # or "fallback" (return a neutral draft instead of the blocked one).
    ai_guardrail_mode: str = os.getenv("AI_GUARDRAIL_MODE", "reject")

    # Knowledge base directory for RAG
    knowledge_dir: str = os.getenv("KNOWLEDGE_DIR", "")

    # Embedder: "bow" (hashed bag-of-words, offline default) | "hf" (sentence-transformers, lazy-load, BoW fallback)
    ai_embed_provider: str = os.getenv("AI_EMBED_PROVIDER", "bow")

    # Workflow confidence thresholds
    workflow_high_confidence: float = float(os.getenv("WORKFLOW_HIGH_CONFIDENCE", "0.85"))
    workflow_low_confidence: float = float(os.getenv("WORKFLOW_LOW_CONFIDENCE", "0.60"))

    # Cloudflare Workers AI
    cloudflare_account_id: str = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
    cloudflare_api_token: str = os.getenv("CLOUDFLARE_API_TOKEN", "")
    cloudflare_model: str = os.getenv("CLOUDFLARE_MODEL", "@cf/meta/llama-3.1-8b-instruct")

    # OpenAI-compatible (kept as an alternative provider)
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    cors_origins: list[str] = field(
        default_factory=lambda: _split_origins(
            os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
        )
    )


settings = Settings()
