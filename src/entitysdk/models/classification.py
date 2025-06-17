"""Classification models."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.core import Identifiable
from entitysdk.types import ID


class Classification(Identifiable):
    """Classification base model."""

    entity_id: ID
    authorized_public: Annotated[
        bool,
        Field(
            description="Whether the resource is authorized to be public.",
        ),
    ] = False
    authorized_project_id: Annotated[
        ID | None,
        Field(
            description="The project ID the resource is authorized to be public.",
        ),
    ] = None


class MTypeClassification(Classification):
    """Mtype classification model."""

    mtype_class_id: ID


class ETypeClassification(Classification):
    """Etype classification model."""

    etype_class_id: ID
