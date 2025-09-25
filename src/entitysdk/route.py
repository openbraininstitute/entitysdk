"""Route handling."""

from entitysdk.exception import RouteNotFoundError
from entitysdk.models.core import Identifiable
from entitysdk.models.entity import Entity
from entitysdk.types import ID

# Mapping of entity type to api route name.
_ROUTES = {
    "Activity": "activity",
    "BrainLocation": "brain-location",
    "BrainRegion": "brain-region",
    "BrainRegionHierarchy": "brain-region-hierarchy",
    "CellMorphology": "cell-morphology",
    "Circuit": "circuit",
    "Consortium": "consortium",
    "Contribution": "contribution",
    "Derivation": "derivation",
    "ElectricalCellRecording": "electrical-cell-recording",
    "ElectricalRecordingStimulus": "electrical-recording-stimulus",
    "EMCellMesh": "em-cell-mesh",
    "EMDenseReconstructionDataset": "em-dense-reconstruction-dataset",
    "EModel": "emodel",
    "Entity": "entity",
    "ETypeClassification": "etype-classification",
    "ETypeClass": "etype",
    "Ion": "ion",
    "IonChannel": "ion-channel",
    "IonChannelModel": "ion-channel-model",
    "IonChannelRecording": "ion-channel-recording",
    "License": "license",
    "MEModel": "memodel",
    "MEModelCalibrationResult": "memodel-calibration-result",
    "MTypeClassification": "mtype-classification",
    "MTypeClass": "mtype",
    "Organization": "organization",
    "Person": "person",
    "Publication": "publication",
    "ScientificArtifactPublicationLink": "scientific-artifact-publication-link",
    "Simulation": "simulation",
    "SimulationCampaign": "simulation-campaign",
    "SingleNeuronSimulation": "single-neuron-simulation",
    "SingleNeuronSynaptome": "single-neuron-synaptome",
    "SingleNeuronSynaptomeSimulation": "single-neuron-synaptome-simulation",
    "SimulationExecution": "simulation-execution",
    "SimulationGeneration": "simulation-generation",
    "SimulationResult": "simulation-result",
    "Role": "role",
    "Species": "species",
    "Strain": "strain",
    "Subject": "subject",
    "Taxonomy": "taxonomy",
    "ValidationResult": "validation-result",
    # CellMorphologyProtocol type for retrieving
    "CellMorphologyProtocol": "cell-morphology-protocol",
    # CellMorphologyProtocol types for registering
    "DigitalReconstructionCellMorphologyProtocol": "cell-morphology-protocol",
    "ModifiedReconstructionCellMorphologyProtocol": "cell-morphology-protocol",
    "ComputationallySynthesizedCellMorphologyProtocol": "cell-morphology-protocol",
    "PlaceholderCellMorphologyProtocol": "cell-morphology-protocol",
}


def get_route_name(entity_type: type[Identifiable]) -> str:
    """Get the base route for an entity type."""
    class_name = entity_type.__name__

    try:
        return _ROUTES[class_name]
    except KeyError as e:
        raise RouteNotFoundError(
            f"Route for entity type {class_name} not found in routes. "
            f"Existing routes: {sorted(_ROUTES.keys())}"
        ) from e


def get_entities_endpoint(
    *,
    api_url: str,
    entity_type: type[Identifiable],
    entity_id: str | ID | None = None,
) -> str:
    """Get the API endpoint for an entity type."""
    route_name = get_route_name(entity_type)
    endpoint = route_name if entity_id is None else f"{route_name}/{entity_id}"
    return f"{api_url}/{endpoint}"


def get_entity_derivations_endpoint(
    *,
    api_url: str,
    entity_type: type[Entity],
    entity_id: ID,
):
    """Get endpoint for entity derivations."""
    route_name = get_route_name(entity_type)
    return f"{api_url}/{route_name}/{entity_id}/derived-from"


def get_assets_endpoint(
    *,
    api_url: str,
    entity_type: type[Identifiable],
    entity_id: str | ID,
    asset_id: str | ID | None = None,
) -> str:
    """Return the endpoint for the assets of an entity.

    Args:
        api_url: The base URL of the entitycore API.
        entity_type: The type of the entity.
        entity_id: The ID of the entity.
        asset_id: The ID of the asset.

    Returns:
        The endpoint for the assets of an entity.
    """
    base_url = get_entities_endpoint(api_url=api_url, entity_type=entity_type, entity_id=entity_id)
    asset_path = "assets" if asset_id is None else f"assets/{asset_id}"
    return f"{base_url}/{asset_path}"
