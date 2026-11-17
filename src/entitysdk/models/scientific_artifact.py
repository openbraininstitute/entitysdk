"""Scientific artifact model."""

from datetime import datetime

from pydantic import MISSING

from entitysdk.models.brain_region import BrainRegion
from entitysdk.models.entity import Entity
from entitysdk.models.license import License
from entitysdk.models.subject import Subject


class ScientificArtifact(Entity):
    """Scientific artifact base model."""

    experiment_date: datetime | None | MISSING = MISSING
    contact_email: str | None | MISSING = MISSING
    subject: Subject | None | MISSING = MISSING
    brain_region: BrainRegion | None | MISSING = MISSING
    license: License | None | MISSING = MISSING
    published_in: str | None | MISSING = MISSING
    notice_text: str | None | MISSING = MISSING
