"""Tests for EModel registration."""

import uuid
from pathlib import Path

from entitysdk.models import (
    BrainRegion,
    CellMorphology,
    EModel,
    ETypeClass,
    IonChannelModel,
    License,
    Species,
)
from entitysdk.registration.emodel import register_emodel
from entitysdk.types import EntityLifecycleStatus

from .conftest import load_extracted_json


def _emodel_registration_kwargs(
    tmp_path: Path,
    *,
    trace_ids: list[uuid.UUID] | None = None,
    figure_files: list[Path] | None = None,
) -> dict:
    emodel_payload = load_extracted_json("emodel")
    morphology_payload = load_extracted_json("cell-morphology")
    return {
        "name": emodel_payload["name"],
        "description": emodel_payload["description"],
        "authorized_public": emodel_payload["authorized_public"],
        "species": Species.model_validate(emodel_payload["species"]),
        "brain_region": BrainRegion.model_validate(emodel_payload["brain_region"]),
        "license": License.model_validate(load_extracted_json("license")),
        "seed": emodel_payload["seed"],
        "iteration": emodel_payload["iteration"],
        "score": emodel_payload["score"],
        "exemplar_morphology": CellMorphology.model_validate(morphology_payload),
        "ion_channel_models": [
            IonChannelModel.model_validate(load_extracted_json("ion-channel-model")),
        ],
        "lifecycle_status": EntityLifecycleStatus(emodel_payload["lifecycle_status"]),
        "etype_class": ETypeClass.model_validate(load_extracted_json("etype")),
        "hoc_file": tmp_path / "model.hoc",
        "emodel_summary_file": tmp_path / "summary.json",
        "electrical_cell_recording_ids": trace_ids or [uuid.uuid4()],
        "validation_result_figure_files": figure_files or [tmp_path / "figure.png"],
        "validateion_result_status": False,
    }


def test_register_emodel(client, tmp_path, register_entity_responder, upload_file_responder):
    register_entity_responder()
    upload_file_responder()

    kwargs = _emodel_registration_kwargs(tmp_path)
    kwargs["hoc_file"].write_text("hoc-content")
    kwargs["emodel_summary_file"].write_text("{}")
    kwargs["validation_result_figure_files"][0].write_bytes(b"png-content")

    registered = register_emodel(client=client, **kwargs)

    assert isinstance(registered, EModel)
    assert registered.id is not None
    assert registered.name == kwargs["name"]
    assert registered.score == kwargs["score"]
    assert registered.iteration == kwargs["iteration"]


def test_register_emodel_registers_multiple_traces_and_figures(
    client,
    tmp_path,
    register_entity_responder,
    upload_file_responder,
):
    register_entity_responder()
    upload_file_responder()

    figure_one = tmp_path / "figure-one.pdf"
    figure_two = tmp_path / "figure-two.png"
    figure_one.write_bytes(b"pdf-content")
    figure_two.write_bytes(b"png-content")

    kwargs = _emodel_registration_kwargs(
        tmp_path,
        trace_ids=[uuid.uuid4(), uuid.uuid4()],
        figure_files=[figure_one, figure_two],
    )
    kwargs["hoc_file"].write_text("hoc-content")
    kwargs["emodel_summary_file"].write_text("{}")

    registered = register_emodel(client=client, **kwargs)

    assert registered.id is not None
