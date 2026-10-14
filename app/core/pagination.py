"""
Reusable pagination.

- PageParams -> the `?page=2&size=20` query parameters, as a Pydantic model.
                Routes read it with `params: Annotated[PageParams, Query()]`.
                Filter models (ProductFilters, UserFilters...) extend it.
- Page[T]    -> a generic response schema: Page[ProductResponse],
                Page[OrderResponse]... all share the same shape.
- paginate() -> runs the COUNT query and the LIMIT/OFFSET query.
"""
import math
from typing import Generic, TypeVar

from pydantic import BaseModel, Field
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

T = TypeVar("T")


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number, starting at 1")
    size: int = Field(default=10, ge=1, le=100, description="Items per page (max 100)")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int


def paginate(db: Session, query: Select, params: PageParams) -> dict:
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    offset = (params.page - 1) * params.size  # page 1 -> skip 0 rows, page 2 -> skip `size` rows...
    items = db.scalars(query.limit(params.size).offset(offset)).all()
    return {
        "items": items,
        "total": total,
        "page": params.page,
        "size": params.size,
        "pages": math.ceil(total / params.size),
    }
