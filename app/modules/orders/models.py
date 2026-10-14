"""
Order model -> the `orders` table.

One order = one product bought by one user (with a quantity).
The price is copied into the order at the moment of purchase, so later
price changes don't modify old orders.
"""
import enum
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.products.models import Product
    from app.modules.users.models import User


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(TimestampMixin, Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    quantity: Mapped[int]
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))  # product price at the moment of purchase
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))  # unit_price x quantity
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, native_enum=False, length=20), default=OrderStatus.PENDING
    )
    shipping_address: Mapped[str] = mapped_column(String(255))

    # Many orders -> one user / one product
    user: Mapped["User"] = relationship(back_populates="orders")
    product: Mapped["Product"] = relationship(lazy="selectin")
