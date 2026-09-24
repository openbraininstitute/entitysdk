"""Download functions for MEModel entities."""

import concurrent.futures
import logging
from pathlib import Path

from entitysdk.client import Client
from entitysdk.downloaders.cell_morphology import MORPHOLOGY_CONTENT_TYPES, download_morphology
from entitysdk.downloaders.emodel import download_hoc
from entitysdk.downloaders.ion_channel_model import download_ion_channel_mechanism
from entitysdk.exception import StagingError
from entitysdk.models.emodel import EModel
from entitysdk.models.memodel import MEModel
from entitysdk.schemas.memodel import DownloadedMEModel
from entitysdk.utils.filesystem import create_dir

logger = logging.getLogger(__name__)


def download_memodel(
    client: Client,
    memodel: MEModel,
    output_dir=".",
    max_concurrent: int = 1,
) -> DownloadedMEModel:
    """Download all assets needed to run an me-model: hoc, ion channel models, and morphology.

    Args:
        client (Client): EntitySDK client
        memodel (MEModel): MEModel entitysdk object
        output_dir (str): directory to save the downloaded files, defaults to current directory
        max_concurrent (int): maximum number of concurrent downloads. Defaults to 1 (sequential).
    """
    # we have to get the emodel to get the ion channel models.
    emodel = client.get_entity(entity_id=memodel.emodel.id, entity_type=EModel)

    output_dir = Path(output_dir)
    hoc_dir = output_dir / "hoc"
    morphology_dir = output_dir / "morphology"
    mechanisms_dir = create_dir(output_dir / "mechanisms")
    ion_channels = list(emodel.ion_channel_models or [])

    # Stage every morphology format the entity carries, so each downstream consumer (the viewer
    # wants swc, simulators may want asc/h5) finds its format.
    def _download_morphs() -> list[Path]:
        present = {asset.content_type for asset in memodel.morphology.assets}
        formats = [
            file_type
            for file_type, content_type in MORPHOLOGY_CONTENT_TYPES.items()
            if content_type in present
        ]
        if not formats:
            raise StagingError(f"No morphology file found for MEModel {memodel.id}")
        return [
            download_morphology(client, memodel.morphology, morphology_dir, file_type)
            for file_type in formats
        ]

    if max_concurrent == 1:
        hoc_path = download_hoc(client, emodel, hoc_dir)
        if not hoc_path.exists():
            raise StagingError(f"HOC file does not exist: {hoc_path}")
        morphology_paths = _download_morphs()
        mechanism_paths = [
            download_ion_channel_mechanism(client, ic, mechanisms_dir) for ic in ion_channels
        ]
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            hoc_future = executor.submit(download_hoc, client, emodel, hoc_dir)
            morphology_future = executor.submit(_download_morphs)
            mechanism_futures = [
                executor.submit(download_ion_channel_mechanism, client, ic, mechanisms_dir)
                for ic in ion_channels
            ]
            hoc_path = hoc_future.result()
            morphology_paths = morphology_future.result()
            mechanism_paths = [f.result() for f in mechanism_futures]
        if not hoc_path.exists():
            raise StagingError(f"HOC file does not exist: {hoc_path}")

    return DownloadedMEModel(
        hoc_path=hoc_path,
        mechanisms_dir=mechanisms_dir,
        mechanism_files=[p.name for p in mechanism_paths],
        morphology_paths=morphology_paths,
    )
