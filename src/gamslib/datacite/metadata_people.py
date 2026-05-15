"""People-related DataCite metadata models.

Module naming follows the owning model domain so support classes for creators and
contributors can be found quickly in one place.
"""

from pydantic import BaseModel, Field, field_validator, model_validator

from gamslib.datacite.metadata_common import (
    AffiliationId,
    ContributorRole,
    CreatorRole,
    IdentifierScheme,
    PersonOrOrganizationType,
    _lowercase_if_string,
    _require_exactly_one,
)


class PersonOrOrganizationIdentifier(BaseModel):
    """Represents a person or organization identifier."""

    scheme: IdentifierScheme
    identifier: str

    @field_validator("scheme", mode="before")
    @classmethod
    def normalize_scheme(cls, value):
        """Normalize identifier schemes to lowercase."""
        return _lowercase_if_string(value)


class PersonOrOrganization(BaseModel):
    """Represents a person or organization used in creator-like fields."""

    type: PersonOrOrganizationType
    given_name: str | None = None
    family_name: str | None = None
    name: str | None = None
    identifiers: PersonOrOrganizationIdentifier | None = None

    @model_validator(mode="after")
    def validate_name_fields(self):
        """Validate required/forbidden name fields based on the type value."""
        if self.type == "personal":
            if not self.given_name or not self.family_name:
                raise ValueError(
                    "For type='personal', both given_name and family_name are required."
                )
            if self.name is not None:
                raise ValueError("For type='personal', name must not be set.")
        elif self.type == "organizational":
            if not self.name:
                raise ValueError("For type='organizational', name is required.")
            if self.given_name is not None or self.family_name is not None:
                raise ValueError(
                    "For type='organizational', given_name and family_name must not be set."
                )
        return self


class Affiliation(BaseModel):
    """Represents an affiliation for a person or organization."""

    id: AffiliationId | None = None
    name: str | None = None

    @model_validator(mode="after")
    def validate_exactly_one_field(self):
        """Validate that exactly one of id or name is provided."""
        _require_exactly_one({"id": self.id, "name": self.name}, "an affiliation")
        return self


class Creator(BaseModel):
    """Represents a creator for a record."""

    person_or_org: PersonOrOrganization
    role: CreatorRole | None = None
    affiliations: list[Affiliation] = Field(default_factory=list)


class Contributor(Creator):
    """Represents a contributor for a record."""

    role: ContributorRole