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
from gamslib.datacite.metadata_common import (
    Identifier,
    Iso639ThreeLanguage,
    LocalizedTitle,
    _validate_edtf,
)
from gamslib.datacite.metadata_dates import Date, DateTitle, DateType
from gamslib.datacite.metadata_people import (
    Affiliation,
    Contributor,
    Creator,
    PersonOrOrganization,
    PersonOrOrganizationIdentifier,
)
from gamslib.datacite.metadata_rights import Rights, RightsDescription, RightsTitle
from gamslib.datacite.metadata_subjects import Subject


Language = Iso639ThreeLanguage


class Metadata(BaseModel):
    """Represents the metadata for a record."""

    id: Identifier
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
    "Contributor",
    "Creator",
    "Date",
    "DateTitle",
    "DateType",
    "Identifier",
    "Language",
    "LocalizedTitle",
    "Metadata",
    "PersonOrOrganization",
    "PersonOrOrganizationIdentifier",
    "Rights",
    "RightsDescription",
    "RightsTitle",
    "Subject",
]


