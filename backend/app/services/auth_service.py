"""Authentication business logic."""

from sqlalchemy.orm import Session

from app.models import User
from app.security import verify_password


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user
