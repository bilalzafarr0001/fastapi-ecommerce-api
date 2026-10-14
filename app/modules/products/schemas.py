"""
Products schemas (DTOs).

Money uses `Decimal`, never `float`. In JSON responses Pydantic sends
Decimals as strings ("59.99") so no precision is lost on the way.
"""
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import Field, computed_field

from app.core.pagination import PageParams
from app.core.schemas import RequestSchema, ResponseSchema
from app.modules.categories.schemas import CategorySummary


# ---------- Requests ----------


class ProductCreate(RequestSchema):
    name: str = Field(min_length=2, max_length=150, examples=["Wireless Headphones"])
    description: str | None = Field(default=None, max_length=2000)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2, examples=["59.99"])
    stock: int = Field(ge=0, le=100_000, examples=[25])
    category_id: int = Field(gt=0)


class ProductUpdate(RequestSchema):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    price: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    stock: int | None = Field(default=None, ge=0, le=100_000)
    category_id: int | None = Field(default=None, gt=0)
    is_active: bool | None = None


class ProductFilters(PageParams):
    """
    Query parameters of the product list (plus `page` and `size` from PageParams).
    Every field is read from the URL:

        GET /products?search=phone&min_price=10&sort_by=price&sort_order=asc&page=1
    """

    search: str | None = Field(default=None, min_length=2, max_length=100, description="Search in name and description")
    category_id: int | None = Field(default=None, gt=0)
    min_price: Decimal | None = Field(default=None, ge=0)
    max_price: Decimal | None = Field(default=None, ge=0)
    in_stock: bool = Field(default=False, description="true = only show products that are in stock")
    sort_by: Literal["created_at", "price", "name"] = "created_at"
    sort_order: Literal["asc", "desc"] = "desc"


# ---------- Responses ----------


class ProductResponse(ResponseSchema):
    id: int
    name: str
    description: str | None
    price: Decimal
    stock: int
    image_url: str | None
    is_active: bool
    category: CategorySummary  # nested schema, filled from the `product.category` relationship
    created_at: datetime
    updated_at: datetime

    # A computed field is not stored anywhere: it's calculated when the
    # response is built, and it shows up in the JSON and in the docs.
    @computed_field
    @property
    def in_stock(self) -> bool:
        return self.stock > 0


class ProductSummary(ResponseSchema):
    """Short version, shown inside an order."""

    id: int
    name: str
