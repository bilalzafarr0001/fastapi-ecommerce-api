"""
User model -> the `users` table.
"""
import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin

# Imports only used for type hints (avoids circular imports at runtime).
if TYPE_CHECKING:
    from app.modules.orders.models import Order
    from app.modules.reviews.models import Review


class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"

print('my name'wfwfewefwef;
 
class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100))
    hashed_password: Mapped[str] = mapped_column(String(255))
    # native_enum=False -> stored as a simple VARCHAR column, easier to change later.
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=20), default=UserRole.CUSTOMER
    )
    is_active: Mapped[bool] = mapped_column(default=True)

    # One user -> many orders / reviews
    orders: Mapped[list["Order"]] = relationship(back_populates="user")
    reviews: Mapped[list["Review"]] = relationship(back_populates="user")
