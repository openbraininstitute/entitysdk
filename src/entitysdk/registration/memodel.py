"""Module for registering memodels."""

import logging

from entitysdk import Client
from entitysdk.models import BrainRegion, CellMorphology, EModel, License, MEModel, Species
from entitysdk.registration.classification import (
    register_etype_classification,
    register_mtype_classification,
)
from entitysdk.types import EntityLifecycleStatus, ValidationStatus

L = logging.getLogger(__name__)


def register_memodel(
    *,
    client: Client,
    name: str,
    description: str,
    species: Species,
    brain_region: BrainRegion,
    license: License,  # noqa: A002
    morphology: CellMorphology,
    emodel: EModel,
    threshold_current: float,
    holding_current: float,
    authorized_public: bool,
    validation_status: ValidationStatus,
    lifecycle_status: EntityLifecycleStatus,
) -> MEModel:
    """Register MEModel."""
    memodel = client.register_entity(
        MEModel(
            name=name,
            description=description,
            species=species,
            brain_region=brain_region,
            license=license,
            morphology=morphology,
            emodel=emodel,
            holding_current=holding_current,
            threshold_current=threshold_current,
            lifecycle_status=lifecycle_status,
            validation_status=validation_status,
            authorized_public=authorized_public,
        )
    )

    L.info("Registered MEModel(id=%s, name=%s)", memodel.id, memodel.name)
    for mtype in morphology.mtypes:
        register_mtype_classification(
            client=client,
            entity=memodel,
            mtype_class=mtype,
        )
    for etype in emodel.etypes:
        register_etype_classification(
            client=client,
            entity=memodel,
            etype_class=etype,
        )
    return memodel
