"""Download functions for MEModel entities."""

import itertools
from concurrent.futures import ThreadPoolExecutor

from entitysdk.client import Client
from entitysdk.downloaders.emodel import download_hoc
from entitysdk.downloaders.ion_channel_model import download_ion_channel_mechanism
from entitysdk.downloaders.morphology import download_morphology
from entitysdk.models.emodel import EModel
from entitysdk.models.memodel import MEModel
from entitysdk.schemas.memodel import DownloadedMEModel
from entitysdk.utils.filesystem import create_dir


def download_memodel(client: Client, memodel: MEModel):
    """Download all assets needed to run an me-model: hoc, ion channel models, and morphology.

    Args:
        client (Client): EntitySDK client
        memodel (MEModel): MEModel entitysdk object
    """
    # we have to get the emodel to get the ion channel models.
    emodel = client.get_entity(entity_id=memodel.emodel.id, entity_type=EModel)

    hoc_path = download_hoc(client, emodel, "./hoc")
    morphology_path = download_morphology(client, memodel.morphology, "./morphology")
    mechanisms_dir = create_dir("./mechanisms")
    for ic in emodel.ion_channel_models:
        download_ion_channel_mechanism(client, ic, mechanisms_dir)

    return DownloadedMEModel(
        hoc_path=hoc_path, mechanisms_dir=mechanisms_dir, morphology_path=morphology_path
    )
