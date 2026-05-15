"""Top-level DataCite record models.

The module name follows the owning model so the record-level classes are easy to find,
while `datacite.py` remains a compatibility facade.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from gamslib.datacite.access import Access
from gamslib.datacite.metadata import Metadata


class DataCite(BaseModel):
    """Representation of a top-level DataCite/Invenio record."""

    record_schema: str = Field(
        default="local://records/record-v2.0.0.json",
        alias="$schema",
        serialization_alias="$schema",
    )
    id: str | None = None
    pid: dict[str, Any] | None = None
    pids: dict[str, Any] = Field(default_factory=dict)
    parent: dict[str, Any] | None = None
    access: Access
    metadata: Metadata
    custom_fields: dict[str, Any] = Field(default_factory=dict)
    files: dict[str, Any] = Field(default_factory=dict)
    tombstone: dict[str, Any] | None = None
    created: datetime | None = None
    updated: datetime | None = None


__all__ = ["DataCite"]
