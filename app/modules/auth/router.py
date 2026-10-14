"""
Auth routes: register, login, refresh.
"""
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Form, status

from app.core.email import send_email
from app.dependencies import DbSession
from app.modules.auth import controller
from app.modules.auth.schemas import RefreshTokenRequest, RegisterRequest, TokenResponse
from app.modules.users.schemas import UserResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: DbSession, background_tasks: BackgroundTasks):
    """
    Create a new customer account.

    A welcome email is sent in the **background**: the response comes back
    immediately and the email is "sent" afterwards (watch the server console).
    """
    user = controller.register_user(db, data)
    background_tasks.add_task(
        send_email,
        to=user.email,
        subject="Welcome to ShopSphere!",
        body=f"Hi {user.full_name}, thanks for joining us.",
    )
    return user


@router.post("/login", response_model=TokenResponse)
def login(username: Annotated[str, Form()], password: Annotated[str, Form()], db: DbSession):
    """
    Log in with email + password, sent as **form data** (not JSON).

    Put your email in the `username` field: that is the name the OAuth2
    standard uses, and it's what Swagger's **Authorize** button sends.
    """
    return controller.login(db, email=username, password=password)


@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshTokenRequest, db: DbSession):
    """Exchange a valid refresh token for a brand new pair of tokens."""
    return controller.refresh_tokens(db, data.refresh_token)
