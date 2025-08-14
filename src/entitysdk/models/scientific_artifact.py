"""Scientific artifact model."""

from datetime import datetime

from entitysdk.models.brain_region import BrainRegion
from entitysdk.models.entity import Entity
from entitysdk.models.license import License
from entitysdk.models.subject import Subject


class ScientificArtifact(Entity):
    """Scientific artifact base model."""

    experiment_date: datetime | None = None
    contact_email: str | None = None
    subject: Subject | None = None
    brain_region: BrainRegion | None = None
    license: License | None = None
    published_in: str | None = None
