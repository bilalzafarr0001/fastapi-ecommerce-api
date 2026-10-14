"""
Users routes (the HTTP layer).

Routers stay thin: they declare the URL, the input/output schemas and the
dependencies, then hand the real work over to the controller.
"""
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.pagination import Page
from app.dependencies import CurrentUser, DbSession
from app.modules.users import controller
from app.modules.users.schemas import ChangePasswordRequest, UserAdminUpdate, UserFilters, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])

# IMPORTANT: the "/me" routes are declared BEFORE "/{user_id}". FastAPI checks
# routes in order, so otherwise "/users/me" would match "/{user_id}" with user_id="me".


@router.get("/me", response_model=UserResponse)
def read_my_profile(current_user: CurrentUser):
    """Get the profile of the logged-in user."""
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_my_profile(data: UserUpdate, db: DbSession, current_user: CurrentUser):
    """Update your own name and/or email."""
    return controller.update_profile(db, current_user, data)


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_my_password(data: ChangePasswordRequest, db: DbSession, current_user: CurrentUser):
    """Change your password (you must also send your current password)."""
    controller.change_password(db, current_user, data)


# ---------- Admin only (the controller checks the role) ----------


@router.get("", response_model=Page[UserResponse])
def list_users(db: DbSession, current_user: CurrentUser, params: Annotated[UserFilters, Query()]):
    """List all users, with optional search and role filter. **Admin only.**"""
    return controller.list_users(db, params, current_user)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: DbSession, current_user: CurrentUser):
    """Get any user by id. **Admin only.**"""
    return controller.get_user(db, user_id, current_user)


@router.patch("/{user_id}", response_model=UserResponse)
def admin_update_user(user_id: int, data: UserAdminUpdate, db: DbSession, current_user: CurrentUser):
    """Change a user's role, or activate/deactivate their account. **Admin only.**"""
    return controller.admin_update_user(db, user_id, data, current_user)
