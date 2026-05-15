"""Rights-related DataCite metadata models."""

from pydantic import BaseModel, model_validator

from gamslib.datacite.metadata_common import LocalizedTitle, _require_exactly_one


RightsDescription = LocalizedTitle
RightsTitle = LocalizedTitle


class Rights(BaseModel):
    """Represents the rights information for a record."""

    id: str | None = None
    title: str | None = None
    description: LocalizedTitle | None = None
    link: str | None = None

    @model_validator(mode="after")
    def validate_id_or_title_field(self):
        """Validate that exactly one of id or title is provided."""
        _require_exactly_one({"id": self.id, "title": self.title}, "rights information")
        return self