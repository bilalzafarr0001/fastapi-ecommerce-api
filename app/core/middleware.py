"""
Custom middleware.

A middleware wraps EVERY request:
  - code before `call_next()` runs before the route,
  - code after `call_next()` runs after the route has built the response.
"""
import logging
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("app.requests")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs every request with its duration and adds an `X-Process-Time` header."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)  # <- the route runs here
        duration_ms = (time.perf_counter() - start) * 1000

        response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"
        logger.info("%s %s -> %s (%.2fms)", request.method, request.url.path, response.status_code, duration_ms)
        return response
