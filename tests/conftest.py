"""
Shared test setup (pytest fixtures).

- Tests use a temporary in-memory SQLite database, so they run anywhere and
  never touch your real PostgreSQL data.
- The real `get_db` dependency is swapped for one that uses the test
  database, with `app.dependency_overrides`: one of FastAPI's most useful
  testing features.
"""
import os

# Must be set BEFORE the app is imported, because settings are read at import time.
os.environ["SECRET_KEY"] = "test-secret-key-that-is-at-least-32-characters-long"

from decimal import Decimal  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.database import Base  # noqa: E402
from app.core.security import create_access_token, hash_password  # noqa: E402
from app.dependencies import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.modules.categories.models import Category  # noqa: E402
from app.modules.products.models import Product  # noqa: E402
from app.modules.users.models import User, UserRole  # noqa: E402

PASSWORD = "Password123"

# StaticPool + check_same_thread=False -> every session shares ONE in-memory database.
engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False)


@pytest.fixture
def db():
    """A fresh, empty database for every test."""
    Base.metadata.create_all(engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def no_email_delay(monkeypatch):
    """autouse=True -> applied to every test: skip the fake email delay so tests stay fast."""
    monkeypatch.setattr("app.core.email.FAKE_DELAY_SECONDS", 0)


@pytest.fixture
def client(db: Session):
    """An HTTP client that talks to the app, using the test database."""

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ---------- Helpers ----------


def create_user(db: Session, email: str, role: UserRole = UserRole.CUSTOMER) -> User:
    user = User(email=email, full_name="Test User", hashed_password=hash_password(PASSWORD), role=role)
    db.add(user)
    db.commit()
    return user


def auth_headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


# ---------- Ready-made data ----------


@pytest.fixture
def customer(db: Session) -> User:
    return create_user(db, "customer@example.com")


@pytest.fixture
def admin(db: Session) -> User:
    return create_user(db, "admin@example.com", role=UserRole.ADMIN)


@pytest.fixture
def customer_headers(customer: User) -> dict[str, str]:
    return auth_headers(customer)


@pytest.fixture
def admin_headers(admin: User) -> dict[str, str]:
    return auth_headers(admin)


@pytest.fixture
def category(db: Session) -> Category:
    category = Category(name="Electronics")
    db.add(category)
    db.commit()
    return category


@pytest.fixture
def product(db: Session, category: Category) -> Product:
    product = Product(name="Headphones", price=Decimal("19.99"), stock=10, category=category)
    db.add(product)
    db.commit()
    return product
