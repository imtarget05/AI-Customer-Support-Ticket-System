"""Domain enums. Stored as plain strings in the DB for SQLite/Postgres portability."""

import enum


class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    AGENT = "agent"


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TicketCategory(str, enum.Enum):
    UNKNOWN = "unknown"
    AUTHENTICATION = "authentication"
    PAYMENT = "payment"
    REFUND = "refund"
    TECHNICAL = "technical"
    OTHER = "other"
