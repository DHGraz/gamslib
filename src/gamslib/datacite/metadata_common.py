"""Shared helpers and reusable models for DataCite metadata."""

from datetime import datetime
from enum import StrEnum
import re
from typing import Literal

from pydantic import BaseModel, field_validator
from pycountry import languages


def _lowercase_if_string(value):
    """Normalize string values to lowercase and leave other types unchanged."""
    if isinstance(value, str):
        return value.lower()
    return value


def _normalize_iso_639_1(value):
    """Normalize and validate an ISO 639-1 language code."""
    value = _lowercase_if_string(value)
    if isinstance(value, str) and languages.get(alpha_2=value) is None:
        raise ValueError(f"'{value}' is not a valid ISO 639-1 language code")
    return value


def _normalize_iso_639_3(value):
    """Normalize and validate an ISO 639-3 language code."""
    value = _lowercase_if_string(value)
    if isinstance(value, str) and languages.get(alpha_3=value) is None:
        raise ValueError(f"'{value}' is not a valid ISO 639-3 language code")
    return value


def _require_exactly_one(values: dict[str, object], context: str) -> None:
    """Ensure exactly one of the provided optional values is set."""
    provided_names = [name for name, value in values.items() if value is not None]
    if len(provided_names) != 1:
        field_names = " or ".join(values)
        raise ValueError(f"Exactly one of {field_names} must be provided for {context}.")


MAX_MONTH = 12
RANGE_PART_COUNT = 2


def _validate_edtf_single_date(value: str) -> None:
    """Validate a single EDTF date token.

    Allowed formats:
    - YYYY-MM-DD
    - YYYY-MM
    - YYYY
    """
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return
    except ValueError:
        pass

    month_match = re.match(r"^\d{4}-(\d{2})$", value)
    if month_match and 1 <= int(month_match.group(1)) <= MAX_MONTH:
        return

    if re.match(r"^\d{4}$", value):
        return

    raise ValueError("Date must be in EDTF format (YYYY-MM-DD, YYYY-MM, or YYYY).")


def _validate_edtf(value: str) -> str:
    """Validate and normalize a string value using EDTF rules."""
    if not isinstance(value, str):
        raise TypeError("EDTF values must be strings.")

    if "/" in value:
        parts = value.split("/")
        if len(parts) != RANGE_PART_COUNT or not parts[0] or not parts[1]:
            raise ValueError("Date ranges must contain exactly two dates separated by '/'.")
        _validate_edtf_single_date(parts[0])
        _validate_edtf_single_date(parts[1])
        return value

    _validate_edtf_single_date(value)
    return value


IdentifierScheme = Literal["orcid", "gnd", "isni", "ror"]
PersonOrOrganizationType = Literal["personal", "organizational"]
AffiliationId = Literal["isni", "ror"]
CreatorRole = Literal["creator", "contributor"]
AdditionalTitleTypeId = Literal[
    "subtitle",
    "alternative-title",
    "translated-title",
    "other",
]
AdditionalDescriptionTypeId = Literal[
    "abstract",
    "methods",
    "series-information",
    "table-of-contents",
    "technical-info",
    "other",
]
ContributorRole = Literal[
    "editor",
    "funder",
    "project_leader",
    "project_manager",
    "other",
]
DateTypeId = Literal[
    "accepted",
    "available",
    "collected",
    "copyrighted",
    "created",
    "issued",
    "other",
    "submitted",
    "updated",
    "valid",
    "withdrawn",
]


class Identifier(StrEnum):
    """Identifies a metadata identifier as type-subtype."""

    IMAGE_PHOTO = "image-photo"


class LocalizedTitle(BaseModel):
    """Represents a localized title value serialized as {"en": "some title"}."""

    lang: str
    title: str

    @field_validator("lang", mode="before")
    @classmethod
    def validate_iso_639_1(cls, value):
        """Validate that the value is a valid ISO 639-1 language code."""
        return _normalize_iso_639_1(value)


class Iso639ThreeLanguage(BaseModel):
    """Represents a normalized ISO 639-3 language code."""

    id: str

    @field_validator("id", mode="before")
    @classmethod
    def validate_iso_639_3(cls, value):
        """Validate that the value is a valid ISO 639-3 language code."""
        return _normalize_iso_639_3(value)