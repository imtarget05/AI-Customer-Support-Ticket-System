"""Seed demo data for local development: python -m app.seed

Demo accounts:
    agent@supportdesk.dev / agent1234      (support agent)
    casey@example.com     / customer1234   (customer)
    jordan@example.com    / customer1234   (customer)
"""

from app.database import Base, SessionLocal, engine
from app.enums import TicketCategory, TicketPriority, TicketStatus, UserRole
from app.models import Message, Ticket, User
from app.security import hash_password

DEMO_PASSWORD = "customer1234"
AGENT_PASSWORD = "agent1234"

SEED_TICKETS = [
    {
        "email": "casey@example.com",
        "name": "Casey Customer",
        "subject": "Cannot reset my password",
        "description": "I clicked 'Forgot password' three times and never received the reset "
        "email. I checked spam too. I need access to my account to place an order today.",
        "category": TicketCategory.AUTHENTICATION.value,
        "priority": TicketPriority.HIGH.value,
        "status": TicketStatus.IN_PROGRESS.value,
        "messages": [
            ("customer", "Any update? I still cannot get in."),
            (
                "agent",
                "Thanks Casey — I re-triggered the reset email and escalated to IT. "
                "Can you confirm the email on file ends with @example.com?",
            ),
        ],
    },
    {
        "email": "jordan@example.com",
        "name": "Jordan Buyer",
        "subject": "Payment charged twice for one order",
        "description": "Order #8841 shows two charges of $59.00 on my card but I only received "
        "one confirmation email. One of them needs to be refunded.",
        "category": TicketCategory.PAYMENT.value,
        "priority": TicketPriority.URGENT.value,
        "status": TicketStatus.OPEN.value,
        "messages": [],
    },
    {
        "email": "casey@example.com",
        "name": "Casey Customer",
        "subject": "Question about refund timeline",
        "description": "I returned item #5520 last week and the refund status says processing. "
        "How long does it usually take to appear on my statement?",
        "category": TicketCategory.REFUND.value,
        "priority": TicketPriority.NORMAL.value,
        "status": TicketStatus.WAITING.value,
        "messages": [
            (
                "agent",
                "Hi Casey, refunds land 5-7 business days after the item passes inspection. "
                "Could you share the tracking number of the return so I can check it?",
            ),
            ("customer", "Sure, tracking is 1Z999AA10123456784."),
        ],
    },
]

SEED_TICKETS += [
    {
        "email": "jordan@example.com",
        "name": "Jordan Buyer",
        "subject": "Login loop after mobile app update",
        "description": "Since updating the iOS app to version 4.2, logging in bounces me back to "
        "the welcome screen. Deleting and reinstalling did not help.",
        "category": TicketCategory.TECHNICAL.value,
        "priority": TicketPriority.NORMAL.value,
        "status": TicketStatus.RESOLVED.value,
        "messages": [
            (
                "agent",
                "This was a session-cookie bug in 4.2. Please update to 4.2.1 and log in "
                "again — it should stick now.",
            ),
            ("customer", "Confirmed, 4.2.1 fixed it. Thanks!"),
            ("agent", "Marking this resolved. Reopen if it recurs."),
        ],
    },
    {
        "email": "casey@example.com",
        "name": "Casey Customer",
        "subject": "Feature idea: dark mode",
        "description": "It would be great if the dashboard had a dark mode option for evening "
        "shifts. Not urgent, just a suggestion.",
        "category": TicketCategory.OTHER.value,
        "priority": TicketPriority.LOW.value,
        "status": TicketStatus.CLOSED.value,
        "messages": [
            (
                "agent",
                "Love the idea — passed it to the product team. Closing this ticket for "
                "now; watch the changelog.",
            ),
        ],
    },
]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        agent = db.query(User).filter(User.email == "agent@supportdesk.dev").first()
        if agent is None:
            agent = User(
                name="Sam Agent",
                email="agent@supportdesk.dev",
                password_hash=hash_password(AGENT_PASSWORD),
                role=UserRole.AGENT.value,
            )
            db.add(agent)

        customers: dict[str, User] = {}
        for spec in SEED_TICKETS:
            email = spec["email"]
            if email not in customers:
                user = db.query(User).filter(User.email == email).first()
                if user is None:
                    user = User(
                        name=spec["name"],
                        email=email,
                        password_hash=hash_password(DEMO_PASSWORD),
                        role=UserRole.CUSTOMER.value,
                    )
                    db.add(user)
                customers[email] = user
        db.commit()

        for spec in SEED_TICKETS:
            exists = db.query(Ticket).filter(Ticket.subject == spec["subject"]).first()
            if exists is not None:
                continue
            customer = customers[spec["email"]]
            ticket = Ticket(
                customer_id=customer.id,
                subject=spec["subject"],
                description=spec["description"],
                category=spec["category"],
                priority=spec["priority"],
                status=spec["status"],
            )
            db.add(ticket)
            db.flush()
            for role, content in spec["messages"]:
                sender = agent if role == "agent" else customer
                db.add(Message(ticket_id=ticket.id, sender_id=sender.id, content=content))
        db.commit()

        total = db.query(Ticket).count()
        print(f"Seed complete: {total} tickets, {len(customers) + 1} users.")
        print("  agent login:    agent@supportdesk.dev / agent1234")
        print("  customer login: casey@example.com / customer1234")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
