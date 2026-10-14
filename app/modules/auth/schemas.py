"""
Auth schemas (DTOs).
"""
from pydantic import BaseModel, EmailStr, Field

from app.core.schemas import RequestSchema
from app.modules.users.schemas import Password


class RegisterRequest(RequestSchema):
    email: EmailStr = Field(examples=["jane@example.com"])
    full_name: str = Field(min_length=2, max_length=100, examples=["Jane Doe"])
    password: Password = Field(examples=["Secret123"])


class RefreshTokenRequest(RequestSchema):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
