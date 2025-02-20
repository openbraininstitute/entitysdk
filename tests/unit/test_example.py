"""Sample test file."""

import pytest

from entitysdk import example


def test_add_3_4():
    """Adding 3 and 4."""
    assert example.add(3, 4) == 7


def test_add_0_0():
    """Adding zero to zero."""
    assert example.add(0, 0) == 0


def test_add__raise():
    """Ensure it raises for x < 0."""

    with pytest.raises(ValueError, match="x must be positive"):
        example.add(-1, 0)
