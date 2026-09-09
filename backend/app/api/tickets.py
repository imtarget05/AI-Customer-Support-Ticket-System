from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, get_optional_user, require_agent
from app.enums import TicketCategory, TicketPriority, TicketStatus
from app.models import User
from app.schemas import (
    MessageCreate,
    MessageOut,
    TicketCreate,
    TicketDetailOut,
    TicketOut,
    TicketPage,
    TicketUpdate,
)
from app.services import ticket_service
from app.services.state_machine import InvalidTransition

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(
    body: TicketCreate,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> TicketOut:
    if user is not None:
        if user.role != "customer":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only customers can create tickets",
            )
        customer = user
    else:
        if not body.customer_email:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="customer_email is required when submitting without an account",
            )
        customer = ticket_service.find_or_create_customer(
            db, body.customer_email, body.customer_name
        )

    ticket = ticket_service.create_ticket(
        db, subject=body.subject, description=body.description, customer=customer
    )
    return TicketOut.model_validate(ticket)


@router.get("", response_model=TicketPage)
def list_tickets(
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    priority: TicketPriority | None = None,
    category: TicketCategory | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TicketPage:
    tickets, total = ticket_service.list_tickets(
        db,
        viewer=user,
        status=status_filter,
        priority=priority,
        category=category,
        page=page,
        page_size=page_size,
    )
    return TicketPage(
        items=[TicketOut.model_validate(t) for t in tickets],
        total=total,
        page=page,
        page_size=page_size,
    )


def _load_visible_ticket(ticket_id: int, db: Session, user: User):
    ticket = ticket_service.get_ticket_or_none(db, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    try:
        ticket_service.ensure_ticket_visible(ticket, user)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to view this ticket"
        )
    return ticket


@router.get("/{ticket_id}", response_model=TicketDetailOut)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TicketDetailOut:
    ticket = _load_visible_ticket(ticket_id, db, user)
    return TicketDetailOut.model_validate(ticket)


@router.patch("/{ticket_id}", response_model=TicketOut)
def update_ticket(
    ticket_id: int,
    body: TicketUpdate,
    db: Session = Depends(get_db),
    agent: User = Depends(require_agent),
) -> TicketOut:
    ticket = ticket_service.get_ticket_or_none(db, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    try:
        ticket = ticket_service.update_ticket(
            db, ticket, status=body.status, priority=body.priority
        )
    except InvalidTransition as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return TicketOut.model_validate(ticket)


@router.post(
    "/{ticket_id}/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED
)
def add_message(
    ticket_id: int,
    body: MessageCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MessageOut:
    ticket = _load_visible_ticket(ticket_id, db, user)
    try:
        message = ticket_service.add_message(db, ticket, user, body.content)
    except ticket_service.TicketRuleViolation as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return MessageOut.model_validate(message)
