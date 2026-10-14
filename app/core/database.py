"""
Database setup (SQLAlchemy 2.0).

- engine        -> manages the connections to PostgreSQL
- SessionLocal  -> creates a new Session (a "conversation" with the DB)
- Base          -> parent class of every model (every table)

The `get_db` dependency that gives each request its own session lives in
`app/dependencies.py`.
"""
from datetime import datetime

from sqlalchemy import DateTime, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,  # check a connection is alive before using it
)

SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    """Every model inherits from this class."""


class TimestampMixin:
    """Adds `created_at` and `updated_at` columns to a model."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
