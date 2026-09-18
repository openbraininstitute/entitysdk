"""Staging constants."""

from enum import auto

from entitysdk.compat import StrEnum

DEFAULT_NODE_POPULATION_NAME = "All"
DEFAULT_NODE_SET_NAME = "All"


class MorphologyFormat(StrEnum):
    """A morphology file extension that SONATA can declare in a circuit config."""

    swc = auto()
    asc = auto()
    h5 = auto()
