import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import User

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class BootstrapRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=200)
    setup_token: str = Field(min_length=8, max_length=200)


class RegisterRequest(BaseModel):
    """Customer self-registration (đăng ký). Role is NOT client-controlled —
    registration always creates a customer account."""

    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=200)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if not EMAIL_RE.match(value):
            raise ValueError("email must be a valid email address")
        return value


class LoginRequest(BaseModel):
    email: str
    password: str


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


def to_user_public(user: User) -> UserPublic:
    return UserPublic.model_validate(user)
