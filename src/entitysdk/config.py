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

    staging_api_url: Annotated[
        str,
        Field(
            alias="ENTITYSDK_STAGING_API_URL",
            description="Default staging entitycore API url.",
        ),
    ] = "https://staging.openbraininstitute.org/api/entitycore"

    production_api_url: Annotated[
        str,
        Field(
            alias="ENTITYSDK_PRODUCTION_API_URL",
            description="Default production entitycore API url.",
        ),
    ] = "https://www.openbraininstitute.org/api/entitycore"

    connect_timeout: Annotated[
        float,
        Field(
            alias="ENTITYSDK_CONNECT_TIMEOUT",
            description="Maximum time to wait until a connection is established, in seconds.",
        ),
    ] = 5
    read_timeout: Annotated[
        float,
        Field(
            alias="ENTITYSDK_READ_TIMEOUT",
            description="Maximum time to wait for a chunk of data to be received, in seconds.",
        ),
    ] = 30
    write_timeout: Annotated[
        float,
        Field(
            alias="ENTITYSDK_WRITE_TIMEOUT",
            description="Maximum time to wait for a chunk of data to be sent, in seconds.",
        ),
    ] = 30
    pool_timeout: Annotated[
        float,
        Field(
            alias="ENTITYSDK_POOL_TIMEOUT",
            description="Maximum time to acquire a connection from the pool, in seconds.",
        ),
    ] = 5


settings = Settings()
