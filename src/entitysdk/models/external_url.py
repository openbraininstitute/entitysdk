"""External Url models."""

from pydantic import HttpUrl

from entitysdk.models.core import Identifiable
from entitysdk.types import ExternalSource


class ExternalUrl(Identifiable):
    """External Url model."""

    name: str
    description: str
    source: ExternalSource
    url: HttpUrl
    source_name: str | None = None
