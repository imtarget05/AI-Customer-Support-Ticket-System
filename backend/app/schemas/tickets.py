import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.enums import TicketCategory, TicketPriority, TicketStatus
from app.schemas.auth import UserPublic

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class TicketCreate(BaseModel):
    subject: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=5000)
    # Required only for anonymous submission; ignored when a customer token is provided.
    customer_email: str | None = Field(default=None, max_length=255)
    customer_name: str | None = Field(default=None, max_length=120)

    @field_validator("customer_email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is not None and not EMAIL_RE.match(value):
            raise ValueError("customer_email must be a valid email address")
        return value


class TicketUpdate(BaseModel):
    status: TicketStatus | None = None
    priority: TicketPriority | None = None


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sender: UserPublic
    content: str
    created_at: datetime


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject: str
    description: str
    category: TicketCategory
    priority: TicketPriority
    status: TicketStatus
    ai_summary: str | None
    ai_confidence: float | None
    customer: UserPublic
    created_at: datetime
    updated_at: datetime


class TicketDetailOut(TicketOut):
    messages: list[MessageOut]


class TicketPage(BaseModel):
    items: list[TicketOut]
    total: int
    page: int
    page_size: int
