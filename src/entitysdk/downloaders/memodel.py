"""Download functions for MEModel entities."""

import itertools
import pathlib
from concurrent.futures import ThreadPoolExecutor

from entitysdk.client import Client
from entitysdk.downloaders.emodel import download_hoc
from entitysdk.downloaders.ion_channel_model import download_one_mechanism
from entitysdk.downloaders.morphology import download_morphology
from entitysdk.models.emodel import EModel
from entitysdk.models.memodel import MEModel
from entitysdk.schemas.memodel import DownloadedMEModel


def download_memodel(client: Client, memodel: MEModel):
    """Download all assets needed to run an me-model: hoc, ion channel models, and morphology.

    Args:
        client (Client): EntitySDK client
        memodel (MEModel): MEModel entitysdk object
    """
    morphology = memodel.morphology
    # we have to get the emodel to get the ion channel models.
    emodel = client.get_entity(entity_id=memodel.emodel.id, entity_type=EModel)

    # + 2 for hoc and morphology
    # len of ion_channel_models should be around 10 for most cases,
    # and always < 100, even for genetic models
    max_workers = len(emodel.ion_channel_models) + 2
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        hoc_future = executor.submit(download_hoc, client, emodel, "./hoc")
        morph_future = executor.submit(download_morphology, client, morphology, "./morphology")
        mechanisms_dir = pathlib.Path("./mechanisms")
        mechanisms_dir.mkdir(parents=True, exist_ok=True)
        executor.map(
            download_one_mechanism,
            itertools.repeat(client),
            emodel.ion_channel_models,
            itertools.repeat(mechanisms_dir),
        )

        hoc_path = hoc_future.result()
        morphology_path = morph_future.result()

    return DownloadedMEModel(
        hoc_path=hoc_path, mechanisms_dir=mechanisms_dir, morphology_path=morphology_path
    )
