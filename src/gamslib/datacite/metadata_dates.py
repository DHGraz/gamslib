"""Date-related DataCite metadata models."""

from pydantic import BaseModel, field_validator

from gamslib.datacite.common import LocalizedTitle, _validate_edtf
from gamslib.datacite.vocabularies import DateTypeId


DateTitle = LocalizedTitle


class DateType(BaseModel):
    """Identifies the type of a date."""

    id: DateTypeId
    title: LocalizedTitle


class Date(BaseModel):
    """Represents a date for a record."""

    date: str
    type: DateType | None = None
    description: str | None = None

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        """Validate date values using the shared EDTF rules."""
        return _validate_edtf(value)
