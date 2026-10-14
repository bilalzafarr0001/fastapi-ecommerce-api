"""
Reviews controller.

Business rules:
  - only customers who RECEIVED the product (delivered order) can review it,
  - one review per product per user,
  - only the author can edit a review; the author or an admin can delete it.
"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.pagination import PageParams, paginate
from app.modules.orders.models import Order, OrderStatus
from app.modules.products.controller import get_product
from app.modules.reviews.models import Review
from app.modules.reviews.schemas import ReviewCreate, ReviewUpdate
from app.modules.users.models import User, UserRole


def list_reviews(db: Session, product_id: int, params: PageParams) -> dict:
    get_product(db, product_id)  # 404 if the product doesn't exist
    query = (
        select(Review)
        .where(Review.product_id == product_id)
        .order_by(Review.created_at.desc(), Review.id.desc())
    )
    return paginate(db, query, params)


def get_review_summary(db: Session, product_id: int) -> dict:
    get_product(db, product_id)
    # Aggregate functions: let the database calculate the average and the count.
    average, count = db.execute(
        select(func.avg(Review.rating), func.count(Review.id)).where(Review.product_id == product_id)
    ).one()
    return {
        "product_id": product_id,
        "average_rating": round(float(average), 1) if average is not None else None,
        "review_count": count,
    }


def has_received_product(db: Session, user_id: int, product_id: int) -> bool:
    order_id = db.scalar(
        select(Order.id)
        .where(
            Order.user_id == user_id,
            Order.product_id == product_id,
            Order.status == OrderStatus.DELIVERED,
        )
        .limit(1)
    )
    return order_id is not None


def create_review(db: Session, product_id: int, user: User, data: ReviewCreate) -> Review:
    get_product(db, product_id)

    if not has_received_product(db, user.id, product_id):
        raise ForbiddenError("You can only review products from your delivered orders")

    already_reviewed = db.scalar(
        select(Review.id).where(Review.user_id == user.id, Review.product_id == product_id)
    )
    if already_reviewed:
        raise ConflictError("You have already reviewed this product")

    review = Review(**data.model_dump(), user_id=user.id, product_id=product_id)
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def get_review(db: Session, review_id: int) -> Review:
    review = db.get(Review, review_id)
    if review is None:
        raise NotFoundError("Review not found")
    return review


def update_review(db: Session, review_id: int, user: User, data: ReviewUpdate) -> Review:
    review = get_review(db, review_id)
    if review.user_id != user.id:
        raise ForbiddenError("You can only edit your own reviews")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(review, field, value)

    db.commit()
    db.refresh(review)
    return review


def delete_review(db: Session, review_id: int, user: User) -> None:
    review = get_review(db, review_id)
    if review.user_id != user.id and user.role != UserRole.ADMIN:
        raise ForbiddenError("You can only delete your own reviews")

    db.delete(review)
    db.commit()
