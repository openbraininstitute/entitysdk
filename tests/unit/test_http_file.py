import io

import httpx2
import pytest

from entitysdk.http_file import HttpFile


class RangeServer:
    """httpx2 transport serving one blob with Range GETs, like S3 behind a GET-only
    presigned URL: HEAD is refused with 403."""

    def __init__(self, blob: bytes, *, ranges: bool = True):
        self.blob = blob
        self.ranges = ranges
        self.requests: list[str] = []

    def __call__(self, request: httpx2.Request) -> httpx2.Response:
        self.requests.append(f"{request.method} {request.headers.get('range', '')}".strip())
        if request.method == "HEAD":
            return httpx2.Response(403)
        if not self.ranges or "range" not in request.headers:
            return httpx2.Response(200, content=self.blob)
        start, end = request.headers["range"].removeprefix("bytes=").split("-")
        return httpx2.Response(206, content=self.blob[int(start) : int(end) + 1])


def _client(server: RangeServer) -> httpx2.Client:
    return httpx2.Client(transport=httpx2.MockTransport(server))


class TestHttpFile:
    def test_nothing_is_fetched_before_the_first_read(self):
        server = RangeServer(b"x" * 100)
        remote = HttpFile("http://s/f", _client(server), 100)
        assert remote.size == 100
        assert server.requests == []
        assert remote.readable()
        assert remote.seekable()

    def test_repr_omits_the_url(self):
        remote = HttpFile("https://s3/f.bin?X-Amz-Signature=secret", _client(RangeServer(b"x")), 1)
        assert "secret" not in repr(remote)
        assert "HttpFile" in repr(remote)

    def test_server_without_ranges_is_refused_on_the_first_read(self):
        server = RangeServer(b"x" * 10, ranges=False)
        remote = HttpFile("http://s/f", _client(server), 10, block_size=4)
        with pytest.raises(OSError, match="Expected 206"):
            remote.read(1)
        assert server.requests == ["GET bytes=0-3"]

    def test_an_error_status_is_an_oserror_without_the_signed_url(self):
        client = httpx2.Client(transport=httpx2.MockTransport(lambda _: httpx2.Response(403)))
        remote = HttpFile("https://s3/f.bin?X-Amz-Signature=secret", client, 10)
        with pytest.raises(OSError, match="got 403") as excinfo:
            remote.read(1)
        assert "secret" not in str(excinfo.value)
        assert "secret" not in repr(remote)
        assert excinfo.value.__cause__ is None

    def test_a_size_larger_than_the_file_is_an_error_not_short_bytes(self):
        remote = HttpFile("http://s/f", _client(RangeServer(b"x" * 10)), 12)
        with pytest.raises(OSError, match="wrong file size"):
            remote.read(12)

    def test_small_reads_share_one_block(self):
        blob = bytes(range(256)) * 4
        server = RangeServer(blob)
        remote = HttpFile("http://s/f", _client(server), len(blob), block_size=512)
        assert remote.read(4) == blob[:4]
        remote.seek(500)
        assert remote.read(4) == blob[500:504]
        assert server.requests == ["GET bytes=0-511"]
        remote.seek(600)
        assert remote.read(4) == blob[600:604]
        assert remote.requests == 2
        assert server.requests[-1] == "GET bytes=512-1023"

    def test_a_block_covers_a_read_that_crosses_its_boundary(self):
        blob = bytes(range(256)) * 4
        server = RangeServer(blob)
        remote = HttpFile("http://s/f", _client(server), len(blob), block_size=512)
        remote.seek(500)
        assert remote.read(100) == blob[500:600]
        assert server.requests == ["GET bytes=0-599"]

    def test_a_large_read_is_one_exact_request(self):
        blob = bytes(range(256)) * 16
        server = RangeServer(blob)
        remote = HttpFile("http://s/f", _client(server), len(blob), block_size=512)
        remote.seek(300)
        assert remote.read(2000) == blob[300:2300]
        assert server.requests == ["GET bytes=300-2299"]

    def test_reads_stop_at_the_end_of_the_file(self):
        blob = b"abcdef"
        remote = HttpFile("http://s/f", _client(RangeServer(blob)), len(blob), block_size=4)
        remote.seek(-2, io.SEEK_END)
        assert remote.read(10) == b"ef"
        assert remote.read(10) == b""
        assert remote.tell() == 6
        remote.seek(-3, io.SEEK_CUR)
        assert remote.read(1) == b"d"

    @pytest.mark.parametrize(
        ("offset", "whence", "match"),
        [(-1, io.SEEK_SET, "negative seek position"), (0, 3, "invalid whence")],
    )
    def test_invalid_seek_is_rejected(self, offset, whence, match):
        remote = HttpFile("http://s/f", _client(RangeServer(b"x")), 1)
        with pytest.raises(ValueError, match=match):
            remote.seek(offset, whence)

    def test_a_middle_slice_does_not_fetch_the_whole_file(self):
        blob = bytes(range(256)) * 64
        server = RangeServer(blob)
        remote = HttpFile("http://s/f", _client(server), len(blob), block_size=512)
        remote.seek(4000)
        assert remote.read(8) == blob[4000:4008]
        fetched = sum(len(block) for block in remote._blocks)
        assert fetched < len(blob)
        assert server.requests == ["GET bytes=3584-4095"]

    def test_a_large_read_is_not_kept_in_memory(self):
        blob = bytes(range(256)) * 16
        server = RangeServer(blob)
        remote = HttpFile("http://s/f", _client(server), len(blob), block_size=512)
        remote.seek(300)
        assert remote.read(2000) == blob[300:2300]
        assert remote._blocks == []
        remote.seek(300)
        assert remote.read(4) == blob[300:304]
        assert server.requests == ["GET bytes=300-2299", "GET bytes=0-511"]

    def test_close_frees_the_blocks_and_rejects_further_use(self):
        remote = HttpFile("http://s/f", _client(RangeServer(b"x" * 10)), 10, block_size=4)
        assert remote.read(1) == b"x"
        remote.close()
        assert remote.closed
        assert remote._blocks == []
        for operation in (lambda: remote.read(1), remote.tell, lambda: remote.seek(0)):
            with pytest.raises(ValueError, match="closed file"):
                operation()
        with pytest.raises(ValueError, match="closed file"):
            remote.read_at(0, 1)
        remote.close()

    def test_a_full_body_answer_is_refused_before_its_body_is_read(self):
        class Body(httpx2.SyncByteStream):
            read = False

            def __iter__(self):
                Body.read = True
                yield b"x" * 10

        transport = httpx2.MockTransport(lambda _: httpx2.Response(200, stream=Body()))
        remote = HttpFile("http://s/f", httpx2.Client(transport=transport), 10)
        with pytest.raises(OSError, match="got 200"):
            remote.read(1)
        assert not Body.read

    def test_read_at_is_one_exact_request_outside_the_cache(self):
        blob = bytes(range(256)) * 4
        server = RangeServer(blob)
        remote = HttpFile("http://s/f", _client(server), len(blob), block_size=512)
        assert remote.read(4) == blob[:4]
        assert remote.read_at(100, 8) == blob[100:108]
        assert server.requests == ["GET bytes=0-511", "GET bytes=100-107"]
        assert remote.tell() == 4
        with pytest.raises(ValueError, match="past the file size"):
            remote.read_at(1020, 8)
