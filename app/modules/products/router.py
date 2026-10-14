"""
Products routes: public catalog + admin management.
"""
from typing import Annotated

from fastapi import APIRouter, Query, UploadFile, status

from app.core.pagination import Page
from app.dependencies import CurrentUser, DbSession
from app.modules.products import controller
from app.modules.products.schemas import ProductCreate, ProductFilters, ProductResponse, ProductUpdate

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=Page[ProductResponse])
def list_products(db: DbSession, filters: Annotated[ProductFilters, Query()]):
    """Browse the catalog with search, filters, sorting and pagination. Public."""
    # Annotated[..., Query()] -> FastAPI fills the ProductFilters model from the URL's query parameters
    return controller.list_products(db, filters)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: DbSession):
    """Get one product. Public."""
    return controller.get_product(db, product_id)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, db: DbSession, current_user: CurrentUser):
    """Create a product. **Admin only.**"""
    return controller.create_product(db, data, current_user)


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, data: ProductUpdate, db: DbSession, current_user: CurrentUser):
    """Update a product (send only the fields you want to change). **Admin only.**"""
    return controller.update_product(db, product_id, data, current_user)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: DbSession, current_user: CurrentUser):
    """Hide a product from the catalog (soft delete). **Admin only.**"""
    controller.delete_product(db, product_id, current_user)


@router.post("/{product_id}/image", response_model=ProductResponse)
def upload_product_image(product_id: int, image: UploadFile, db: DbSession, current_user: CurrentUser):
    """
    Upload a product image (JPEG, PNG or WEBP, max `MAX_IMAGE_SIZE_MB`, 2 MB by default)
    as **multipart/form-data**. The image is then served at the returned `image_url`. **Admin only.**
    """
    return controller.upload_product_image(db, product_id, image, current_user)
