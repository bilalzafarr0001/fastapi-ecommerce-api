"""
Orders controller: placing orders, cancelling them and moving them through
their lifecycle:

    pending -> paid -> shipped -> delivered
       |         |
       +---------+--> cancelled
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, NotFoundError
from app.core.pagination import paginate
from app.modules.orders.models import Order, OrderStatus
from app.modules.orders.schemas import OrderCreate, OrderFilters
from app.modules.products.models import Product
from app.modules.users.controller import check_admin
from app.modules.users.models import User, UserRole

# For each status: which statuses an admin may move the order to.
ALLOWED_STATUS_CHANGES: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING: {OrderStatus.PAID, OrderStatus.CANCELLED},
    OrderStatus.PAID: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}


def create_order(db: Session, user: User, data: OrderCreate) -> Order:
    """
    Reducing the stock and saving the order happen in ONE database
    transaction: if anything fails we raise an error before `db.commit()`,
    so nothing at all is saved.
    """
    # with_for_update() locks the product row until we commit, so two
    # customers can't buy the very last item at the same time.
    product = db.scalar(select(Product).where(Product.id == data.product_id).with_for_update())
    if product is None or not product.is_active:
        raise NotFoundError("Product not found")
    if product.stock < data.quantity:
        raise BadRequestError(f"Not enough stock for '{product.name}' (available: {product.stock})")

    product.stock -= data.quantity
    order = Order(
        user_id=user.id,
        product_id=product.id,
        quantity=data.quantity,
        unit_price=product.price,
        total_amount=product.price * data.quantity,
        shipping_address=data.shipping_address,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def list_orders(db: Session, user: User, params: OrderFilters) -> dict:
    query = select(Order).order_by(Order.created_at.desc(), Order.id.desc())
    if user.role != UserRole.ADMIN:
        query = query.where(Order.user_id == user.id)  # customers only see their own orders
    if params.status is not None:
        query = query.where(Order.status == params.status)
    return paginate(db, query, params)


def get_order(db: Session, order_id: int, user: User) -> Order:
    order = db.get(Order, order_id)
    # A customer asking for someone else's order gets 404 (not 403), so they
    # can't even find out that the order exists.
    if order is None or (user.role != UserRole.ADMIN and order.user_id != user.id):
        raise NotFoundError("Order not found")
    return order


def cancel_order(db: Session, order_id: int, user: User) -> Order:
    order = get_order(db, order_id, user)
    if order.status != OrderStatus.PENDING:
        raise BadRequestError("Only pending orders can be cancelled")

    restore_stock(order)
    order.status = OrderStatus.CANCELLED
    db.commit()
    db.refresh(order)
    return order


def update_order_status(db: Session, order_id: int, new_status: OrderStatus, current_user: User) -> Order:
    """Admin only."""
    check_admin(current_user)
    order = get_order(db, order_id, current_user)
    if new_status not in ALLOWED_STATUS_CHANGES[order.status]:
        raise BadRequestError(f"Cannot change order status from '{order.status.value}' to '{new_status.value}'")

    if new_status == OrderStatus.CANCELLED:
        restore_stock(order)
    order.status = new_status
    db.commit()
    db.refresh(order)
    return order


def restore_stock(order: Order) -> None:
    """Put the quantity of a cancelled order back in stock."""
    order.product.stock += order.quantity
