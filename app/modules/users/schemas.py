"""
Users schemas (DTOs): the shape of the data going in and out of the users API.
"""
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, EmailStr, Field, model_validator

from app.core.pagination import PageParams
from app.core.schemas import RequestSchema, ResponseSchema
from app.modules.users.models import UserRole


def check_password_strength(password: str) -> str:
    if not any(char.isupper() for char in password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not any(char.islower() for char in password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not any(char.isdigit() for char in password):
        raise ValueError("Password must contain at least one digit")
    return password


# A reusable type: every field declared as `Password` gets all these rules.
Password = Annotated[str, Field(min_length=8, max_length=64), AfterValidator(check_password_strength)]


# ---------- Requests ----------


class UserUpdate(RequestSchema):
    """What a user can change on their own profile. Every field is optional."""

    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    email: EmailStr | None = None


class ChangePasswordRequest(RequestSchema):
    current_password: str
    new_password: Password

    # A model validator sees ALL fields at once, so it can compare them.
    @model_validator(mode="after")
    def check_passwords_differ(self) -> "ChangePasswordRequest":
        if self.current_password == self.new_password:
            raise ValueError("New password must be different from the current password")
        return self


class UserAdminUpdate(RequestSchema):
    """What only an admin can change."""

    role: UserRole | None = None
    is_active: bool | None = None


class UserFilters(PageParams):
    """Query parameters of the user list: ?search=john&role=admin&page=1&size=10"""

    search: str | None = Field(default=None, min_length=2, max_length=100, description="Search by name or email")
    role: UserRole | None = None


# ---------- Responses ----------


class UserResponse(ResponseSchema):
    # Notice: no password field here, so it can never be sent to the client.
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class UserSummary(ResponseSchema):
    """Public info about a user (e.g. the author of a review). No email!"""

    id: int
    full_name: str
