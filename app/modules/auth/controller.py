"""
Auth controller: registration, login and token refresh.

Notice this module has no `models.py`: it works with the User model that
belongs to the users module.
"""
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ForbiddenError, UnauthorizedError
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.modules.auth.schemas import RegisterRequest, TokenResponse
from app.modules.users.controller import get_user_by_email
from app.modules.users.models import User


def register_user(db: Session, data: RegisterRequest) -> User:
    if get_user_by_email(db, data.email):
        raise ConflictError("Email is already registered")

    user = User(
        email=data.email.lower(),
        full_name=data.full_name,
        hashed_password=hash_password(data.password),  # never store plain passwords!
    )
    db.add(user)
    db.commit()
    db.refresh(user)  # reload from the DB to get the generated id, created_at...
    return user


def login(db: Session, email: str, password: str) -> TokenResponse:
    user = get_user_by_email(db, email)
    if user is None or not verify_password(password, user.hashed_password):
        # Same message in both cases, so nobody can find out which emails are registered.
        raise UnauthorizedError("Incorrect email or password")
    if not user.is_active:
        raise ForbiddenError("Your account has been disabled")
    return create_tokens(user)


def refresh_tokens(db: Session, refresh_token: str) -> TokenResponse:
    user_id = decode_token(refresh_token, expected_type="refresh")
    user = db.get(User, user_id) if user_id else None
    if user is None or not user.is_active:
        raise UnauthorizedError("Invalid or expired refresh token")
    return create_tokens(user)


def create_tokens(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )
