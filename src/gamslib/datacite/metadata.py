"""Public DataCite metadata facade.

Implementation is split into `metadata_<topic>.py` modules so classes that only support a
specific part of the DataCite model stay easy to find by topic, while this module keeps the
public import surface stable.
"""

from pydantic import BaseModel, Field, field_validator

from gamslib.datacite.metadata_additional_descriptions import (
    AdditionalDescription,
    AdditionalDescriptionTitle,
    AdditionalDescriptionType,
    AddtionalDescriptionLang,
)
from gamslib.datacite.metadata_additional_titles import (
    AdditionalTitle,
    AdditionalTitleLang,
    AdditionalTitleType,
)
from gamslib.datacite.metadata_funding import FundingReference
from gamslib.datacite.metadata_identifiers import AlternateIdentifier, RelatedIdentifier
from gamslib.datacite.metadata_common import (
    Format,
    MetadataIdentifier,
    Iso639ThreeLanguage,
    LocalizedTitle,
    _validate_edtf,
)
from gamslib.datacite.metadata_dates import Date, DateTitle, DateType
from gamslib.datacite.metadata_location import Location
from gamslib.datacite.metadata_people import (
    Affiliation,
    Contributor,
    Creator,
    PersonOrOrganization,
    PersonOrOrganizationIdentifier,
)
from gamslib.datacite.metadata_reference import GeneralReference
from gamslib.datacite.metadata_rights import Rights, RightsDescription, RightsTitle
from gamslib.datacite.metadata_subjects import Subject


Language = Iso639ThreeLanguage


class Metadata(BaseModel):
    """Represents the metadata for a record."""

    id: MetadataIdentifier
    title: str
    publication_date: str
    creators: list[Creator]
    additional_titles: list[AdditionalTitle] = Field(default_factory=list)
    description: str | None = None
    additional_descriptions: list[AdditionalDescription] = Field(default_factory=list)
    rights: Rights | None = None
    copyright: str | None = None
    contributors: list[Contributor] = Field(default_factory=list)
    subjects: list[Subject] = Field(default_factory=list)
    languages: list[Language] = Field(default_factory=list)
    dates: list[Date] = Field(default_factory=list)
    version: str = ""
    publisher: str = "GAMS"
    identifiers: list[AlternateIdentifier] = Field(default_factory=list)
    related_identifiers: list[RelatedIdentifier] = Field(default_factory=list)
    sizes: list[str] = Field(default_factory=list)
    formats: list[Format] = Field(
        default_factory=list
    )  # MIME type TODO: validate the values?
    locations: list[Location] = Field(default_factory=list)
    funding: list[FundingReference] = Field(default_factory=list)
    references: list[GeneralReference] = Field(default_factory=list)

    @field_validator("publication_date")
    @classmethod
    def validate_publication_date(cls, value: str) -> str:
        """Validate publication_date using the shared EDTF rules."""
        return _validate_edtf(value)


__all__ = [
    "AdditionalDescription",
    "AdditionalDescriptionTitle",
    "AdditionalDescriptionType",
    "AdditionalTitle",
    "AdditionalTitleLang",
    "AdditionalTitleType",
    "AddtionalDescriptionLang",
    "Affiliation",
    "AlternateIdentifier",
    "Contributor",
    "Creator",
    "Date",
    "DateTitle",
    "DateType",
    "Language",
    "LocalizedTitle",
    "Metadata",
    "MetadataIdentifier",
    "PersonOrOrganization",
    "PersonOrOrganizationIdentifier",
    "RelatedIdentifier",
    "Rights",
    "RightsDescription",
    "RightsTitle",
    "Subject",
]
