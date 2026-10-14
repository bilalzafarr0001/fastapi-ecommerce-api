"""
Dashboard routes. Admin only.
"""
from fastapi import APIRouter

from app.dependencies import CurrentUser, DbSession
from app.modules.dashboard import controller
from app.modules.dashboard.schemas import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_stats(db: DbSession, current_user: CurrentUser):
    """Store statistics: users, products, orders, revenue and low-stock alerts. **Admin only.**"""
    return controller.get_stats(db, current_user)
