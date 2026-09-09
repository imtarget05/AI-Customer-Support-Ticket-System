"""AI-related tables: embeddings, raw predictions, evaluation records."""

from sqlalchemy import Boolean, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin


class TicketEmbedding(Base):
    __tablename__ = "ticket_embeddings"

    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), primary_key=True)
    # JSON-encoded list[float]; vector search runs in Python at MVP scale.
    embedding: Mapped[str] = mapped_column(Text, nullable=False)


class AIPrediction(TimestampMixin, Base):
    __tablename__ = "ai_predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True, nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    # Raw LLM output kept for debugging/evaluation.
    raw_response: Mapped[str | None] = mapped_column(Text, nullable=True)


class AIEvaluation(TimestampMixin, Base):
    __tablename__ = "ai_evaluations"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True, nullable=False)
    expected_category: Mapped[str] = mapped_column(String(30), nullable=False)
    predicted_category: Mapped[str] = mapped_column(String(30), nullable=False)
    correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
