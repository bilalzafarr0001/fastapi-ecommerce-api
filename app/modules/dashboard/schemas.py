"""
Dashboard schemas (DTOs).
"""
from decimal import Decimal

from pydantic import BaseModel

from app.core.schemas import ResponseSchema


class LowStockProduct(ResponseSchema):
    id: int
    name: str
    stock: int


class DashboardStats(BaseModel):
    total_users: int
    total_products: int
    total_orders: int
    total_revenue: Decimal
    orders_by_status: dict[str, int]
    low_stock_products: list[LowStockProduct]
