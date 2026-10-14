"""
Categories schemas (DTOs).
"""
from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.core.schemas import RequestSchema, ResponseSchema


class CategoryCreate(RequestSchema):
    name: str = Field(min_length=2, max_length=50, examples=["Electronics"])
    description: str | None = Field(default=None, max_length=500, examples=["Phones, laptops and gadgets"])


class CategoryUpdate(RequestSchema):
    name: str | None = Field(default=None, min_length=2, max_length=50)
    description: str | None = Field(default=None, max_length=500)


class CategoryResponse(ResponseSchema):
    id: int
    name: str
    description: str | None
    created_at: datetime


class CategorySummary(ResponseSchema):
    """Short version, shown inside a product."""

    id: int
    name: str


class CategoryProduct(ResponseSchema):
    """A product, as shown inside its category."""

    id: int
    name: str
    price: Decimal
    stock: int


class CategoryWithProducts(CategoryResponse):
    """One category + its products (used by GET /categories/{category_id})."""

    products: list[CategoryProduct]  # the products that get_category() loaded
