"""Iterator wrapper for iterable results."""

from collections.abc import Iterable, Iterator
from typing import Self, TypeVar

from entitysdk.exception import IteratorResultError

ResultType = TypeVar("ResultType")


class IteratorResult(Iterator[ResultType]):
    """A result of an iterator."""

    def __init__(self, iterable: Iterable[ResultType]) -> None:
        """Initialize the iterator result."""
        self._iterable = iter(iterable)

    def __iter__(self) -> Self:
        """Return the iterator."""
        return self

    def __next__(self) -> ResultType:
        """Return the next element of the iterable."""
        return next(self._iterable)

    def first(self) -> ResultType | None:
        """Return the first element of the iterable or None if empty."""
        return next(self, None)

    def one(self) -> ResultType:
        """Return exactly one item from the iterable or raise an error if not exactly one item."""
        if (first_item := self.first()) is None:
            raise IteratorResultError("Iterable is empty.")
        if next(self, None) is None:
            return first_item
        raise IteratorResultError("There are more than one items.")

    def one_or_none(self) -> ResultType | None:
        """Return exactly one item from the iterable or None if empty."""
        first_item = self.first()
        if next(self, None) is None:
            return first_item
        raise IteratorResultError("There are more than one items.")

    def all(self) -> list[ResultType]:
        """Return all items from the iterable."""
        return list(self._iterable)
