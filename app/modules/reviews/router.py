"""
Reviews routes.

Reviews belong to a product, so listing/creating them uses nested URLs:
    /products/{product_id}/reviews
while editing/deleting one review uses its own id:
    /reviews/{review_id}
That's why this router has no prefix.
"""
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.pagination import Page, PageParams
from app.dependencies import CurrentUser, DbSession
from app.modules.reviews import controller
from app.modules.reviews.schemas import ReviewCreate, ReviewResponse, ReviewSummary, ReviewUpdate

router = APIRouter(tags=["Reviews"])


@router.get("/products/{product_id}/reviews", response_model=Page[ReviewResponse])
def list_product_reviews(product_id: int, db: DbSession, params: Annotated[PageParams, Query()]):
    """List the reviews of a product, newest first. Public."""
    return controller.list_reviews(db, product_id, params)


@router.get("/products/{product_id}/reviews/summary", response_model=ReviewSummary)
def get_review_summary(product_id: int, db: DbSession):
    """Average rating and number of reviews of a product. Public."""
    return controller.get_review_summary(db, product_id)


@router.post(
    "/products/{product_id}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_review(product_id: int, data: ReviewCreate, db: DbSession, current_user: CurrentUser):
    """Review a product you have received (it must be in one of your delivered orders)."""
    return controller.create_review(db, product_id, current_user, data)


@router.patch("/reviews/{review_id}", response_model=ReviewResponse)
def update_review(review_id: int, data: ReviewUpdate, db: DbSession, current_user: CurrentUser):
    """Edit your own review."""
    return controller.update_review(db, review_id, current_user, data)


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(review_id: int, db: DbSession, current_user: CurrentUser):
    """Delete your own review (admins can delete any review)."""
    controller.delete_review(db, review_id, current_user)
