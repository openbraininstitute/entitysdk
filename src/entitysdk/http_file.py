"""Read parts of a remote file with HTTP byte-range requests, not the whole file.

``HttpFile`` makes a URL look like a seekable file. Reads use ``Range`` and expect ``206``.
"""

import io
import logging
from collections import OrderedDict
from collections.abc import Callable, Iterator
from contextlib import contextmanager

from entitysdk.compat import Buffer, override
from entitysdk.utils.http import HTTPClient, HTTPResponse

L = logging.getLogger(__name__)

DEFAULT_BLOCK_SIZE = 1024 * 1024
DEFAULT_MAX_BLOCKS = 8
HTTP_PARTIAL_CONTENT = 206
HTTP_FORBIDDEN = 403


class HttpFile(io.RawIOBase):
    """A read-only, seekable file whose bytes are fetched from a URL on demand.

    The file is split into fixed, aligned blocks of ``block_size`` bytes. A read uses the
    blocks already cached and fetches the missing ones in one request. At most
    ``max_blocks`` blocks are kept; the least recently used are dropped first. A read
    spanning more than ``max_blocks`` blocks is fetched exactly and not cached, and
    ``read()`` of the whole remainder is a single request.

    A read raises ``OSError`` when the server does not answer 206 or returns the wrong
    number of bytes (a wrong ``size``). A presigned URL expires: when ``get_url`` is given,
    a 403 fetches a fresh URL and retries once; a failing ``get_url`` raises ``OSError``.
    The signed URL is never included in ``repr`` or error messages.

    Not thread-safe: the position and the cache are unguarded. Requests go through the
    given HTTP client, so the file stops working once that client is closed.

    Example:
        ::

            remote = HttpFile(url, http_client, size=742_603_632)
            with remote:
                remote.seek(0)
                header = remote.read(8)

    Attributes:
        size: File size in bytes, as given by the caller. Read-only.
        requests: Number of range requests sent so far. Read-only.
    """

    def __init__(
        self,
        url: str,
        http_client: HTTPClient,
        size: int,
        block_size: int = DEFAULT_BLOCK_SIZE,
        max_blocks: int = DEFAULT_MAX_BLOCKS,
        get_url: Callable[[], str] | None = None,
    ) -> None:
        """Store the URL and the size; nothing is fetched before the first read.

        Args:
            url: Address of a file served with byte-range support.
            http_client: Client used for every request (connection pool, timeouts).
            size: File size in bytes.
            block_size: Bytes per cached block.
            max_blocks: Maximum number of blocks kept in memory.
            get_url: Returns a fresh URL; called once when a request gets 403.
        """
        if block_size < 1 or max_blocks < 1:
            msg = f"block_size ({block_size}) and max_blocks ({max_blocks}) must be positive"
            raise ValueError(msg)
        super().__init__()
        self._url = url
        self._get_url = get_url
        self._http = http_client
        self._block_size = block_size
        self._max_blocks = max_blocks
        self._position = 0
        # Block index -> bytes, least recently used first.
        self._blocks: OrderedDict[int, bytes] = OrderedDict()
        self._requests = 0
        self._size = size

    def __repr__(self) -> str:
        """Omit the URL: it may carry presigned credentials."""
        # getattr: repr may run on an instance whose __init__ failed.
        return f"<HttpFile size={getattr(self, '_size', None)} closed={self.closed}>"

    @property
    def size(self) -> int:
        """File size in bytes, as given by the caller."""
        return self._size

    @property
    def requests(self) -> int:
        """Number of range requests sent so far."""
        return self._requests

    @override
    def readable(self) -> bool:
        """Return True; the file supports reads."""
        return True

    @override
    def seekable(self) -> bool:
        """Return True; the file supports seeks."""
        return True

    @override
    def close(self) -> None:
        """Drop cached blocks and mark the file closed."""
        # Assigned, not cleared: close() also runs from __del__ when __init__ failed.
        self._blocks = OrderedDict()
        super().close()

    def _check_open(self) -> None:
        """Raise ``ValueError`` after ``close()``, as ``io`` requires."""
        if self.closed:
            msg = "I/O operation on closed file"
            raise ValueError(msg)

    @override
    def tell(self) -> int:
        """Return the current byte position."""
        self._check_open()
        return self._position

    @override
    def seek(self, offset: int, whence: int = io.SEEK_SET, /) -> int:
        """Move the file position; no network request."""
        self._check_open()
        try:
            base = {io.SEEK_SET: 0, io.SEEK_CUR: self._position, io.SEEK_END: self.size}[whence]
        except KeyError as err:
            msg = f"invalid whence ({whence}, should be 0, 1 or 2)"
            raise ValueError(msg) from err
        position = base + offset
        if position < 0:
            msg = f"negative seek position {position}"
            raise ValueError(msg)
        self._position = position
        return self._position

    @override
    def readinto(self, buffer: Buffer, /) -> int:
        """Fill ``buffer`` from the current position; at most one request.

        Never a short read: callers that ignore the returned count would otherwise see
        uninitialised bytes past a partial fill.

        Returns:
            The number of bytes copied; 0 at the end of the file.
        """
        self._check_open()
        view = memoryview(buffer).cast("B")
        start = self._position
        length = min(len(view), self.size - start)
        if length <= 0:
            return 0
        end = start + length
        first, last = start // self._block_size, (end - 1) // self._block_size
        if last - first + 1 > self._max_blocks:
            self._fetch_into(start, view[:length])
        else:
            self._copy_from_blocks(start, end, first, last, view)
        self._position = end
        return length

    @override
    def readall(self) -> bytes:
        """Read from the position to the end of the file in one request, bypassing the cache."""
        self._check_open()
        start = self._position
        if start >= self.size:
            return b""
        content = self._fetch(start, self.size)
        self._position = self.size
        return content

    def read_at(self, start: int, length: int) -> bytes:
        """Fetch bytes ``[start, start + length)`` in one request, bypassing the cache.

        Does not change the file position.

        Raises:
            ValueError: Negative arguments, or the range ends past the end of the file.
        """
        self._check_open()
        if start < 0 or length < 0:
            msg = f"negative start ({start}) or length ({length})"
            raise ValueError(msg)
        if start + length > self.size:
            msg = f"range {start}-{start + length - 1} ends past the file size {self.size}"
            raise ValueError(msg)
        if length == 0:
            return b""
        return self._fetch(start, start + length)

    def _copy_from_blocks(
        self, start: int, end: int, first: int, last: int, view: memoryview
    ) -> None:
        """Copy ``[start, end)`` into ``view`` from blocks ``first..last``, fetching missing."""
        bs = self._block_size
        missing = [index for index in range(first, last + 1) if index not in self._blocks]
        if missing:
            # One request from the first to the last missing block; cached ones in between
            # are fetched again rather than splitting the read into several requests.
            span_start = missing[0] * bs
            data = self._fetch(span_start, min((missing[-1] + 1) * bs, self.size))
            for index in range(missing[0], missing[-1] + 1):
                offset = index * bs - span_start
                self._blocks[index] = data[offset : offset + bs]
        out = 0
        for index in range(first, last + 1):
            self._blocks.move_to_end(index)
            block_start = index * bs
            low = max(start, block_start) - block_start
            high = min(end, block_start + bs) - block_start
            view[out : out + high - low] = memoryview(self._blocks[index])[low:high]
            out += high - low
        while len(self._blocks) > self._max_blocks:
            self._blocks.popitem(last=False)

    @contextmanager
    def _range_response(self, start: int, end: int) -> Iterator[HTTPResponse]:
        """Stream a ``206`` response for ``[start, end)``; refresh the URL once on 403.

        Raises:
            OSError: Status other than 206, or ``get_url`` failed. The signed URL is left out.
        """
        headers = {"Range": f"bytes={start}-{end - 1}"}
        get_url = self._get_url
        while True:
            self._requests += 1
            # Streamed: a 200 (Range header dropped) is refused before its body is read.
            # No raise_for_status(): its message holds the signed URL.
            with self._http.stream(
                "GET", self._url, headers=headers, follow_redirects=True
            ) as response:
                status = response.status_code
                if status == HTTP_PARTIAL_CONTENT:
                    yield response
                    return
            # Refreshed after the 403 response is closed, so its connection is free for
            # the request get_url() makes, even with a one-connection pool.
            if status == HTTP_FORBIDDEN and get_url is not None:
                L.debug("Range read refused with 403, refreshing the URL")
                self._url = _refresh_url(get_url)
                get_url = None
                continue
            msg = f"Expected 206 for a range request, got {status}"
            raise OSError(msg)

    def _fetch(self, start: int, end: int) -> bytes:
        """Fetch bytes ``[start, end)`` in one request.

        Raises:
            OSError: Status other than 206, or wrong length.
        """
        with self._range_response(start, end) as response:
            content = response.read()
        _check_length(end - start, len(content))
        L.debug("Range read %s-%s (%d bytes)", start, end - 1, len(content))
        return content

    def _fetch_into(self, start: int, view: memoryview) -> None:
        """Fetch ``len(view)`` bytes from ``start`` straight into ``view``, without a copy.

        Raises:
            OSError: Status other than 206, or wrong length.
        """
        expected = len(view)
        received = 0
        with self._range_response(start, start + expected) as response:
            for chunk in response.iter_bytes():
                if received + len(chunk) > expected:
                    _check_length(expected, received + len(chunk))
                view[received : received + len(chunk)] = chunk
                received += len(chunk)
        _check_length(expected, received)
        L.debug("Range read %s-%s (%d bytes)", start, start + expected - 1, expected)


def _refresh_url(get_url: Callable[[], str]) -> str:
    """Call ``get_url``; raise ``OSError`` on failure, as file readers like h5py expect."""
    try:
        return get_url()
    except Exception as err:
        msg = f"Could not refresh the expired URL ({type(err).__name__})"
        raise OSError(msg) from err


def _check_length(expected: int, received: int) -> None:
    if received != expected:
        msg = f"Expected {expected} bytes, got {received}: wrong file size?"
        raise OSError(msg)
