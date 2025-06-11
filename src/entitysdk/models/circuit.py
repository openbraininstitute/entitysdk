"""Circuit model."""

from entitysdk.models.scientific_artifact import ScientificArtifact
from entitysdk.types import ID, CircuitBuildCategory, CircuitScale


class Circuit(ScientificArtifact):
    """Circuit model."""

    has_morphologies: bool = False
    has_point_neurons: bool = False
    has_electrical_cell_models: bool = False
    has_spines: bool = False

    number_neurons: int
    number_synapses: int
    number_connections: int | None

    scale: CircuitScale
    build_category: CircuitBuildCategory

    root_circuit_id: ID | None = None
    atlas_id: ID | None = None
