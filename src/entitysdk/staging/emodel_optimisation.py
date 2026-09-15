"""Staging functions for emodel optimisation."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path
from typing import TypeVar
from uuid import UUID

from entitysdk.client import Client
from entitysdk.models.cell_morphology import CellMorphology
from entitysdk.models.derivation import Derivation
from entitysdk.models.entity import Entity
from entitysdk.models.types import RegisteredEntity
from entitysdk.types import ID, AssetLabel, ContentType

L = logging.getLogger(__name__)

TEntity = TypeVar("TEntity", bound=Entity)

EntityRef = RegisteredEntity | tuple[ID, type[Entity]]


def _resolve_entity(
    client: Client,
    entity_or_id: EntityRef,
) -> Entity:
    if isinstance(entity_or_id, tuple):
        entity_id, entity_type = entity_or_id
        return client.get_entity(entity_id=entity_id, entity_type=entity_type)
    return entity_or_id


def _entity_id(entity_or_id: EntityRef) -> UUID:
    if isinstance(entity_or_id, tuple):
        return entity_or_id[0]
    return entity_or_id.id


def stage_extraction_features(
    client: Client,
    *,
    extraction_task_result: EntityRef,
    emodel_name: str,
    output_dir: Path,
) -> Path:
    """Stage extracted e-features for an emodel optimisation run.

    Args:
        client: EntitySDK client.
        extraction_task_result: Extraction task result entity or ``(id, TaskResult)`` tuple.
        emodel_name: Name of the emodel used for the staged features filename.
        output_dir: Root output directory for the optimisation workspace.

    Returns:
        Path to the staged features JSON file.
    """
    features_dir = output_dir / "config" / "features"
    features_dir.mkdir(parents=True, exist_ok=True)
    target = features_dir / f"{emodel_name}.json"
    client.fetch_assets(
        entity_or_id=extraction_task_result,
        selection={"label": AssetLabel.efeature_extraction_features},
        output_path=target,
    ).one()
    L.info("Staged extracted features: %s", target)
    return target


def stage_morphology(
    client: Client,
    *,
    morphology: EntityRef,
    output_dir: Path,
    content_type: ContentType = ContentType.application_swc,
) -> str:
    """Stage a morphology file for an emodel optimisation run.

    Args:
        client: EntitySDK client.
        morphology: Cell morphology entity or ``(id, CellMorphology)`` tuple.
        output_dir: Root output directory for the optimisation workspace.
        content_type: Morphology asset content type to fetch.

    Returns:
        Staged morphology filename (not the full path).
    """
    morph_dir = output_dir / "morphologies"
    morph_dir.mkdir(parents=True, exist_ok=True)
    morphology_id = _entity_id(morphology)
    morph_filename = f"{morphology_id}.swc"
    client.fetch_assets(
        entity_or_id=morphology,
        selection={
            "label": AssetLabel.morphology,
            "content_type": content_type,
        },
        output_path=morph_dir / morph_filename,
    ).one()
    L.info("Staged morphology: %s", morph_filename)
    return morph_filename


def stage_mechanisms(
    client: Client,
    *,
    ion_channel_models: Sequence[EntityRef],
    output_dir: Path,
) -> Path:
    """Stage ion channel mechanism files for an emodel optimisation run.

    Args:
        client: EntitySDK client.
        ion_channel_models: Ion channel model entities or ``(id, IonChannelModel)`` tuples.
        output_dir: Root output directory for the optimisation workspace.

    Returns:
        Path to the staged mechanisms directory.
    """
    mech_dir = output_dir / "mechanisms"
    mech_dir.mkdir(parents=True, exist_ok=True)
    for ion_channel_model in ion_channel_models:
        client.fetch_assets(
            entity_or_id=ion_channel_model,
            selection={"content_type": ContentType.application_mod},
            output_path=mech_dir,
        ).one()
    L.info("Staged %d ion channel models.", len(ion_channel_models))
    return mech_dir


def stage_traces(
    client: Client,
    extraction_task_result: EntityRef,
) -> list[str]:
    """Resolve electrical cell recording trace IDs linked to an extraction task result.

    Args:
        client: EntitySDK client.
        extraction_task_result: Extraction task result entity or ``(id, TaskResult)`` tuple.

    Returns:
        Trace entity IDs as strings, discovered via derivation links.
    """
    extraction_task_result_id = _entity_id(extraction_task_result)
    derivations = client.search_entity(
        entity_type=Derivation,
        query={"generated__id": extraction_task_result_id},
    )
    trace_ids = [
        str(derivation.used.id)
        for derivation in derivations
        if derivation.used and derivation.used.id
    ]
    L.info("Found %d trace IDs via derivation chain.", len(trace_ids))
    return trace_ids


def derive_mtype(
    client: Client,
    morphology: EntityRef,
) -> str | None:
    """Derive the m-type pref label from a cell morphology entity.

    Args:
        client: EntitySDK client.
        morphology: Cell morphology entity or ``(id, CellMorphology)`` tuple.

    Returns:
        The first m-type pref label, if present.
    """
    morphology_entity = _resolve_entity(client, morphology)
    if not isinstance(morphology_entity, CellMorphology):
        msg = f"Expected CellMorphology, got {type(morphology_entity)}"
        raise TypeError(msg)
    if morphology_entity.mtypes:
        return str(morphology_entity.mtypes[0].pref_label)
    return None
