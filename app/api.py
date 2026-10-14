"""
All the API routes in one place.

Every module has its own router. Here they are grouped into ONE main router
with the /api/v1 prefix, so main.py only needs a single `include_router()`.

Adding a new module? Import its router and include it below.
"""
from fastapi import APIRouter

from app.core.config import settings
from app.modules.auth.router import router as auth_router
from app.modules.categories.router import router as categories_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.health.router import router as health_router
from app.modules.notifications.router import router as notifications_router
from app.modules.orders.router import router as orders_router
from app.modules.products.router import router as products_router
from app.modules.reviews.router import router as reviews_router
from app.modules.users.router import router as users_router

api_router = APIRouter(prefix=settings.API_V1_PREFIX)

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(categories_router)
api_router.include_router(products_router)
api_router.include_router(orders_router)
api_router.include_router(reviews_router)
api_router.include_router(dashboard_router)
api_router.include_router(notifications_router)
api_router.include_router(health_router)
