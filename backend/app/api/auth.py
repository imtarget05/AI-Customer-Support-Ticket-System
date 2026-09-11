from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.enums import UserRole
from app.models import User
from app.schemas import BootstrapRequest, LoginRequest, TokenResponse, UserPublic
from app.security import create_access_token, hash_password
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = auth_service.authenticate(db, body.email, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    return TokenResponse(access_token=create_access_token(user), user=UserPublic.model_validate(user))


@router.post("/bootstrap", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def bootstrap(body: BootstrapRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """One-time first-agent bootstrap.

    Guard order matters: the setup-token check runs FIRST so a wrong token
    always yields 403 (even after an agent already exists). With a valid
    token, a second call yields 409 (agent already exists). Unset
    BOOTSTRAP_TOKEN disables the route entirely (403).

    Tests override the token via the BOOTSTRAP_TOKEN env var + settings
    reload (Settings is frozen, so monkeypatch.setattr cannot assign).
    """
    import hmac as _hmac

    expected = (settings.bootstrap_token or "").strip()
    provided = (body.setup_token or "").strip()
    if not expected or not _hmac.compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid setup token"
        )
    if db.query(User).filter(User.role == UserRole.AGENT.value).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Agent already exists"
        )
    email = body.email.strip().lower()
    if db.query(User).filter(User.email == email).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )
    user = User(
        name=body.name.strip(),
        email=email,
        password_hash=hash_password(body.password),
        role=UserRole.AGENT.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(user), user=UserPublic.model_validate(user))


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(get_current_user)) -> UserPublic:
    return UserPublic.model_validate(user)
