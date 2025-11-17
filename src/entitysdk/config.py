"""Configuration for this library."""

from typing import Annotated, Literal

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

    deserialize_model_extra: Annotated[
        Literal["ignore", "forbid"],
        Field(
            alias="ENTITYSDK_DESERIALIZE_MODEL_EXTRA",
            description="How to handle extra fields during the deserialization of models.",
        ),
    ] = "ignore"


settings = Settings()
