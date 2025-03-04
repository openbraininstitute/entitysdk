"""Configuration for this library."""

from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings


class Constants(BaseSettings):
    """Constants for this library."""

    page_size: Annotated[int, Field(description="Default pagination page size.")] = 20


constants = Constants()
