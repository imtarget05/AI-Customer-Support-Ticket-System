"""Ticket lifecycle state machine. The backend is the single source of truth.

    OPEN → IN_PROGRESS → WAITING → IN_PROGRESS → RESOLVED → CLOSED

Anything not listed here is rejected with 409 by the API layer.
AI never performs transitions.
"""

from app.enums import TicketStatus

ALLOWED_TRANSITIONS: dict[TicketStatus, set[TicketStatus]] = {
    TicketStatus.OPEN: {TicketStatus.IN_PROGRESS},
    TicketStatus.IN_PROGRESS: {TicketStatus.WAITING, TicketStatus.RESOLVED},
    TicketStatus.WAITING: {TicketStatus.IN_PROGRESS},
    TicketStatus.RESOLVED: {TicketStatus.CLOSED},
    TicketStatus.CLOSED: set(),
}


class InvalidTransition(Exception):
    def __init__(self, current: TicketStatus, target: TicketStatus):
        self.current = current
        self.target = target
        super().__init__(f"Illegal status transition: {current.value} → {target.value}")


def validate_transition(current: TicketStatus, target: TicketStatus) -> None:
    if target not in ALLOWED_TRANSITIONS[current]:
        raise InvalidTransition(current, target)
