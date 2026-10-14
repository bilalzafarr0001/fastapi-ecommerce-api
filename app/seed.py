"""
Fill the database with demo data so you can try the API right away.

Run it once, after `alembic upgrade head`:

    python -m app.seed
"""
from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import Category, Order, Product, Review, User
from app.modules.orders.models import OrderStatus
from app.modules.users.models import UserRole

ADMIN_EMAIL, ADMIN_PASSWORD = "admin@shopsphere.com", "Admin12345"
CUSTOMER_EMAIL, CUSTOMER_PASSWORD = "john@example.com", "Customer123"

# category -> [(name, description, price, stock), ...]
CATALOG = {
    "Electronics": [
        ("Wireless Headphones", "Noise-cancelling over-ear headphones with 30h battery.", "59.99", 25),
        ("Smartphone X200", "6.5-inch display, 128 GB storage, dual camera.", "499.00", 10),
        ("USB-C Charger 65W", "Fast charger for laptops and phones.", "29.90", 3),
    ],
    "Books": [
        ("Clean Code", "A handbook of agile software craftsmanship.", "34.50", 40),
        ("Learning Python", "A complete introduction to Python programming.", "45.00", 15),
    ],
    "Clothing": [
        ("Classic White T-Shirt", "100% organic cotton.", "15.00", 100),
        ("Denim Jacket", "Timeless blue denim jacket.", "79.99", 0),
    ],
    "Home & Kitchen": [
        ("Coffee Maker", "12-cup programmable coffee maker.", "89.00", 8),
        ("Chef Knife", "8-inch stainless steel chef knife.", "39.95", 20),
    ],
}


def seed() -> None:
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == ADMIN_EMAIL)):
            print("The database already has demo data. Nothing to do.")
            return

        admin = User(
            email=ADMIN_EMAIL,
            full_name="Store Admin",
            hashed_password=hash_password(ADMIN_PASSWORD),
            role=UserRole.ADMIN,
        )
        customer = User(
            email=CUSTOMER_EMAIL,
            full_name="John Doe",
            hashed_password=hash_password(CUSTOMER_PASSWORD),
        )
        db.add_all([admin, customer])

        products = []
        for category_name, items in CATALOG.items():
            category = Category(name=category_name)
            for name, description, price, stock in items:
                products.append(
                    Product(name=name, description=description, price=Decimal(price), stock=stock, category=category)
                )
        db.add_all(products)

        # Two delivered orders for John, so he can write reviews right away.
        headphones, book = products[0], products[3]
        for product in (headphones, book):
            db.add(
                Order(
                    user=customer,
                    product=product,
                    quantity=1,
                    unit_price=product.price,
                    total_amount=product.price,
                    status=OrderStatus.DELIVERED,
                    shipping_address="221B Baker Street, London",
                )
            )
        db.add(Review(user=customer, product=headphones, rating=5, comment="Amazing sound quality!"))

        db.commit()

    print("Demo data created!")
    print(f"  Admin    -> {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    print(f"  Customer -> {CUSTOMER_EMAIL} / {CUSTOMER_PASSWORD}")


if __name__ == "__main__":
    seed()
