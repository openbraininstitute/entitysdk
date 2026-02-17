from pathlib import Path

from entitysdk.utils import io as test_module


def create_tmp_file(tmp_dir: Path, size: int):
    """Create a temporary file with dummy content."""
    path = tmp_dir / f"file_{size}.bin"
    # Fill the file with a repeating byte pattern (0-255)
    content = bytes([i % 256 for i in range(size)])
    path.write_bytes(content)
    return path, content


def test_iter_bytes_chunk__size_equals_buffer(tmp_path):
    size = 12
    file_path, file_content = create_tmp_file(tmp_path, size)
    chunks = list(
        test_module.iter_bytes_chunk(path=file_path, offset=0, size=size, buffer_size=size)
    )
    assert len(chunks) == 1
    assert len(chunks[0]) == size

    assert b"".join(chunks) == file_content
    assert sum(len(c) for c in chunks) == size


def test_iter_bytes_chunk__buffer_larger_than_size(tmp_path):
    size = 12
    file_path, file_content = create_tmp_file(tmp_path, size)
    chunks = list(
        test_module.iter_bytes_chunk(path=file_path, offset=0, size=size, buffer_size=1000)
    )
    assert len(chunks) == 1
    assert len(chunks[0]) == size

    assert b"".join(chunks) == file_content
    assert sum(len(c) for c in chunks) == size


def test_iter_bytes_chunk__buffer_multiple_of_size(tmp_path):
    size = 50
    file_path, file_content = create_tmp_file(tmp_path, size)

    chunks = list(test_module.iter_bytes_chunk(file_path, offset=10, size=20, buffer_size=5))

    assert len(chunks) == 4
    assert [len(c) for c in chunks] == [5, 5, 5, 5]

    content = b"".join(chunks)
    assert content == file_content[10:30]


def test_iter_bytes_chunk__inexact_buffer(tmp_path):
    size = 50
    file_path, file_content = create_tmp_file(tmp_path, size)

    chunks = list(test_module.iter_bytes_chunk(file_path, offset=10, size=20, buffer_size=6))

    assert len(chunks) == 4
    assert [len(c) for c in chunks] == [6, 6, 6, 2]

    content = b"".join(chunks)
    assert content == file_content[10:30]


def test_iter_bytes_chunk__offset_at_eof(tmp_path):
    size = 10
    file_path, file_content = create_tmp_file(tmp_path, size)

    chunks = list(test_module.iter_bytes_chunk(file_path, offset=10, size=20, buffer_size=6))
    assert chunks == []


def test_iter_bytes_chunk_offset__offset_plus_size_exceeds_eof(tmp_path):
    size = 10
    file_path, file_content = create_tmp_file(tmp_path, size)

    chunks = list(test_module.iter_bytes_chunk(file_path, offset=7, size=5, buffer_size=4))
    content = b"".join(chunks)

    assert content == file_content[7:10]
