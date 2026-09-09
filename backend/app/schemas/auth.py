from pydantic import BaseModel, ConfigDict

from app.models import User


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
