"""Subject-related DataCite metadata models."""

from pydantic import BaseModel, model_validator

from gamslib.datacite.metadata_common import _require_exactly_one


class Subject(BaseModel):
    """Represents a subject for a record."""

    id: str | None = None
    subject: str | None = None

    @model_validator(mode="after")
    def validate_id_or_subject_field(self):
        """Validate that exactly one of id or subject is provided."""
        _require_exactly_one({"id": self.id, "subject": self.subject}, "a subject")
        return self
