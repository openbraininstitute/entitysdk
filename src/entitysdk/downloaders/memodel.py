"""Download functions for MEModel entities."""

import itertools
import pathlib
from concurrent.futures import ThreadPoolExecutor

from entitysdk.downloaders.emodel import download_hoc
from entitysdk.downloaders.ion_channel_model import download_one_mechanism
from entitysdk.downloaders.morphology import download_morphology
from entitysdk.models.emodel import EModel


def download_memodel(client, access_token, memodel):
    """Download all assets needed to run an me-model: hoc, ion channel models, and morphology.

    Args:
        client (Client): EntitySDK client
        access_token (str): access token for authentication
        memodel (MEModel): MEModel entitysdk object
    """
    morphology = memodel.morphology
    # we have to get the emodel to get the ion channel models.
    emodel = client.get_entity(entity_id=memodel.emodel.id, entity_type=EModel, token=access_token)

    # + 2 for hoc and morphology
    # len of ion_channel_models should be around 10 for most cases,
    # and always < 100, even for genetic models
    max_workers = len(emodel.ion_channel_models) + 2
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        hoc_future = executor.submit(download_hoc, client, access_token, emodel, "./hoc")
        morph_future = executor.submit(
            download_morphology, client, access_token, morphology, "./morphology"
        )
        mechanisms_dir = pathlib.Path("./mechanisms")
        mechanisms_dir.mkdir(parents=True, exist_ok=True)
        executor.map(
            download_one_mechanism,
            itertools.repeat(client),
            itertools.repeat(access_token),
            emodel.ion_channel_models,
            itertools.repeat(mechanisms_dir),
        )

        hoc_path = hoc_future.result()
        morphology_path = morph_future.result()

    return hoc_path, mechanisms_dir, morphology_path
