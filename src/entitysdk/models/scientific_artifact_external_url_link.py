"""Scientific artifact external url link."""

from entitysdk.models.core import Identifiable
from entitysdk.models.external_url import ExternalUrl
from entitysdk.models.scientific_artifact import ScientificArtifact


class ScientificArtifactExternalUrlLink(Identifiable):
    """Scientific artifact - external url link."""

    external_url: ExternalUrl
    scientific_artifact: ScientificArtifact
