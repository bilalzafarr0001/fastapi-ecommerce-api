"""
Categories routes: anyone can read, only admins can write.
"""
from fastapi import APIRouter, status

from app.dependencies import CurrentUser, DbSession
from app.modules.categories import controller
from app.modules.categories.schemas import CategoryCreate, CategoryResponse, CategoryUpdate, CategoryWithProducts

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=list[CategoryResponse])
def list_categories(db: DbSession):
    """List all categories. Public."""
    return controller.list_categories(db)


@router.get("/{category_id}", response_model=CategoryWithProducts)
def get_category(category_id: int, db: DbSession):
    """Get one category with its visible products. Public."""
    return controller.get_category(db, category_id)


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(data: CategoryCreate, db: DbSession, current_user: CurrentUser):
    """Create a category. **Admin only.**"""
    return controller.create_category(db, data, current_user)


@router.patch("/{category_id}", response_model=CategoryResponse)
def update_category(category_id: int, data: CategoryUpdate, db: DbSession, current_user: CurrentUser):
    """Update a category (send only the fields you want to change). **Admin only.**"""
    return controller.update_category(db, category_id, data, current_user)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: DbSession, current_user: CurrentUser):
    """Delete a category. Fails with 409 if it still has products. **Admin only.**"""
    controller.delete_category(db, category_id, current_user)
