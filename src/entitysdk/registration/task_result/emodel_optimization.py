"""Module for registering emodel optimization TaskResult."""

import logging
from pathlib import Path

from entitysdk import Client, MultipartDirectoryUploadTransferConfig
from entitysdk.models import TaskResult
from entitysdk.types import AssetLabel, ContentType, TaskResultType

L = logging.getLogger(__name__)


def register_emodel_optimization_result(
    *,
    client: Client,
    name: str,
    description: str,
    authorized_public: bool,
    hdf5_checkpoint_file: Path,
    analysis_figures_dir: Path,
    summary_file: Path,
):
    """Register emodel_optimization__result."""
    task_result = client.register_entity(
        TaskResult(
            name=name,
            description=description,
            authorized_public=authorized_public,
            task_result_type=TaskResultType.emodel_optimisation__result,
        )
    )
    L.info("Registered optimiation TaskResult(id=%s)", task_result.id)
    asset = client.upload_file(
        entity_id=task_result.id,
        entity_type=TaskResult,
        file_path=hdf5_checkpoint_file,
        file_content_type=ContentType.application_x_hdf5,
        asset_label=AssetLabel.emodel_optimisation_checkpoint,
    )
    L.info("Registered TaskResult Asset(id=%s, path=%s)", asset.id, asset.path)
    asset = client.upload_directory(
        entity_id=task_result.id,
        entity_type=TaskResult,
        paths={
            str(p.relative_to(analysis_figures_dir)): p
            for p in analysis_figures_dir.iterdir()
            if p.is_file()
        },
        name=AssetLabel.emodel_analysis_figures,
        label=AssetLabel.emodel_analysis_figures,
        transfer_config=MultipartDirectoryUploadTransferConfig(),
    )
    L.info("Registered TaskResult Asset(id=%s, path=%s)", asset.id, asset.path)
    asset = client.upload_file(
        entity_id=task_result.id,
        entity_type=TaskResult,
        file_path=summary_file,
        file_content_type=ContentType.application_json,
        asset_label=AssetLabel.emodel_analysis_summary,
    )
    L.info("Registered TaskResult Asset(id=%s, path=%s)", asset.id, asset.path)
    return task_result
