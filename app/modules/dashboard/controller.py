"""
Dashboard controller: store statistics, calculated by the database with
aggregate functions (COUNT, SUM) and GROUP BY.
"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.orders.models import Order, OrderStatus
from app.modules.products.models import Product
from app.modules.users.controller import check_admin
from app.modules.users.models import User

LOW_STOCK_THRESHOLD = 5


def get_stats(db: Session, current_user: User) -> dict:
    check_admin(current_user)

    # SUM gives None when there are no orders yet, so fall back to 0
    total_revenue = db.scalar(
        select(func.sum(Order.total_amount)).where(Order.status != OrderStatus.CANCELLED)
    ) or 0

    # -> [(OrderStatus.PENDING, 3), (OrderStatus.PAID, 1), ...]
    status_counts = dict(db.execute(select(Order.status, func.count(Order.id)).group_by(Order.status)).all())

    low_stock_products = db.scalars(
        select(Product)
        .where(Product.is_active.is_(True), Product.stock < LOW_STOCK_THRESHOLD)
        .order_by(Product.stock)
    ).all()

    return {
        "total_users": db.scalar(select(func.count(User.id))),
        "total_products": db.scalar(select(func.count(Product.id)).where(Product.is_active.is_(True))),
        "total_orders": db.scalar(select(func.count(Order.id))),
        "total_revenue": total_revenue,
        # Every status is listed, even the ones with 0 orders
        "orders_by_status": {status.value: status_counts.get(status, 0) for status in OrderStatus},
        "low_stock_products": low_stock_products,
    }
