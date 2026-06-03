"""Funding models for DataCite metadata.funding field."""

from pydantic import BaseModel, Field, field_validator

from gamslib.datacite.metadata_common import LocalizedTitle


class Funder(BaseModel):
    """A class representing a funding reference.

    Compatible with the DataCite schema for FundingReference.
    """

    # id should be a OFR (Open Funder Registry) identifier or ROR.
    # Currently I cannot figure out how to keep these in a vocabulary,
    # as this seems to change freqently.
    # May be can use the API? Or just ignore it.
    id: str | None = None
    name: str | None = None

    # either id or name must be provided, but not both
    @field_validator("id", "name")
    @classmethod
    def validate_id_or_name(cls, v, values):
        """Validate that either 'id' or 'name' is provided, but not both."""
        if v is None and values.get("id") is None:
            raise ValueError("Either 'id' or 'name' must be provided.")
        if v is not None and values.get("id") is not None:
            raise ValueError("Only one of 'id' or 'name' can be provided.")
        return v


class AwardIdentifier(BaseModel):
    """A class representing an award identifier.

    Compatible with the DataCite schema for FundingReference."""

    scheme: str
    identifier: str


class Award(BaseModel):
    """A class representing an award, compatible with the DataCite schema for FundingReference."""

    id: str | None = None  # Award identifier from a vocabulary # TODO
    title: LocalizedTitle | None = None
    funder: Funder | None = None
    number: str
    identifiers: list[AwardIdentifier] = Field(default_factory=list)


class FundingReference(BaseModel):
    """A class representing a funding reference.

    Compatible with the DataCite schema for FundingReference.
    """

    funder: Funder
    award: Award | None = None
