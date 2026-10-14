"""
Review model -> the `reviews` table.
"""
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.products.models import Product
    from app.modules.users.models import User


class Review(TimestampMixin, Base):
    __tablename__ = "reviews"
    # Rules enforced by the DATABASE itself (a second safety net after Pydantic):
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_reviews_user_product"),  # 1 review per product per user
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_rating_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    rating: Mapped[int]
    comment: Mapped[str | None] = mapped_column(Text)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)

    user: Mapped["User"] = relationship(back_populates="reviews", lazy="selectin")
    product: Mapped["Product"] = relationship(back_populates="reviews")
