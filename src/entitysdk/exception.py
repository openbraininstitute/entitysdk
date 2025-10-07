"""Exception classes."""

import base64
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
        request = response.request
        try:
            json_response_data = response.json()
        except JSONDecodeError:
            json_response_data = None
        try:
            text_response_data = response.text
        except (UnicodeDecodeError, LookupError):
            text_response_data = None
        try:
            json_request_data = loads(request.content.decode())
        except JSONDecodeError:
            json_request_data = request.content.decode()
        try:
            text_request_data = request.content.decode("utf-8")
        except UnicodeDecodeError:
            # Binary fallback: base64 encode to preserve data
            text_request_data = base64.b64encode(request.content).decode("ascii")

        self.summary = {
            "request": {
                "method": request.method,
                "url": str(request.url),
                "text": text_request_data,
                "json": json_request_data,
            },
            "response": {
                "status_code": response.status_code,
                "text": text_response_data,
                "json": json_response_data,
            },
        }
        self.response = response

        # for printing do not include empty entries
        message_summary = {
            transaction: {k: v for k, v in info.items() if v}
            for transaction, info in self.summary.items()
        }
        # and if there is a json, do not show text for less noise
        for transaction in ("request", "response"):
            if message_summary[transaction].get("text") and message_summary[transaction].get(
                "json"
            ):
                del message_summary[transaction]["text"]

        super().__init__(dumps(message_summary, indent=2))
