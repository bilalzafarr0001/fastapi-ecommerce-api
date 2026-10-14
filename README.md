# ShopSphere API

An e-commerce REST API built with **FastAPI**, **SQLAlchemy 2.0**, **PostgreSQL** and **Alembic**.

Customers browse a catalog, place orders, follow them live and review what they bought.
Admins manage the catalog, move orders through their lifecycle and watch store statistics.

The project is written to **learn FastAPI from the basics up to advanced topics**: every module
uses the same simple structure, and the [learning path](#learning-path-fastapi-from-basic-to-advanced)
below points to the exact file where each feature is used.

---

## Features

| Module | What it does |
|---|---|
| **auth** | Register, log in (JWT access + refresh tokens), refresh tokens |
| **users** | Your profile, change password; admins list users, change roles, disable accounts |
| **categories** | Product categories (public read, admin write) |
| **products** | Catalog with search, filters, sorting, pagination, image upload, soft delete |
| **orders** | Place orders (stock is locked and reserved), cancel, status workflow `pending → paid → shipped → delivered` |
| **reviews** | 1–5 star reviews, only for products from your **delivered** orders, one per product |
| **dashboard** | Admin statistics: revenue, orders per status, low-stock alerts |
| **notifications** | Live WebSocket notifications when an order status changes |

---

## Project structure

```
fast-api-sample-project/
├── app/
│   ├── main.py              # Creates the app: middleware, error handlers, static files, routes
│   ├── api.py               # Groups every module's router under /api/v1
│   ├── dependencies.py      # The 2 shared dependencies: get_db, get_current_user
│   ├── models.py            # Imports every model (needed by Alembic)
│   ├── seed.py              # Demo data: python -m app.seed
│   │
│   ├── core/                # Building blocks used by every module
│   │   ├── config.py        # Settings read from .env
│   │   ├── database.py      # Engine, SessionLocal, Base, TimestampMixin
│   │   ├── security.py      # Password hashing + JWT tokens
│   │   ├── exceptions.py    # Custom errors (NotFoundError...) + handlers
│   │   ├── middleware.py    # Request logging + X-Process-Time header
│   │   ├── pagination.py    # PageParams, Page[T], paginate()
│   │   ├── schemas.py       # RequestSchema / ResponseSchema base classes
│   │   └── email.py         # Fake email sender (used by background tasks)
│   │
│   └── modules/             # One folder per feature, always the same files:
│       ├── users/
│       │   ├── models.py      # SQLAlchemy model = database table
│       │   ├── schemas.py     # Pydantic schemas (DTOs) = shape of requests/responses
│       │   ├── controller.py  # Business logic + database queries
│       │   └── router.py      # HTTP routes (thin: validate -> call controller -> respond)
│       ├── auth/            # (no models.py: it uses the User model)
│       ├── categories/
│       ├── products/
│       ├── orders/
│       ├── reviews/
│       ├── dashboard/       # (no models.py: only statistics queries)
│       ├── notifications/   # WebSocket: router.py + manager.py + demo.html
│       └── health/          # (only router.py: a tiny health check)
│
├── alembic/                 # Database migrations
├── tests/                   # Pytest tests (in-memory SQLite, no PostgreSQL needed)
├── uploads/                 # Uploaded product images (served at /uploads/...)
├── .env / .env.example      # Configuration
├── requirements.txt
├── Dockerfile / docker-compose.yml   # Optional
└── README.md
```

### How a request flows through the code

```
HTTP request
   │
   ▼
Middleware (core/middleware.py, CORS)           -> runs for every request
   │
   ▼
router.py        -> FastAPI validates the input with schemas.py (422 if invalid)
   │                and runs the dependencies (DB session, current user, admin check...)
   ▼
controller.py    -> business rules + database work with models.py
   │                raises NotFoundError / ConflictError... when something is wrong
   ▼
router.py        -> returns the object; `response_model` turns it into JSON
   │                (and hides fields like hashed_password)
   ▼
HTTP response    (+ background tasks run AFTER the response is sent)
```

---

## Getting started (Windows / PowerShell)

### 1. Install the dependencies

```powershell
python -m venv .venv                 # already done if the .venv folder exists
.\.venv\Scripts\Activate.ps1         # activate it (your prompt now starts with (.venv))
pip install -r requirements.txt
```

> If PowerShell refuses to run `Activate.ps1`, run this once:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### 2. Create the PostgreSQL database

With **pgAdmin** (right click *Databases* → *Create* → name it `shopsphere`) or from the terminal:

```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -c "CREATE DATABASE shopsphere;"
```

### 3. Configure `.env`

Open `.env` and put **your PostgreSQL password** in `DATABASE_URL`:

```
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/shopsphere
```

(`.env.example` documents every setting. Set `DB_ECHO=true` to see every SQL query in the console.)

### 4. Create the tables, add demo data, start the server

```powershell
alembic upgrade head             # creates all the tables
python -m app.seed               # demo users, categories, products, an order and a review
uvicorn app.main:app --reload    # --reload restarts the server when you edit code
```

Open **http://127.0.0.1:8000/docs**

| Demo account | Email | Password |
|---|---|---|
| Admin | `admin@shopsphere.com` | `Admin12345` |
| Customer | `john@example.com` | `Customer123` |

---

## Try it in Swagger UI (`/docs`)

1. Click **Authorize** (top right). Type the customer email in **username**, the password, then **Authorize**.
2. `GET /api/v1/products?search=phone&sort_by=price&sort_order=asc`: browse the catalog.
3. `POST /api/v1/orders`: buy something:
   ```json
   { "product_id": 2, "quantity": 1, "shipping_address": "12 Mall Road, Lahore" }
   ```
   Look at the server console: about 2 seconds later the confirmation "email" (a background task) is logged.
4. Open **http://127.0.0.1:8000/api/v1/notifications/demo** in another tab, paste the customer's
   access token (from `POST /auth/login`) and click **Connect**.
5. Back in Swagger, **Logout**, then **Authorize** as the admin and call
   `PATCH /api/v1/orders/{order_id}/status` with `{"status": "paid"}`.
   The notification appears live in the demo tab.
6. Continue to `shipped` then `delivered`, then as the customer `POST /api/v1/products/2/reviews`.
7. As admin: `GET /api/v1/dashboard/stats`.

Also try to break things: wrong passwords, negative prices, `min_price` > `max_price`,
ordering more than the stock, reviewing a product you never received... and read the error messages.

---

## API endpoints

All routes are prefixed with `/api/v1`.
🔓 public · 👤 logged-in user · 🛡️ admin only

| Method | Path | Access | Description |
|---|---|---|---|
| POST | `/auth/register` | 🔓 | Create a customer account (welcome email in background) |
| POST | `/auth/login` | 🔓 | Get access + refresh tokens (form data) |
| POST | `/auth/refresh` | 🔓 | Exchange a refresh token for new tokens |
| GET | `/users/me` | 👤 | Your profile |
| PATCH | `/users/me` | 👤 | Update your name / email |
| POST | `/users/me/change-password` | 👤 | Change your password |
| GET | `/users` | 🛡️ | List users (search, role filter, pagination) |
| GET | `/users/{user_id}` | 🛡️ | Get a user |
| PATCH | `/users/{user_id}` | 🛡️ | Change role / activate / deactivate |
| GET | `/categories` | 🔓 | List categories |
| GET | `/categories/{category_id}` | 🔓 | Get a category with its products (from `category.products`) |
| POST | `/categories` | 🛡️ | Create a category |
| PATCH | `/categories/{category_id}` | 🛡️ | Update a category |
| DELETE | `/categories/{category_id}` | 🛡️ | Delete a category (409 if it has products) |
| GET | `/products` | 🔓 | Search, filter, sort, paginate |
| GET | `/products/{product_id}` | 🔓 | Get a product |
| POST | `/products` | 🛡️ | Create a product |
| PATCH | `/products/{product_id}` | 🛡️ | Update a product |
| DELETE | `/products/{product_id}` | 🛡️ | Hide a product (soft delete) |
| POST | `/products/{product_id}/image` | 🛡️ | Upload an image (multipart) |
| POST | `/orders` | 👤 | Place an order |
| GET | `/orders` | 👤 | Your orders (admins: all orders), `?status=` filter |
| GET | `/orders/{order_id}` | 👤 | Get an order (yours, or any for admins) |
| POST | `/orders/{order_id}/cancel` | 👤 | Cancel your pending order (stock is restored) |
| PATCH | `/orders/{order_id}/status` | 🛡️ | Change status (+ live WebSocket notification) |
| GET | `/products/{product_id}/reviews` | 🔓 | Reviews of a product |
| GET | `/products/{product_id}/reviews/summary` | 🔓 | Average rating + count |
| POST | `/products/{product_id}/reviews` | 👤 | Review a product you received |
| PATCH | `/reviews/{review_id}` | 👤 | Edit your review |
| DELETE | `/reviews/{review_id}` | 👤 | Delete your review (admins: any review) |
| GET | `/dashboard/stats` | 🛡️ | Store statistics |
| WS | `/notifications/ws?token=...` | 👤 | Live notifications |
| GET | `/health` | 🔓 | API + database health check |

---

## Learning path: FastAPI from basic to advanced

Suggested reading order: `main.py` + `api.py` → `core/config.py` + `core/database.py` → the **categories**
module (the simplest CRUD) → `dependencies.py` → **auth** + **users** → **products** →
**orders** → **reviews** + **dashboard** → **notifications** → `tests/`.

### Level 1: Basics

| Feature | Where |
|---|---|
| Routes: `@router.get/post/patch/delete` | any `router.py`, start with `categories/router.py` |
| Path parameters (`category_id: int`, converted and validated automatically) | `categories/router.py` |
| Query parameters with validation: `Query(min_length=2)` | `users/router.py` → `list_users` |
| Request body = a Pydantic model | `categories/schemas.py` → `CategoryCreate` |
| `response_model` (filters the output, e.g. never returns passwords) | `users/schemas.py` → `UserResponse` |
| Status codes: `201 Created`, `204 No Content` | `categories/router.py` |
| Enums as allowed values | `users/models.py` → `UserRole`, `orders/models.py` → `OrderStatus` |
| Automatic docs: docstrings, tags, `Field(examples=...)` | any `router.py`, `products/schemas.py` |
| Routers inside a router (`include_router`) | `api.py` |

### Level 2: Validation, responses and errors

| Feature | Where |
|---|---|
| `Field` constraints: lengths, `gt`/`ge`/`le`, decimals | `products/schemas.py` |
| `EmailStr` | `auth/schemas.py` |
| `@field_validator` (check and clean one field) | `orders/schemas.py` → `clean_shipping_address` |
| `@model_validator` (compare fields) | `users/schemas.py` → `ChangePasswordRequest` |
| Reusable validated type: `Annotated[str, Field(...), AfterValidator(...)]` | `users/schemas.py` → `Password` |
| Reject unknown fields: `extra="forbid"` | `core/schemas.py` → `RequestSchema` |
| Build responses from ORM objects: `from_attributes=True` | `core/schemas.py` → `ResponseSchema` |
| Nested schemas | `products/schemas.py` → `ProductResponse.category` |
| `@computed_field` | `products/schemas.py` → `ProductResponse.in_stock` |
| Generic schema `Page[T]` | `core/pagination.py` |
| Partial updates (PATCH): `model_dump(exclude_none=True)` | `products/controller.py` → `update_product` |
| `HTTPException` | `dependencies.py` |
| Custom exceptions + exception handlers | `core/exceptions.py` |
| Query parameters as a Pydantic model: `Annotated[ProductFilters, Query()]` | `products/router.py`, `products/schemas.py` |
| Form data (`Form()`) | `auth/router.py` → `login` |
| File upload (`UploadFile`) + size/type checks | `products/router.py`, `products/controller.py` |
| Static files | `main.py` → `app.mount("/uploads", ...)` |
| `Response` parameter (change status code), `HTMLResponse` | `health/router.py`, `notifications/router.py` |

### Level 3: Dependency injection

The project has only **two** dependencies, both in `dependencies.py`: `get_db` and `get_current_user`.

| Feature | Where |
|---|---|
| Dependency with `yield` (open/close a DB session) | `dependencies.py` → `get_db` |
| A dependency that uses another one: `get_current_user` → `get_db` | `dependencies.py` |
| `Annotated` shortcuts: `DbSession`, `CurrentUser` | `dependencies.py` |
| Overriding dependencies in tests: `app.dependency_overrides` | `tests/conftest.py` |

### Level 4: Security

| Feature | Where |
|---|---|
| Password hashing (Argon2) | `core/security.py` |
| JWT access + refresh tokens (expiry, token type) | `core/security.py`, `auth/controller.py` |
| `OAuth2PasswordBearer` + the Swagger **Authorize** button | `dependencies.py` |
| Role-based access (customer / admin): first line of every admin-only controller function | `users/controller.py` → `check_admin` |
| Ownership checks (404 instead of 403 to hide other people's data) | `orders/controller.py` → `get_order` |
| CORS | `main.py` |

### Level 5: Database (SQLAlchemy 2.0 + Alembic)

| Feature | Where |
|---|---|
| Typed models: `Mapped[...]`, `mapped_column` | any `models.py` |
| One-to-many / many-to-one relationships | `users/models.py` (one user → many orders), `orders/models.py` (many orders → one user / product) |
| Avoiding the N+1 problem: `lazy="selectin"` | `products/models.py` |
| Unique + check constraints | `reviews/models.py` |
| Search (`ilike`), filters, sorting, pagination | `products/controller.py` → `list_products` |
| Aggregates: `COUNT`, `SUM`, `AVG`, `GROUP BY` | `dashboard/controller.py`, `reviews/controller.py` |
| Transactions + row locking (`with_for_update`) | `orders/controller.py` → `create_order` |
| Soft delete | `products/controller.py` → `delete_product` |
| Migrations | `alembic/`, see [Database migrations](#database-migrations) |

### Level 6: Advanced

| Feature | Where |
|---|---|
| Background tasks | `auth/router.py`, `orders/router.py` |
| WebSockets (with token authentication) | `notifications/router.py`, `notifications/manager.py` |
| Custom middleware | `core/middleware.py` |
| Lifespan (startup / shutdown) | `main.py` → `lifespan` |
| Settings with `pydantic-settings` | `core/config.py` |
| Testing: `TestClient`, fixtures, WebSocket tests | `tests/` |

### Why `def` and not `async def` in the routes?

SQLAlchemy is used in its normal (synchronous) mode here because it is simpler to learn.
FastAPI runs `def` routes in a **thread pool**, so a slow database query never blocks the server.
Use `async def` only when everything you wait for inside is async, like the WebSocket route in
`notifications/router.py`. Calling blocking code (like a sync DB query) inside `async def` WOULD
block the whole server.

---

## Running the tests

```powershell
pytest            # or: pytest -v  for one line per test
```

The tests use an in-memory SQLite database (through `app.dependency_overrides`), so they don't
need PostgreSQL and never touch your data.

---

## Database migrations

When you change a model (for example, add a column):

```powershell
alembic revision --autogenerate -m "add phone to users"   # creates a file in alembic/versions/
# open the new file and check it! autogenerate is good, not perfect
alembic upgrade head                                      # apply it
alembic downgrade -1                                      # undo the last one if needed
```

---

## How to add a new module (example: wishlist)

1. Create `app/modules/wishlist/` with `__init__.py`, `models.py`, `schemas.py`, `controller.py`, `router.py`.
2. Import the new model in `app/models.py` (so Alembic sees it).
3. Include the router in `app/api.py`: `api_router.include_router(wishlist_router)`.
4. `alembic revision --autogenerate -m "add wishlist"` then `alembic upgrade head`.
5. Add tests in `tests/test_wishlist.py`.

---

## Docker (optional)

```powershell
docker compose up --build                  # PostgreSQL + API on http://127.0.0.1:8000
docker compose exec api python -m app.seed # demo data
```
