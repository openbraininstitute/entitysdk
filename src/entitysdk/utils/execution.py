"""Execution module."""

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")  # Generic return type


def execute_with_retry(
    fn: Callable[[], T],
    *,
    max_retries: int = 3,
    backoff_base: float = 0.5,
    retry_on: tuple[type[BaseException], ...] = (Exception,),
) -> T:
    """Execute a callable with retries and exponential backoff.

    Args:
        fn: Callable with no arguments returning any type T.
        max_retries: Maximum number of attempts (>=0).
        backoff_base: Base delay in seconds for exponential backoff.
        retry_on: Types of exceptions to retry.

    Returns:
        The result of `fn()` if successful.

    Raises:
        The last exception if all retries fail.
    """
    if not (max_retries >= 0):
        raise ValueError("max_retries must be >= 0")
    last_exception: BaseException | None = None

    for attempt in range(1, max_retries + 1):
        try:
            return fn()
        except retry_on as exc:
            last_exception = exc
            delay = backoff_base * (2 ** (attempt - 1))
            time.sleep(delay)

    assert last_exception is not None
    raise last_exception
