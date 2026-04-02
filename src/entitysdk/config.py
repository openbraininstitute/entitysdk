"""Configuration for this library."""

from typing import Annotated, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Constants for this library."""

    model_config = SettingsConfigDict(
        env_prefix="ENTITYSDK_",
        case_sensitive=False,
    )
    page_size: Annotated[
        int | None,
        Field(
            description="Default pagination page size, or None to use server default.",
        ),
    ] = None
    staging_api_url: Annotated[
        str,
        Field(
            description="Default staging entitycore API url.",
        ),
    ] = "https://staging.cell-a.openbraininstitute.org/api/entitycore"
    production_api_url: Annotated[
        str,
        Field(
            description="Default production entitycore API url.",
        ),
    ] = "https://cell-a.openbraininstitute.org/api/entitycore"
    connect_timeout: Annotated[
        float,
        Field(
            description="Maximum time to wait until a connection is established, in seconds.",
        ),
    ] = 5
    read_timeout: Annotated[
        float,
        Field(
            description="Maximum time to wait for a chunk of data to be received, in seconds.",
        ),
    ] = 30
    write_timeout: Annotated[
        float,
        Field(
            description="Maximum time to wait for a chunk of data to be sent, in seconds.",
        ),
    ] = 30
    pool_timeout: Annotated[
        float,
        Field(
            description="Maximum time to acquire a connection from the pool, in seconds.",
        ),
    ] = 5
    deserialize_model_extra: Annotated[
        Literal["ignore", "forbid"],
        Field(
            description="How to handle extra fields during the deserialization of models.",
        ),
    ] = "ignore"
    download_stream_data_buffer_size: Annotated[
        int, Field(description="The chunk size when streaming a file to a file.")
    ] = 256 * 1024


settings = Settings()
