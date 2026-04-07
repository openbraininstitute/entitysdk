"""Download functions for MEModel entities."""

import concurrent.futures
from pathlib import Path
from typing import cast

from entitysdk.client import Client
from entitysdk.downloaders.cell_morphology import download_morphology
from entitysdk.downloaders.emodel import download_hoc
from entitysdk.downloaders.ion_channel_model import download_ion_channel_mechanism
from entitysdk.exception import IteratorResultError, StagingError
from entitysdk.models.emodel import EModel
from entitysdk.models.memodel import MEModel
from entitysdk.schemas.memodel import DownloadedMEModel
from entitysdk.utils.filesystem import create_dir


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
    emodel = cast(
        EModel,
        client.get_entity(entity_id=memodel.emodel.id, entity_type=EModel),  # type: ignore
    )

    output_dir = Path(output_dir)
    hoc_dir = output_dir / "hoc"
    morphology_dir = output_dir / "morphology"
    mechanisms_dir = create_dir(output_dir / "mechanisms")
    ion_channels = list(emodel.ion_channel_models or [])

    # only take .asc format for now.
    # Will take specific format when morphology_format is integrated into MEModel
    def _download_morph() -> Path:
        try:
            return download_morphology(client, memodel.morphology, morphology_dir, "asc")
        except IteratorResultError:
            return download_morphology(client, memodel.morphology, morphology_dir, "swc")

    if max_concurrent == 1:
        hoc_path = download_hoc(client, emodel, hoc_dir)
        if not hoc_path.exists():
            raise StagingError(f"HOC does not exist: {hoc_path}")
        morphology_path = _download_morph()
        mechanism_paths = [
            download_ion_channel_mechanism(client, ic, mechanisms_dir) for ic in ion_channels
        ]
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            hoc_future = executor.submit(download_hoc, client, emodel, hoc_dir)
            morphology_future = executor.submit(_download_morph)
            mechanism_futures = [
                executor.submit(download_ion_channel_mechanism, client, ic, mechanisms_dir)
                for ic in ion_channels
            ]
            hoc_path = hoc_future.result()
            morphology_path = morphology_future.result()
            mechanism_paths = [f.result() for f in mechanism_futures]
        if not hoc_path.exists():
            raise StagingError(f"HOC does not exist: {hoc_path}")

    return DownloadedMEModel(
        hoc_path=hoc_path,
        mechanisms_dir=mechanisms_dir,
        mechanism_files=[p.name for p in mechanism_paths],
        morphology_path=morphology_path,
    )
