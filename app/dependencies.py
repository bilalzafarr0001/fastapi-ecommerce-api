"""
Shared dependencies (Dependency Injection).

A dependency is a function FastAPI runs BEFORE your route. Its return value
is passed into the route as a parameter. This project has only two:

    get_db            -> gives the route a database session
    get_current_user  -> gives the route the logged-in user (uses get_db itself)

Use them through the short aliases at the bottom:

    @router.get("/me")
    def read_me(current_user: CurrentUser): ...

Rules like "admins only" are NOT dependencies here: they are checked inside
the controller functions (see `check_admin` in users/controller.py).
"""
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import decode_token
from app.modules.users.models import User


def get_db() -> Generator[Session, None, None]:
    """
    Open one database session per request and ALWAYS close it at the end.

    Code before `yield` runs before the route, code after it runs when the
    request is finished. If the route fails before `db.commit()`, closing
    the session rolls back every unsaved change.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Reads the "Authorization: Bearer <token>" header. `tokenUrl` tells Swagger UI
# where to send the username/password when you click the "Authorize" button.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    """Return the logged-in user, or answer 401 if the token is missing/invalid."""
    user_id = decode_token(token, expected_type="access")
    user = db.get(User, user_id) if user_id else None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account has been disabled")
    return user


# --- Short aliases used in route signatures ---
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
