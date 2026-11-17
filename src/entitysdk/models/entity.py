"""Entity model."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from pydantic import MISSING, Field

from entitysdk.mixin import HasAssets
from entitysdk.models.core import Identifiable
from entitysdk.types import ID, EntityLifecycleStatus, EntityType


class Entity(Identifiable, HasAssets):
    """Entity is a model with id and authorization."""

    # Name/description are non-nullable on entitycore when present (NameDescriptionMixin).
    # Omit with MISSING for entity types that lack them or when unset on create.
    name: Annotated[
        str | MISSING,
        Field(
            examples=["Entity 1"],
            description="The name of the entity.",
        ),
    ] = MISSING
    description: Annotated[
        str | MISSING,
        Field(
            examples=["This is entity 1"],
            description="The description of the entity.",
        ),
    ] = MISSING
    # Server-assigned from the entity route / SQLAlchemy polymorphic identity.
    # Not on EntityCreate; clients must not send it (excluded in serdes).
    type: Annotated[
        EntityType | MISSING,
        Field(
            examples=["license"],
            description="The type of this Entity (server-assigned).",
        ),
    ] = MISSING
    authorized_public: Annotated[
        bool,
        Field(
            examples=[True, False],
            description="Whether the resource is authorized to be public.",
        ),
    ] = False
    # Server-assigned from project context headers; not on EntityCreate (excluded in serdes).
    authorized_project_id: Annotated[
        ID | MISSING,
        Field(
            examples=[UUID("12345678-1234-1234-1234-123456789012")],
            description="The project ID owning the resource (server-assigned).",
        ),
    ] = MISSING
    contributions: Annotated[
        list[Contribution] | None | MISSING,
        Field(description="The constributions for this entity."),
    ] = MISSING
    legacy_id: Annotated[
        list[str] | None | MISSING,
        Field(description="Legacy NEXUS ids."),
    ] = MISSING
    lifecycle_status: Annotated[
        EntityLifecycleStatus, Field(description="The lifecycle status of this entity.")
    ] = EntityLifecycleStatus.active

    # entitycore expandable fields use MISSING when not expanded; older responses
    # still send null, so accept None on deserialize while defaulting to MISSING.
    generated_from_derivations: list[Derivation] | None | MISSING = MISSING
    used_by_derivations: list[Derivation] | None | MISSING = MISSING


from entitysdk.models.contribution import Contribution  # noqa: E402
from entitysdk.models.derivation import Derivation  # noqa: E402

Entity.model_rebuild()
