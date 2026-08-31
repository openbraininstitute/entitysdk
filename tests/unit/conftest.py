import uuid
from collections.abc import Generator
from typing import Any, NamedTuple
from urllib.parse import parse_qsl, urlparse

import pytest
import respx
from respx.mocks import HTTPCoreMocker

from entitysdk.client import Client
from entitysdk.common import ProjectContext
from entitysdk.config import settings
from entitysdk.token_manager import TokenFromValue
from tests.unit.util import PROJECT_ID, VIRTUAL_LAB_ID


class HTTPCore2Mocker(HTTPCoreMocker):
    name = "httpcore2"
    targets = [
        "httpcore2._sync.connection.HTTPConnection",
        "httpcore2._sync.connection_pool.ConnectionPool",
        "httpcore2._sync.http_proxy.HTTPProxy",
        "httpcore2._async.connection.AsyncHTTPConnection",
        "httpcore2._async.connection_pool.AsyncConnectionPool",
        "httpcore2._async.http_proxy.AsyncHTTPProxy",
    ]


class HTTPXMock:
    """Register mocked httpx2 responses for the current test."""

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
        self._route(**matchers).mock(side_effect=exception)

    def _route(self, **matchers: Any) -> respx.models.Route:
        method = matchers.pop("method", None)
        url = matchers.pop("url", None)
        match_headers = matchers.pop("match_headers", None)
        match_json = matchers.pop("match_json", None)
        match_data = matchers.pop("match_data", None)
        match_files = matchers.pop("match_files", None)
        match_params = matchers.pop("match_params", None)
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


@pytest.fixture
def httpx_mock() -> Generator[HTTPXMock, None, None]:
    with respx.mock(using="httpcore2", assert_all_called=False) as router:
        yield HTTPXMock(router)


class Clients(NamedTuple):
    with_context: Client
    wout_context: Client


@pytest.fixture(autouse=True)
def _deserialize_model_extra_forbid(monkeypatch):
    # be more restrictive during tests to ensure that all the models are up to date
    monkeypatch.setattr(settings, "deserialize_model_extra", "forbid")


@pytest.fixture(scope="session")
def api_url():
    return "http://mock-host:8000"


@pytest.fixture(scope="session")
def project_context():
    return ProjectContext(
        project_id=PROJECT_ID,
        virtual_lab_id=VIRTUAL_LAB_ID,
    )


@pytest.fixture(scope="session")
def auth_token():
    return "mock-token"


@pytest.fixture(scope="session")
def token_from_value_manager(auth_token):
    return TokenFromValue(value=auth_token)


@pytest.fixture(scope="session")
def request_headers(project_context, auth_token):
    return {
        "project-id": str(project_context.project_id),
        "virtual-lab-id": str(project_context.virtual_lab_id),
        "Authorization": f"Bearer {auth_token}",
    }


@pytest.fixture(scope="session")
def request_headers_no_context(auth_token):
    return {
        "Authorization": f"Bearer {auth_token}",
    }


@pytest.fixture
def client(project_context, api_url, auth_token):
    return Client(api_url=api_url, project_context=project_context, token_manager=auth_token)


@pytest.fixture
def client_no_context(api_url, auth_token):
    return Client(api_url=api_url, token_manager=auth_token)


@pytest.fixture
def clients(client, client_no_context):
    return Clients(
        with_context=client,
        wout_context=client_no_context,
    )


@pytest.fixture
def random_uuid():
    return uuid.uuid4()
