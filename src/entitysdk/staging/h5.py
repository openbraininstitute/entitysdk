"""Helpers for reading HDF5 datasets from an ``HttpFile``.

Requires the ``staging`` extra (``h5py``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import h5py
import numpy as np

if TYPE_CHECKING:
    from entitysdk.http_file import HttpFile


def read_contiguous_dataset(dataset: h5py.Dataset, remote: HttpFile) -> np.ndarray:
    """Read a whole dataset of a file opened on ``remote``, fetching its bytes outside h5py.

    A contiguous, uncompressed dataset is one run of bytes: its offset and size give one
    exact range request that does not hold h5py's lock. Chunked, compressed and
    variable-length-string datasets are read through h5py as usual.

    Returns:
        The dataset's values, as ``dataset[()]`` gives them.
    """
    offset = dataset.id.get_offset()
    if (
        offset is None
        or dataset.dtype.kind == "O"
        or dataset.id.get_storage_size() != dataset.nbytes
    ):
        return dataset[()]
    raw = remote.read_at(offset, dataset.nbytes)
    return np.frombuffer(raw, dtype=dataset.dtype).reshape(dataset.shape)
