"""Reference models for DataCite metadata.reference field."""
from pydantic import BaseModel

from gamslib.datacite.metadata_common import IdentifierScheme


class GeneralReference(BaseModel):
    """General reference for related identifiers, funding, and references."""

    reference: str
    identifier: str | None = None
    scheme: IdentifierScheme|None = None
