"""
Reviews schemas (DTOs).
"""
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.schemas import RequestSchema, ResponseSchema
from app.modules.users.schemas import UserSummary


class ReviewCreate(RequestSchema):
    rating: int = Field(ge=1, le=5, examples=[5])
    comment: str | None = Field(default=None, max_length=1000, examples=["Great product, fast delivery!"])


class ReviewUpdate(RequestSchema):
    rating: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)


class ReviewResponse(ResponseSchema):
    id: int
    product_id: int
    rating: int
    comment: str | None
    user: UserSummary  # only id + name of the author: never expose their email
    created_at: datetime
    updated_at: datetime


class ReviewSummary(BaseModel):
    product_id: int
    average_rating: float | None  # None when the product has no reviews yet
    review_count: int
