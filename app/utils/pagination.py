from typing import TypeVar, Generic, Sequence
from pydantic import BaseModel

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: Sequence[T]
    total: int
    skip: int
    limit: int

def paginate(items: Sequence[T], total: int, skip: int, limit: int) -> PaginatedResponse[T]:
    return PaginatedResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )
