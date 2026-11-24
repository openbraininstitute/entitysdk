import gc
import io
import sys

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
        assert server.requests == ["GET bytes=0-1023"]
        remote.seek(510)
        assert remote.read(10) == blob[510:520]
        assert remote.requests == 1

    def test_a_read_spanning_several_blocks_is_one_aligned_request(self):
        blob = bytes(range(256)) * 16
        server = RangeServer(blob)
        remote = HttpFile("http://s/f", _client(server), len(blob), block_size=512)
        remote.seek(300)
        assert remote.read(2000) == blob[300:2300]
        assert server.requests == ["GET bytes=0-2559"]
        assert sorted(remote._blocks) == [0, 1, 2, 3, 4]

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
        fetched = sum(len(block) for block in remote._blocks.values())
        assert fetched < len(blob)
        assert server.requests == ["GET bytes=3584-4095"]

    def test_a_read_larger_than_the_cache_is_exact_and_not_kept(self):
        blob = bytes(range(256)) * 16
        server = RangeServer(blob)
        remote = HttpFile("http://s/f", _client(server), len(blob), block_size=512, max_blocks=2)
        remote.seek(300)
        assert remote.read(2000) == blob[300:2300]
        assert not remote._blocks
        remote.seek(300)
        assert remote.read(4) == blob[300:304]
        assert server.requests == ["GET bytes=300-2299", "GET bytes=0-511"]

    def test_close_frees_the_blocks_and_rejects_further_use(self):
        remote = HttpFile("http://s/f", _client(RangeServer(b"x" * 10)), 10, block_size=4)
        assert remote.read(1) == b"x"
        remote.close()
        assert remote.closed
        assert not remote._blocks
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


MiB = 1024 * 1024


class CountingRangeServer:
    """Serve one blob with Range GETs; record ranges and bytes sent.

    After ``expire_after`` requests, URLs without ``fresh`` get 403, like an expired
    presigned URL.
    """

    def __init__(self, blob: bytes, *, expire_after: int | None = None):
        self.blob = blob
        self.ranges: list[tuple[int, int]] = []
        self.bytes_sent = 0
        self.expire_after = expire_after

    def __call__(self, request: httpx2.Request) -> httpx2.Response:
        expired = self.expire_after is not None and len(self.ranges) >= self.expire_after
        if expired and "fresh" not in str(request.url):
            return httpx2.Response(403)
        start, end = map(int, request.headers["range"].removeprefix("bytes=").split("-"))
        self.ranges.append((start, end))
        body = self.blob[start : end + 1]
        self.bytes_sent += len(body)
        return httpx2.Response(206, content=body)


def _counting(blob: bytes, block_size: int = 4 * MiB, **kwargs):
    server = CountingRangeServer(blob, expire_after=kwargs.pop("expire_after", None))
    remote = HttpFile("http://s/f", _client(server), len(blob), block_size=block_size, **kwargs)
    return server, remote


def _cached_bytes(remote: HttpFile) -> int:
    return sum(len(block) for block in remote._blocks.values())


class TestHttpFileBlocks:
    """Fixed blocks with a bounded LRU cache: each byte is downloaded about once."""

    def test_sequential_3mib_reads_download_each_byte_once(self):
        blob = bytes(64 * MiB)
        server, remote = _counting(blob)
        while remote.read(3 * MiB):
            pass
        assert server.bytes_sent == len(blob)
        assert _cached_bytes(remote) <= 8 * 4 * MiB

    def test_read_crossing_a_cached_block_fetches_only_the_missing_block(self):
        server, remote = _counting(bytes(16 * MiB))
        remote.read(1)
        remote.seek(3 * MiB)
        remote.read(2 * MiB)
        assert server.ranges == [(0, 4 * MiB - 1), (4 * MiB, 8 * MiB - 1)]

    def test_cache_is_bounded_during_sequential_small_reads(self):
        blob = bytes(64 * MiB)
        server, remote = _counting(blob)
        while remote.read(64 * 1024):
            pass
        assert server.bytes_sent == len(blob)
        assert _cached_bytes(remote) == 8 * 4 * MiB

    def test_least_recently_used_block_is_dropped_first(self):
        blob = bytes(range(256)) * 4
        server, remote = _counting(blob, block_size=256, max_blocks=2)
        for position in (0, 256, 0, 512):
            remote.seek(position)
            remote.read(1)
        assert sorted(remote._blocks) == [0, 2]
        assert len(server.ranges) == 3

    def test_plain_read_is_one_request_and_not_cached(self):
        blob = bytes(range(256)) * 4096
        server, remote = _counting(blob, block_size=4096)
        remote.seek(10)
        assert remote.read() == blob[10:]
        assert server.ranges == [(10, len(blob) - 1)]
        assert not remote._blocks
        assert remote.read() == b""

    def test_buffered_reader_with_10mb_chunks_downloads_each_byte_about_once(self):
        blob = bytes(64 * MiB)
        server, remote = _counting(blob)
        reader = io.BufferedReader(remote)
        while reader.read(10_000_000):
            pass
        assert server.bytes_sent == len(blob)

    def test_large_read_is_streamed_and_checked_for_length(self):
        server = CountingRangeServer(bytes(100))
        remote = HttpFile("http://s/f", _client(server), 110, block_size=10, max_blocks=1)
        with pytest.raises(OSError, match="wrong file size"):
            remote.read(110)

    def test_large_read_that_returns_too_many_bytes_is_refused(self):
        transport = httpx2.MockTransport(lambda _: httpx2.Response(206, content=b"x" * 50))
        remote = HttpFile("http://s/f", httpx2.Client(transport=transport), 40, 10, 1)
        with pytest.raises(OSError, match="Expected 40 bytes, got 50"):
            remote.read(40)

    @pytest.mark.parametrize(("block_size", "max_blocks"), [(0, 1), (1, 0)])
    def test_invalid_cache_settings_are_rejected(self, block_size, max_blocks):
        with pytest.raises(ValueError, match="must be positive"):
            HttpFile("http://s/f", _client(RangeServer(b"x")), 1, block_size, max_blocks)

    def test_failed_construction_does_not_raise_on_garbage_collection(self):
        unraisable = []
        hook, sys.unraisablehook = sys.unraisablehook, unraisable.append
        try:
            with pytest.raises(ValueError, match="must be positive"):
                HttpFile("http://s/f", _client(RangeServer(b"x")), 1, block_size=0)
            gc.collect()
        finally:
            sys.unraisablehook = hook
        assert unraisable == []


class _Body(httpx2.SyncByteStream):
    def __iter__(self):
        yield b"x"


class TestHttpFileUrlRefresh:
    def test_expired_url_is_refreshed_once(self):
        calls = []

        def get_url():
            calls.append(1)
            return "http://s/f?fresh"

        server, remote = _counting(bytes(16 * MiB), expire_after=1, get_url=get_url)
        remote.read(1)
        remote.seek(8 * MiB)
        assert remote.read(1) == b"\0"
        remote.seek(12 * MiB)
        assert remote.read(1) == b"\0"
        assert calls == [1]
        assert remote.requests == 4

    def test_a_second_403_is_an_error(self):
        _, remote = _counting(bytes(100), expire_after=0, get_url=lambda: "http://s/still-old")
        with pytest.raises(OSError, match="got 403"):
            remote.read(1)
        assert remote.requests == 2

    def test_url_is_refreshed_after_the_403_response_is_closed(self):
        responses = []

        def handler(request):
            # A streamed body: with content=, the response would be closed from the start.
            response = httpx2.Response(403 if not responses else 206, stream=_Body())
            responses.append(response)
            return response

        def get_url():
            assert responses[0].is_closed
            return "http://s/f?fresh"

        client = httpx2.Client(transport=httpx2.MockTransport(handler))
        remote = HttpFile("http://s/f", client, 1, get_url=get_url)
        assert remote.read(1) == b"x"

    def test_a_failing_get_url_is_an_oserror(self):
        def get_url():
            raise RuntimeError("entitycore is down")

        _, remote = _counting(bytes(100), expire_after=0, get_url=get_url)
        with pytest.raises(OSError, match="Could not refresh") as excinfo:
            remote.read(1)
        assert isinstance(excinfo.value.__cause__, RuntimeError)

    def test_without_get_url_a_403_is_an_error(self):
        _, remote = _counting(bytes(100), expire_after=0)
        with pytest.raises(OSError, match="got 403"):
            remote.read(1)
        assert remote.requests == 1


class TestHttpFileAttributes:
    @pytest.mark.parametrize("name", ["size", "requests"])
    def test_size_and_requests_are_read_only(self, name):
        _, remote = _counting(bytes(100))
        with pytest.raises(AttributeError):
            setattr(remote, name, 1)


class TestReadAtArguments:
    @pytest.mark.parametrize(("start", "length"), [(-1, 4), (0, -1)])
    def test_negative_arguments_are_rejected_without_a_request(self, start, length):
        server, remote = _counting(bytes(100), block_size=16)
        with pytest.raises(ValueError, match="negative"):
            remote.read_at(start, length)
        assert server.ranges == []

    def test_zero_length_is_empty_without_a_request(self):
        server, remote = _counting(bytes(100), block_size=16)
        assert remote.read_at(50, 0) == b""
        assert server.ranges == []
