"""Scientific artifact model."""

from datetime import datetime

from entitysdk.models.brain_region import BrainRegion
from entitysdk.models.entity import Entity
from entitysdk.models.license import License
from entitysdk.models.subject import Subject
from entitysdk.types import ID


class ScientificArtifact(Entity):
    """Scientific artifact base model."""

    experiment_date: datetime | None = None
    contact_id: ID | None = None
    atlas_id: ID | None = None

    subject: Subject
    brain_region: BrainRegion

    license: License | None = None
