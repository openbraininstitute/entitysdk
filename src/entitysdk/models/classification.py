"""Classification models."""

from typing import Annotated

from pydantic import MISSING, Field

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
    # Server-assigned from project context headers (excluded in serdes).
    authorized_project_id: Annotated[
        ID | MISSING,
        Field(description="The project ID owning the resource (server-assigned)."),
    ] = MISSING


class MTypeClassification(Classification):
    """Mtype classification model."""

    mtype_class_id: ID


class ETypeClassification(Classification):
    """Etype classification model."""

    etype_class_id: ID
