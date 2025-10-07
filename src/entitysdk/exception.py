"""Exception classes."""

from json import dumps, loads
from json.decoder import JSONDecodeError


class EntitySDKError(Exception):
    """Base exception class for EntitySDK."""


class RouteNotFoundError(EntitySDKError):
    """Raised when a route is not found."""


class IteratorResultError(EntitySDKError):
    """Raised when the result of an iterator is not as expected."""


class DependencyError(EntitySDKError):
    """Raised when a dependency check fails."""


class StagingError(EntitySDKError):
    """Raised when a staging operation has failed."""


class ServerError(EntitySDKError):
    """Raises when a server request error is encountered."""

    def __init__(self, response):
        """Store response for server error."""
        try:
            response_payload = response.json()
        except JSONDecodeError:
            response_payload = response.content.decode()

        request = response.request
        try:
            request_payload = loads(request.content.decode())
        except JSONDecodeError:
            request_payload = request.content.decode()

        self.summary = {
            "Request": {
                "method": request.method,
                "url": str(request.url),
                "payload": request_payload,
            },
            "Response": {
                "status_code": response.status_code,
                "payload": response_payload,
            },
        }
        self.response = response

        super().__init__(dumps(self.summary, indent=2))
