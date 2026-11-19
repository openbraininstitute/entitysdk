from pathlib import Path

import h5py
import numpy as np
import pytest

from entitysdk.staging.h5 import read_contiguous_dataset
from entitysdk.http_file import HttpFile
from tests.unit.test_http_file import RangeServer, _client


@pytest.fixture
def contiguous_h5(tmp_path: Path) -> Path:
    path = tmp_path / "data.h5"
    with h5py.File(path, "w") as h5:
        h5.create_dataset("x", data=np.arange(100, dtype="i8"))
        h5.create_dataset(
            "names",
            data=np.array([b"a", b"b"], dtype=object),
            dtype=h5py.string_dtype(),
        )
    return path


class TestReadContiguousDataset:
    def test_the_column_is_fetched_exactly_not_through_h5py(self, contiguous_h5: Path):
        blob = contiguous_h5.read_bytes()
        server = RangeServer(blob)
        remote = HttpFile("http://s/f", _client(server), len(blob), block_size=4096)
        with h5py.File(remote, "r") as h5:
            column = h5["x"]
            offset, nbytes = column.id.get_offset(), column.nbytes
            values = read_contiguous_dataset(column, remote)
        with h5py.File(contiguous_h5, "r") as h5:
            assert list(values) == list(h5["x"][()])
        assert server.requests[-1] == f"GET bytes={offset}-{offset + nbytes - 1}"

    def test_variable_length_strings_are_read_through_h5py(self, contiguous_h5: Path):
        blob = contiguous_h5.read_bytes()
        remote = HttpFile("http://s/f", _client(RangeServer(blob)), len(blob))
        with h5py.File(remote, "r") as h5:
            library = h5["names"]
            assert list(read_contiguous_dataset(library, remote)) == list(library[()])

    def test_a_chunked_dataset_is_read_through_h5py(self, tmp_path: Path):
        path = tmp_path / "chunked.h5"
        with h5py.File(path, "w") as h5:
            h5.create_dataset("x", data=np.arange(1000), chunks=(100,), compression="gzip")
        blob = path.read_bytes()
        remote = HttpFile("http://s/f", _client(RangeServer(blob)), len(blob))
        with h5py.File(remote, "r") as h5:
            assert list(read_contiguous_dataset(h5["x"], remote)) == list(range(1000))
