"""pytest-httpx-compatible mocking API on top of pytest-httpx2 (respx)."""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qsl, urlparse

import respx


class HTTPXMock:
    """Minimal drop-in for the ``httpx_mock`` fixture provided by pytest-httpx."""

    def __init__(self, router: respx.Router) -> None:
        self._router = router

    def add_response(
        self,
        status_code: int = 200,
        *,
        json: Any = None,
        content: bytes | None = None,
        text: str | None = None,
        headers: dict[str, str] | None = None,
        **matchers: Any,
    ) -> None:
        route = self._route(**matchers)
        respond_kwargs: dict[str, Any] = {"status_code": status_code}
        if json is not None:
            respond_kwargs["json"] = json
        if content is not None:
            respond_kwargs["content"] = content
        if text is not None:
            respond_kwargs["text"] = text
        if headers is not None:
            respond_kwargs["headers"] = headers
        route.respond(**respond_kwargs)

    def add_exception(self, exception: BaseException, **matchers: Any) -> None:
        route = self._route(**matchers)
        route.mock(side_effect=exception)

    def _route(self, **matchers: Any) -> respx.models.Route:
        method = matchers.pop("method", None)
        url = matchers.pop("url", None)
        match_headers = matchers.pop("match_headers", None)
        match_json = matchers.pop("match_json", None)
        match_data = matchers.pop("match_data", None)
        match_files = matchers.pop("match_files", None)
        match_params = matchers.pop("match_params", None)
        # pytest-httpx options not used by this test suite
        matchers.pop("is_optional", None)
        matchers.pop("is_reusable", None)
        matchers.pop("match_content", None)
        matchers.pop("match_extensions", None)
        matchers.pop("proxy_url", None)

        route_kwargs: dict[str, Any] = {}
        if method is not None:
            route_kwargs["method"] = method
        if url is not None:
            parsed = urlparse(str(url))
            route_kwargs["url"] = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                match_params = match_params or dict(parse_qsl(parsed.query))
        if match_params is not None:
            route_kwargs["params"] = match_params
        if match_headers is not None:
            route_kwargs["headers"] = match_headers
        if match_json is not None:
            route_kwargs["json"] = match_json
        if match_data is not None:
            route_kwargs["data"] = match_data
        if match_files is not None:
            route_kwargs["files"] = match_files

        return self._router.route(**route_kwargs)
