"""
Security helpers: password hashing and JWT tokens.

These are plain Python functions with no FastAPI code inside, so they are
easy to reuse anywhere (routes, the seed script, tests...).
"""
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

# Argon2 is the currently recommended password hashing algorithm.
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_token(user_id: int, token_type: str, expires_in: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),  # "subject": who the token belongs to
        "type": token_type,  # "access" or "refresh"
        "exp": now + expires_in,  # expiry: PyJWT rejects expired tokens for us
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(user_id: int) -> str:
    """Short-lived token sent with every request: `Authorization: Bearer <token>`."""
    return create_token(user_id, "access", timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))


def create_refresh_token(user_id: int) -> str:
    """Long-lived token used only to get a new access token."""
    return create_token(user_id, "refresh", timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))


def decode_token(token: str, expected_type: str) -> int | None:
    """
    Return the user id stored in the token, or None when the token is
    invalid, expired, or not of the expected type ("access" / "refresh").
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.InvalidTokenError:  # wrong signature, expired, or not a JWT at all
        return None

    if payload.get("type") != expected_type:
        return None
    return int(payload["sub"])
