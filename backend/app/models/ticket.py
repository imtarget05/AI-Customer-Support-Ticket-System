from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.enums import TicketCategory, TicketPriority, TicketStatus
from app.models.base import TimestampMixin


class Ticket(TimestampMixin, Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        String(30), nullable=False, default=TicketCategory.UNKNOWN.value, index=True
    )
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default=TicketPriority.NORMAL.value, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=TicketStatus.OPEN.value, index=True
    )
    # Filled by the AI service (suggestion-only); never written by AI without validation.
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    customer = relationship("User")
    messages = relationship(
        "Message",
        back_populates="ticket",
        order_by="Message.created_at",
        cascade="all, delete-orphan",
    )
