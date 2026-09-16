"""Module for registering classifications."""

import logging
from typing import cast

from entitysdk.client import Client
from entitysdk.models import (
    Entity,
    ETypeClass,
    ETypeClassification,
    MTypeClass,
    MTypeClassification,
)
from entitysdk.types import ID

L = logging.getLogger(__name__)


def register_etype_classification(
    *, client: Client, entity: Entity, etype_class: ETypeClass
) -> ETypeClassification:
    """Register an ETypeClassification."""
    model = ETypeClassification(
        entity_id=cast(ID, entity.id),
        etype_class_id=cast(ID, etype_class.id),
        authorized_public=True,
    )
    registered_model = client.register_entity(model)
    L.info(
        "Registered ETypeClassification(id=%s) for %s(id=%s) with ETypeClass(id=%s, pref_label=%s)",
        registered_model.id,
        type(entity),
        entity.id,
        etype_class.id,
        etype_class.pref_label,
    )
    return registered_model


def register_mtype_classification(
    *, client: Client, entity: Entity, mtype_class: MTypeClass
) -> MTypeClassification:
    """Register an MTypeClassification."""
    model = MTypeClassification(
        entity_id=entity.id,
        mtype_class_id=mtype_class.id,
        authorized_public=True,
    )
    """Register an MTypeClassification."""
    registered_model = client.register_entity(model)
    L.info(
        "Registered MTypeClassification(id=%s) for %s(id=%s) with MTypeClass(id=%s, pref_label=%s)",
        registered_model.id,
        type(entity),
        entity.id,
        mtype_class.id,
        mtype_class.pref_label,
    )
    return registered_model
