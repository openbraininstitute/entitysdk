"""Scientific artifact model."""

from datetime import datetime

from pydantic import MISSING

from entitysdk.models.brain_region import BrainRegion
from entitysdk.models.entity import Entity
from entitysdk.models.license import License
from entitysdk.models.subject import Subject


class ScientificArtifact(Entity):
    """Scientific artifact base model."""

    experiment_date: datetime | None = MISSING  # type: ignore[assignment]
    contact_email: str | None = MISSING  # type: ignore[assignment]
    subject: Subject | None = MISSING  # type: ignore[assignment]
    brain_region: BrainRegion | None = MISSING  # type: ignore[assignment]
    license: License | None = MISSING  # type: ignore[assignment]
    published_in: str | None = MISSING  # type: ignore[assignment]
    notice_text: str | None = MISSING  # type: ignore[assignment]
