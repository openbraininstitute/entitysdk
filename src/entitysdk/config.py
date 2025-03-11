"""Configuration for this library."""

from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Constants for this library."""

    page_size: Annotated[
        int | None,
        Field(
            alias="ENTITYSDK_PAGE_SIZE",
            description="Default pagination page size, or None to use server default.",
        ),
    ] = None


settings = Settings()
