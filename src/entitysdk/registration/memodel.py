"""Module for registering memodels."""

import logging

from entitysdk import Client
from entitysdk.models import (
    BrainRegion,
    CellMorphology,
    EModel,
    License,
    MEModel,
    MEModelCalibrationResult,
    Species,
)
from entitysdk.registration.classification import (
    register_etype_classification,
    register_mtype_classification,
)
from entitysdk.types import ID, EntityLifecycleStatus, ValidationStatus

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
    for mtype in morphology.mtypes or []:
        register_mtype_classification(
            client=client,
            entity=memodel,
            mtype_class=mtype,
        )
    for etype in emodel.etypes or []:
        register_etype_classification(
            client=client,
            entity=memodel,
            etype_class=etype,
        )
    return memodel


def register_memodel_calibration_result(
    *,
    client: Client,
    calibrated_entity_id: ID,
    holding_current: float,
    threshold_current: float,
    rin: float | None,
    authorized_public: bool,
) -> MEModelCalibrationResult | None:
    """Register a MEModelCalibrationResult for a MEModel.

    Skips registration when a calibration result already exists for
    ``calibrated_entity_id``.

    Returns:
        The registered MEModelCalibrationResult, or ``None`` if it already existed.
    """
    existing = client.search_entity(
        entity_type=MEModelCalibrationResult,
        query={"calibrated_entity_id": calibrated_entity_id},
    ).first()
    if existing is not None:
        L.info(
            "MEModelCalibrationResult already exists for %s; skipping.",
            calibrated_entity_id,
        )
        return None

    result = client.register_entity(
        MEModelCalibrationResult(
            holding_current=holding_current,
            threshold_current=threshold_current,
            rin=rin,
            calibrated_entity_id=calibrated_entity_id,
            authorized_public=authorized_public,
        )
    )
    L.info(
        "Registered MEModelCalibrationResult(id=%s, calibrated_entity_id=%s)",
        result.id,
        calibrated_entity_id,
    )
    return result
