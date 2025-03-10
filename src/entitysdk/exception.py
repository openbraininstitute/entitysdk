"""Exception classes."""


class EntitySDKError(Exception):
    """Base exception class for EntitySDK."""


class RouteNotFoundError(EntitySDKError):
    """Raised when a route is not found."""


class IteratorResultError(EntitySDKError):
    """Raised when the result of an iterator is not as expected."""
