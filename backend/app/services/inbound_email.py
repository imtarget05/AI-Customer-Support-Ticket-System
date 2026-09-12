"""Inbound email parser. Turns a reply email into a ticket message."""

import re

from sqlalchemy.orm import Session

from app.enums import TicketStatus
from app.models.message import Message
from app.models.ticket import Ticket
from app.models.user import User


def process_inbound_email(db: Session, from_email: str, subject: str, body: str) -> dict:
    match = re.search(r"\[SupportDesk\s*#(\d+)\]", subject, re.IGNORECASE)
    if match is None:
        match = re.search(r"#(\d+)", subject)
    if match is None:
        return {"status": "ignored", "reason": "no_ticket_id"}

    ticket_id = int(match.group(1))
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        return {"status": "ignored", "reason": "ticket_not_found"}

    customer = ticket.customer
    if customer is None:
        customer = db.get(User, ticket.customer_id)
    customer_email = (customer.email if customer is not None else "").strip().lower()
    if (from_email or "").strip().lower() != customer_email:
        return {"status": "ignored", "reason": "email_mismatch"}

    if ticket.status == TicketStatus.CLOSED.value:
        return {"status": "ignored", "reason": "ticket_closed"}

    content = (body or "").strip()
    if not content:
        return {"status": "ignored", "reason": "empty_body"}

    message = Message(ticket_id=ticket.id, sender_id=ticket.customer_id, content=content)
    db.add(message)

    if ticket.status in (TicketStatus.WAITING.value, TicketStatus.RESOLVED.value):
        ticket.status = TicketStatus.IN_PROGRESS.value

    db.commit()
    db.refresh(ticket)
    db.refresh(message)
    return {
        "status": "processed",
        "ticket_id": ticket.id,
        "message_id": message.id,
        "ticket_status": ticket.status,
    }
