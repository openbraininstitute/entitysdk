"""Scientific artifact publication link."""

from entitysdk.models.core import Identifiable
from entitysdk.models.publication import Publication
from entitysdk.models.scientific_artifact import ScientificArtifact
from entitysdk.types import PublicationType


class ScientificArtifactPublicationLink(Identifiable):
    """Scientific artifact - publication link."""

    publication: Publication
    scientific_artifact: ScientificArtifact
    publication_type: PublicationType
