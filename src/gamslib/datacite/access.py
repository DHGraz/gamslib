"""Classes for the datacite access information for a record.
This is used to specify the access level of a record, and
any embargo information if the record is embargoed.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator

# Allowed values for record and files access levels
_ALLOWED_ACCESS_VALUES = ("public", "restricted")


class Embargo(BaseModel):
    """Representation of an embargo for a record.

    This is part of the access information for a record, and is used to specify
    when a record will become open access.
    """

    active: bool
    # iso date string in the format YYYY-MM-DD
    until: str | None = None
    # explanation for the embargo
    reason: str | None = None


    @field_validator("until")
    @classmethod
    def validate_until(cls, value: str | None) -> str | None:
        "Validate the until field."
        if value is None:
            return value
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("until must be in YYYY-MM-DD format") from exc
        return value

class Access(BaseModel):
    "Representation of the access information for a record."

    record: Literal["public", "restricted"]
    files: Literal["public", "restricted"]
    embargo: Embargo | None = None
