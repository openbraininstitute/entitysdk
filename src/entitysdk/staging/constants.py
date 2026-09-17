"""Staging constants."""

from entitysdk.compat import StrEnum

DEFAULT_NODE_POPULATION_NAME = "All"
DEFAULT_NODE_SET_NAME = "All"


class MorphologyFormat(StrEnum):
    """A morphology file extension that SONATA can declare in a circuit config."""

    swc = "swc"
    asc = "asc"
    h5 = "h5"
