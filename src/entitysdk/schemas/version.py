"""API version schema."""

from entitysdk.schemas.base import Schema


class APIVersion(Schema):
    """API version schema."""

    app_name: str
    app_version: str
    commit_sha: str
