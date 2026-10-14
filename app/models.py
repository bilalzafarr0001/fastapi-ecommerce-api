"""
Imports every SQLAlchemy model in one place.

SQLAlchemy and Alembic only know about the tables whose model classes have
been imported. Importing this file guarantees that all of them are loaded
(used by Alembic in `alembic/env.py` and by the seed script).
"""
from app.modules.categories.models import Category
from app.modules.orders.models import Order
from app.modules.products.models import Product
from app.modules.reviews.models import Review
from app.modules.users.models import User

__all__ = ["Category", "Order", "Product", "Review", "User"]
