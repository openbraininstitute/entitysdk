"""Activity model."""

from datetime import datetime

from entitysdk.models.core import Identifiable
from entitysdk.models.entity import Entity


class Activity(Identifiable):
    """Activity model."""

    start_time: datetime
    end_time: datetime | None = None

    used: list[Entity] | None = None
    generated: list[Entity] | None = None
