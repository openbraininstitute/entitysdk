"""Tests for MEModel registration."""

import uuid

from entitysdk.models import BrainRegion, CellMorphology, EModel, ETypeClass, License, MEModel, MTypeClass, Species
from entitysdk.registration.memodel import register_memodel
from entitysdk.types import EntityLifecycleStatus, ValidationStatus

from .conftest import load_extracted_json


def _memodel_registration_kwargs(
    *,
    morphology_mtypes: list[MTypeClass] | None,
    emodel_etypes: list[ETypeClass] | None,
) -> dict:
    memodel_payload = load_extracted_json("memodel")
    morphology_payload = load_extracted_json("cell-morphology")
    emodel_payload = load_extracted_json("emodel")
    morphology = CellMorphology.model_validate(morphology_payload).model_copy(
        update={"mtypes": morphology_mtypes},
    )
    emodel = EModel.model_validate(emodel_payload).model_copy(update={"etypes": emodel_etypes})
    return {
        "name": memodel_payload["name"],
        "description": memodel_payload["description"],
        "species": Species.model_validate(memodel_payload["species"]),
        "brain_region": BrainRegion.model_validate(memodel_payload["brain_region"]),
        "license": License.model_validate(load_extracted_json("license")),
        "morphology": morphology,
        "emodel": emodel,
        "threshold_current": memodel_payload.get("threshold_current", 0.1),
        "holding_current": memodel_payload.get("holding_current", -0.1),
        "authorized_public": memodel_payload["authorized_public"],
        "validation_status": ValidationStatus(memodel_payload["validation_status"]),
        "lifecycle_status": EntityLifecycleStatus(memodel_payload["lifecycle_status"]),
    }


def test_register_memodel_registers_classifications(client, register_entity_responder):
    register_entity_responder(("memodel", "mtype-classification", "etype-classification"))

    mtype_class = MTypeClass.model_validate(load_extracted_json("mtype"))
    etype_class = ETypeClass.model_validate(load_extracted_json("etype"))
    kwargs = _memodel_registration_kwargs(
        morphology_mtypes=[mtype_class],
        emodel_etypes=[etype_class],
    )

    registered = register_memodel(client=client, **kwargs)

    assert isinstance(registered, MEModel)
    assert registered.id is not None
    assert registered.name == kwargs["name"]


def test_register_memodel_skips_missing_classifications(client, register_entity_responder):
    register_entity_responder(("memodel",))

    registered = register_memodel(
        client=client,
        **_memodel_registration_kwargs(morphology_mtypes=None, emodel_etypes=None),
    )

    assert registered.id is not None


def test_register_memodel_skips_empty_classification_lists(client, register_entity_responder):
    register_entity_responder(("memodel",))

    registered = register_memodel(
        client=client,
        **_memodel_registration_kwargs(morphology_mtypes=[], emodel_etypes=[]),
    )

    assert registered.id is not None
