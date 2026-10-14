"""
Application entry point: creates the FastAPI app and plugs everything in.

Run:   uvicorn app.main:app --reload
Docs:  http://127.0.0.1:8000/docs
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import AppError, app_error_handler
from app.core.middleware import RequestLoggingMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Server is starting")  # runs ONCE when the server starts
    yield  # <- the app handles requests while we are here
    engine.dispose()  # runs ONCE when the server stops: close the database connections


# 1. Create the app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    swagger_ui_parameters={"persistAuthorization": True},  # keep your token after a page refresh
)

# 2. Middleware: code that runs around every request
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Error handler: turn our custom errors (NotFoundError...) into JSON responses
app.add_exception_handler(AppError, app_error_handler)

# 4. Static files: uploaded images are served at /uploads/...
Path(settings.UPLOAD_DIR, "products").mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# 5. Routes: every module's routes, all under /api/v1 (see app/api.py)
app.include_router(api_router)
