"""Research log model."""

from entitysdk.models.entity import Entity


class ResearchLog(Entity):
    """Logbook of a research session, e.g. produced by an agent in a sandbox.

    The entities used and produced during the session are linked with derivations of type
    `research_log_input` and `research_log_output`, where the research log is the generated entity.
    """
