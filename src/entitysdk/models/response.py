"""Response models."""

from typing import Annotated

from pydantic import BaseModel, Field


class PaginationResponse(BaseModel):
    """Pagination details returned by the entitycore service."""

    page: Annotated[int, Field(ge=1)]
    page_size: Annotated[int, Field(ge=1)]
    total_items: Annotated[int, Field(ge=0)]


class ListResponse(BaseModel):
    """Response returned by the entitycore service."""

    data: list
    pagination: PaginationResponse
