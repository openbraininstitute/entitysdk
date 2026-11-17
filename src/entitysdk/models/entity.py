"""Entity model."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from pydantic import MISSING, Field

from entitysdk.mixin import HasAssets
from entitysdk.models.core import Identifiable
from entitysdk.types import ID, EntityLifecycleStatus, EntityType
from entitysdk.utils.pydantic import RuntimeNullableField


class Entity(Identifiable, HasAssets):
    """Entity is a model with id and authorization."""

    # Server-assigned from the entity route / SQLAlchemy polymorphic identity.
    # Not on EntityCreate; clients must not send it (excluded in serdes).
    type: Annotated[
        EntityType,
        Field(
            examples=["license"],
            description="The type of this Entity (server-assigned).",
        ),
    ] = MISSING  # type: ignore[assignment]
    authorized_public: Annotated[
        bool,
        Field(
            examples=[True, False],
            description="Whether the resource is authorized to be public.",
        ),
    ] = False
    # Present on EntityRead / NestedEntityRead; omitted on NestedEntityBareRead (derivations).
    # RuntimeNullable: omit → MISSING, null → None; excluded from serialize.
    authorized_project_id: Annotated[
        ID,
        RuntimeNullableField,
        Field(
            examples=[UUID("12345678-1234-1234-1234-123456789012")],
            description="The project ID owning the resource (server-assigned).",
        ),
    ] = MISSING  # type: ignore[assignment]
    contributions: Annotated[
        list[Contribution] | None,
        Field(description="The constributions for this entity."),
    ] = MISSING  # type: ignore[assignment]
    legacy_id: Annotated[
        list[str] | None,
        Field(description="Legacy NEXUS ids."),
    ] = MISSING  # type: ignore[assignment]
    lifecycle_status: Annotated[
        EntityLifecycleStatus, Field(description="The lifecycle status of this entity.")
    ] = EntityLifecycleStatus.active

    # entitycore expandable fields use MISSING when not expanded; older responses
    # still send null, so accept None on deserialize while defaulting to MISSING.
    generated_from_derivations: list[Derivation] | None = MISSING  # type: ignore[assignment]
    used_by_derivations: list[Derivation] | None = MISSING  # type: ignore[assignment]


from entitysdk.models.contribution import Contribution  # noqa: E402
from entitysdk.models.derivation import Derivation  # noqa: E402

Entity.model_rebuild()
