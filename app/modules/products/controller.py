"""
Products controller: business logic for products.
"""
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BadRequestError, NotFoundError
from app.core.pagination import paginate
from app.modules.categories.controller import get_category
from app.modules.products.models import Product
from app.modules.products.schemas import ProductCreate, ProductFilters, ProductUpdate
from app.modules.users.controller import check_admin
from app.modules.users.models import User

SORT_COLUMNS = {
    "created_at": Product.created_at,
    "price": Product.price,
    "name": Product.name,
}

ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


def list_products(db: Session, filters: ProductFilters) -> dict:
    if filters.min_price is not None and filters.max_price is not None and filters.min_price > filters.max_price:
        raise BadRequestError("min_price cannot be greater than max_price")

    query = select(Product).where(Product.is_active.is_(True))

    # Each filter is only applied when the client sent it.
    if filters.search:
        pattern = f"%{filters.search}%"
        query = query.where(or_(Product.name.ilike(pattern), Product.description.ilike(pattern)))
    if filters.category_id is not None:
        query = query.where(Product.category_id == filters.category_id)
    if filters.min_price is not None:
        query = query.where(Product.price >= filters.min_price)
    if filters.max_price is not None:
        query = query.where(Product.price <= filters.max_price)
    if filters.in_stock:
        query = query.where(Product.stock > 0)

    column = SORT_COLUMNS[filters.sort_by]
    order = column.asc() if filters.sort_order == "asc" else column.desc()
    query = query.order_by(order, Product.id)  # id as tie-breaker keeps pages stable

    return paginate(db, query, filters)


def get_product(db: Session, product_id: int, include_inactive: bool = False) -> Product:
    product = db.get(Product, product_id)
    if product is None or (not product.is_active and not include_inactive):
        raise NotFoundError("Product not found")
    return product


# ---------- Admin only ----------


def create_product(db: Session, data: ProductCreate, current_user: User) -> Product:
    check_admin(current_user)
    get_category(db, data.category_id)  # raises 404 if the category doesn't exist

    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product_id: int, data: ProductUpdate, current_user: User) -> Product:
    check_admin(current_user)
    # Admins can also edit hidden products (e.g. to set is_active back to true).
    product = get_product(db, product_id, include_inactive=True)
    if data.category_id is not None:
        get_category(db, data.category_id)

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int, current_user: User) -> None:
    """Soft delete: hide the product instead of removing it (old orders still reference it)."""
    check_admin(current_user)
    product = get_product(db, product_id)
    product.is_active = False
    db.commit()


def upload_product_image(db: Session, product_id: int, image: UploadFile, current_user: User) -> Product:
    check_admin(current_user)
    product = get_product(db, product_id, include_inactive=True)

    # Note: content_type is sent by the client. A stricter app would also
    # inspect the file bytes (e.g. with the Pillow library).
    extension = ALLOWED_IMAGE_TYPES.get(image.content_type or "")
    if extension is None:
        raise BadRequestError("Only JPEG, PNG and WEBP images are allowed")

    max_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
    content = image.file.read(max_bytes + 1)  # read at most 1 byte over the limit
    if len(content) > max_bytes:
        raise BadRequestError(f"Image must be smaller than {settings.MAX_IMAGE_SIZE_MB} MB")

    # Random file name: never trust (or reuse) the file name sent by the client.
    filename = f"{uuid.uuid4().hex}{extension}"
    (Path(settings.UPLOAD_DIR) / "products" / filename).write_bytes(content)

    product.image_url = f"/uploads/products/{filename}"
    db.commit()
    db.refresh(product)
    return product
