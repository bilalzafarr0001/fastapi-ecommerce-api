"""
Product model -> the `products` table.
"""
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.categories.models import Category
    from app.modules.reviews.models import Review


class Product(TimestampMixin, Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    # Money is stored as NUMERIC(10, 2), never as float (floats cause rounding errors).
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    stock: Mapped[int] = mapped_column(default=0)
    image_url: Mapped[str | None] = mapped_column(String(255))
    # "Deleting" a product only hides it (soft delete), because old orders still point to it.
    is_active: Mapped[bool] = mapped_column(default=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True)

    # Many products -> one category.
    # lazy="selectin" loads the category of ALL products in one extra query
    # (instead of one query per product, the famous "N+1 problem").
    category: Mapped["Category"] = relationship(back_populates="products", lazy="selectin")
    reviews: Mapped[list["Review"]] = relationship(back_populates="product")
