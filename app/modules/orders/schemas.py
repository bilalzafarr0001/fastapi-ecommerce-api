"""
Orders schemas (DTOs).
"""
from datetime import datetime
from decimal import Decimal

from pydantic import Field, field_validator

from app.core.pagination import PageParams
from app.core.schemas import RequestSchema, ResponseSchema
from app.modules.orders.models import OrderStatus
from app.modules.products.schemas import ProductSummary


# ---------- Requests ----------


class OrderCreate(RequestSchema):
    product_id: int = Field(gt=0, examples=[1])
    quantity: int = Field(gt=0, le=100, examples=[2])
    shipping_address: str = Field(max_length=255, examples=["221B Baker Street, London"])

    # A field validator checks (and can clean) ONE field.
    @field_validator("shipping_address")
    @classmethod
    def clean_shipping_address(cls, address: str) -> str:
        address = " ".join(address.split())  # remove extra spaces: "  12   Main St " -> "12 Main St"
        if len(address) < 10:
            raise ValueError("Shipping address must be at least 10 characters long")
        return address


class OrderStatusUpdate(RequestSchema):
    status: OrderStatus


class OrderFilters(PageParams):
    """Query parameters of the order list: ?status=paid&page=1&size=10"""

    status: OrderStatus | None = None


# ---------- Responses ----------


class OrderResponse(ResponseSchema):
    id: int
    user_id: int
    product: ProductSummary  # nested schema, filled from the `order.product` relationship
    quantity: int
    unit_price: Decimal
    total_amount: Decimal
    status: OrderStatus
    shipping_address: str
    created_at: datetime
    updated_at: datetime
