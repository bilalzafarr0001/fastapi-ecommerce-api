"""
Orders routes. Every route here needs a logged-in user.
"""
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Query, status

from app.core.email import send_email
from app.core.pagination import Page
from app.dependencies import CurrentUser, DbSession
from app.modules.notifications.manager import notification_manager
from app.modules.orders import controller
from app.modules.orders.schemas import OrderCreate, OrderFilters, OrderResponse, OrderStatusUpdate

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    data: OrderCreate, db: DbSession, current_user: CurrentUser, background_tasks: BackgroundTasks
):
    """Place an order. Stock is reserved right away and a confirmation email is sent in the background."""
    order = controller.create_order(db, current_user, data)
    background_tasks.add_task(
        send_email,
        to=current_user.email,
        subject=f"Order #{order.id} received",
        body=f"Thanks for your order! Total: ${order.total_amount}",
    )
    return order


@router.get("", response_model=Page[OrderResponse])
def list_orders(db: DbSession, current_user: CurrentUser, params: Annotated[OrderFilters, Query()]):
    """Customers see their own orders, admins see every order. Filter with `?status=paid`."""
    return controller.list_orders(db, current_user, params)


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: DbSession, current_user: CurrentUser):
    """Get one order (your own, or any order if you are an admin)."""
    return controller.get_order(db, order_id, current_user)


@router.post("/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(order_id: int, db: DbSession, current_user: CurrentUser):
    """Cancel your order. Only possible while it is still `pending`. The stock is put back."""
    return controller.cancel_order(db, order_id, current_user)


@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int, data: OrderStatusUpdate, db: DbSession, current_user: CurrentUser, background_tasks: BackgroundTasks
):
    """
    Move an order through its lifecycle. **Admin only.**

    The customer is notified live through the WebSocket
    (try it with the demo page at `/api/v1/notifications/demo`).
    """
    order = controller.update_order_status(db, order_id, data.status, current_user)
    background_tasks.add_task(
        notification_manager.send_to_user,
        user_id=order.user_id,
        message={"event": "order_status_changed", "order_id": order.id, "status": order.status.value},
    )
    return order
