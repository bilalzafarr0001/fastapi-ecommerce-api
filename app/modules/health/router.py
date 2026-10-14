"""
Health check route: is the API (and its database) up?

Monitoring tools, load balancers and Docker call this URL regularly.
This module is so small that it only needs a router.
"""
from fastapi import APIRouter, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.dependencies import DbSession

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check(db: DbSession, response: Response):
    """Returns 200 when the API and the database are up, 503 otherwise."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "error", "database": "unreachable"}
    return {"status": "ok", "database": "ok"}
