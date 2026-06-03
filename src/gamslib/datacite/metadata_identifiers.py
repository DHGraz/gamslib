"""Identifier models for DataCite metadata."""

from pydantic import BaseModel

from gamslib.datacite.metadata_common import (
    AlternateIdentifierSchema,
    RelatedIdentifierSchema,
)


class AlternateIdentifier(BaseModel):
    """Represents an alternate identifier for a record."""

    identifier: str
    scheme: AlternateIdentifierSchema


class RelatedIdentifier(BaseModel):
    """Represents a related identifier for a record."""

    identifier: str
    scheme: RelatedIdentifierSchema
    relation_type: str
    resource_type: str | None = None


__all__ = ["AlternateIdentifier", "RelatedIdentifier"]
