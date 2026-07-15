"""Module for registering emodels."""

import logging
from pathlib import Path

from entitysdk.models import (
    BrainRegion,
    CellMorphology,
    Derivation,
    EModel,
    Entity,
    ETypeClass,
    IonChannelModel,
    License,
    Species,
)
from entitysdk.registration.classification import (
    register_etype_classification,
)
from entitysdk.registration.validation_result import register_validation_result_figure
from entitysdk.types import (
    ID,
    AssetLabel,
    ContentType,
    DerivationType,
    EntityLifecycleStatus,
    EntityType,
)

L = logging.getLogger(__name__)


def register_emodel(
    *,
    client,
    name: str,
    description: str,
    authorized_public: bool,
    species: Species,
    brain_region: BrainRegion,
    license: License,  # noqa: A002
    seed: int,
    iteration: str,
    score: float,
    exemplar_morphology: CellMorphology,
    ion_channel_models: list[IonChannelModel],
    lifecycle_status: EntityLifecycleStatus,
    etype_class: ETypeClass,
    hoc_file: Path,
    emodel_summary_file: Path,
    electrical_cell_recording_ids: list[ID],
    validation_result_figure_files: list[Path],
    validateion_result_status: bool,
):
    """Register EModel."""
    emodel = client.register_entity(
        EModel(
            name=name,
            description=description,
            authorized_public=authorized_public,
            license=license,
            seed=seed,
            score=score,
            species=species,
            iteration=iteration,
            brain_region=brain_region,
            lifecycle_status=lifecycle_status,
            ion_channel_models=ion_channel_models,
            exemplar_morphology=exemplar_morphology,
        )
    )
    L.info("Registered EModel(id=%s, name=%s)", emodel.id, name)
    register_etype_classification(
        client=client,
        entity=emodel,
        etype_class=etype_class,
    )
    asset = client.upload_file(
        entity_id=emodel.id,
        entity_type=EModel,
        file_path=hoc_file,
        file_content_type=ContentType.application_hoc,
        asset_label=AssetLabel.neuron_hoc,
    )
    L.info("Registered EModel Asset(id=%s, label=%s, path=%s)", asset.id, asset.label, asset.path)
    asset = client.upload_file(
        entity_id=emodel.id,
        entity_type=EModel,
        file_path=emodel_summary_file,
        file_content_type=ContentType.application_json,
        asset_label=AssetLabel.emodel_optimization_output,
    )
    L.info("Registered EModel Asset(id=%s, label=%s, path=%s)", asset.id, asset.label, asset.path)
    for trace_id in electrical_cell_recording_ids:
        derivation = client.register_entity(
            Derivation(
                used=Entity(
                    id=trace_id,
                    type=EntityType.electrical_cell_recording,
                ),
                generated=emodel,
                derivation_type=DerivationType.unspecified,
            )
        )
        L.info("Registered EModel Derivation(id=%s, used=%s)", derivation.id, trace_id)

    for figure_file in validation_result_figure_files:
        register_validation_result_figure(
            client=client,
            authorized_public=emodel.authorized_public,
            figure_file=figure_file,
            validated_entity_id=emodel.id,
            passed=False,
        )
    return emodel
