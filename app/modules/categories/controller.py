"""
Categories controller: business logic for categories.
"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.modules.categories.models import Category
from app.modules.categories.schemas import CategoryCreate, CategoryUpdate
from app.modules.products.models import Product


def list_categories(db: Session) -> list[Category]:
    return list(db.scalars(select(Category).order_by(Category.name)))


def get_category(db: Session, category_id: int) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise NotFoundError("Category not found")
    return category


def get_category_by_name(db: Session, name: str) -> Category | None:
    # Case-insensitive: "electronics" and "Electronics" are the same category
    return db.scalar(select(Category).where(func.lower(Category.name) == name.lower()))


def create_category(db: Session, data: CategoryCreate) -> Category:
    if get_category_by_name(db, data.name):
        raise ConflictError(f"Category '{data.name}' already exists")

    category = Category(**data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(db: Session, category_id: int, data: CategoryUpdate) -> Category:
    category = get_category(db, category_id)

    if data.name is not None:
        existing = get_category_by_name(db, data.name)
        if existing and existing.id != category.id:
            raise ConflictError(f"Category '{data.name}' already exists")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int) -> None:
    category = get_category(db, category_id)

    has_products = db.scalar(select(Product.id).where(Product.category_id == category_id).limit(1))
    if has_products:
        raise ConflictError("Cannot delete a category that still has products")

    db.delete(category)
    db.commit()
