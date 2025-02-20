"""Utility functions."""

import requests


def make_request(url: str, *, method, **kwargs) -> requests.Response:
    """Make a request to the given URL with the given method and data."""
    timeout = kwargs.pop("timeout", 10)
    response = requests.request(method, url, timeout=timeout, **kwargs)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        error_msg = (
            "\n"
            f"  Request failed:\n"
            f"  URL: {url}\n"
            f"  Method: {method}\n"
            f"  Status code: {response.status_code}\n"
            f"  Response body: {response.text}"
        )
        raise requests.exceptions.HTTPError(error_msg) from e

    return response
