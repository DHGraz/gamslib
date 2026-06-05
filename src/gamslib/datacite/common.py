"""Shared helpers and reusable models for DataCite metadata.

This module contains Enums for allowed values and some helper functions
for validating and normalizing values. It also contains some reusable
models that are used across multiple metadata fields, such as
LocalizedTitle and Iso639ThreeLanguage.
"""

import re
from datetime import datetime
from enum import StrEnum

from pycountry import languages
from pydantic import BaseModel, field_validator


def lowercase_if_string(value):
    """Normalize string values to lowercase and leave other types unchanged."""
    if isinstance(value, str):
        return value.lower()
    return value


def normalize_iso_639_1(value):
    """Normalize and validate an ISO 639-1 language code.

    Raises a ValueError if the value is not a valid ISO 639-1 code.
    """
    value = lowercase_if_string(value)
    if isinstance(value, str) and languages.get(alpha_2=value) is None:
        raise ValueError(f"'{value}' is not a valid ISO 639-1 language code")
    return value


def normalize_iso_639_3(value):
    """Normalize and validate an ISO 639-3 language code.

    Raises a ValueError if the value is not a valid ISO 639-3 code.
    """
    value = lowercase_if_string(value)
    if isinstance(value, str) and languages.get(alpha_3=value) is None:
        raise ValueError(f"'{value}' is not a valid ISO 639-3 language code")
    return value


def require_exactly_one(values: dict[str, object], context: str) -> None:
    """Ensure exactly one of the provided optional values is set."""
    provided_names = [name for name, value in values.items() if value is not None]
    if len(provided_names) != 1:
        field_names = " or ".join(values)
        raise ValueError(
            f"Exactly one of {field_names} must be provided for {context}."
        )


def _validate_edtf_single_date(value: str) -> None:
    """Validate a single EDTF date token.

    Allowed formats:
    - YYYY-MM-DD
    - YYYY-MM
    - YYYY

    Raises a ValueError if the value does not match any of these formats.
    """
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return
    except ValueError:
        pass

    month_match = re.match(r"^\d{4}-(\d{2})$", value)
    if month_match and 1 <= int(month_match.group(1)) <= 12:
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
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError(
                "Date ranges must contain exactly two dates separated by '/'."
            )
        _validate_edtf_single_date(parts[0])
        _validate_edtf_single_date(parts[1])
        return value

    _validate_edtf_single_date(value)
    return value


# These are the allowed values for various fields,
# defined as type aliases for better readability.

# Add all accepted mimetypes
# TODO: extend this list with more mimetypes


class MetadataIdentifier(StrEnum):
    """Identifies a metadata identifier as type-subtype."""

    # TODO: Add other identifier types when we've decided on a final set.
    IMAGE_PHOTO = "image-photo"


class AlternateIdentifierSchema(StrEnum):
    """Identifies an alternate identifier as type-subtype."""

    # these are the values allowed for the alternateIdentifierType field
    # in the DataCite schema.
    ARK = "ark"
    ARXIV = "arxiv"
    ADS = "ads"
    CROSSREFFUNDERID = "crossreffunderid"
    DOI = "doi"
    EAN13 = "ean13"
    EISSN = "eissn"
    GRID = "grid"
    HANDLE = "handle"
    IGSN = "igsn"
    ISBN = "isbn"
    ISNI = "isni"
    ISSN = "issn"
    ISTC = "istc"
    LISSN = "lissn"
    LSID = "lsid"
    PMID = "pmid"
    PURL = "purl"
    UPC = "upc"
    URL = "url"
    URN = "urn"
    W3ID = "w3id"
    OTHER = "other"


class RelatedIdentifierSchema(StrEnum):
    """Identifies a related identifier."""

    # these are the values allowed for the relatedIdentifierType field
    # in the DataCite schema.
    ARK = "ark"
    ARXIV = "arxiv"
    BIBCODE = "bibcode"
    DOI = "doi"
    EAN13 = "ean13"
    EISSN = "eissn"
    HANDLE = "handle"
    IGSN = "igsn"
    ISBN = "isbn"
    ISSN = "issn"
    ISTC = "istc"
    LISSN = "lissn"
    LSID = "lsid"
    PUBMED = "pubmed"
    ID = "id"
    PURL = "purl"
    UPC = "upc"
    URL = "url"
    URN = "urn"
    W3ID = "w3id"


class RelationTypeVocabulary(StrEnum):
    """A catalog of defined relation types.

    See https://github.com/inveniosoftware/invenio-rdm-records/blob/master/invenio_rdm_records/fixtures/data/vocabularies/relation_types.yaml
    """

    ISCITEDBY = "iscitedby"
    CITES = "cites"
    ISSUPPLEMENTTO = "issupplementTo"
    ISSUPPLEMENTEDBY = "issupplementedBy"
    ISCONTINUEDBY = "iscontinuedBy"
    CONTINUES = "continues"
    ISDESCRIBEDBY = "isdescribedby"
    DESCIBES = "describes"
    HASMETADATA = "hasmetadata"
    ISMETADATAFOR = "ismetadatafor"
    HASVERSION = "hasversion"
    ISVERSIONOF = "isversionOf"
    ISNEWVERSIONOF = "isnewversionof"
    ISPREVIOUSVERSIONOF = "ispreviousversionof"
    ISPARTOF = "ispartOf"
    HASPART = "haspart"
    ISPUBLISHEDIN = "ispublishedIn"
    ISREFERENCEDBY = "isreferencedby"
    REFERENCES = "references"
    ISDOCUMENTEDBY = "isdocumentedby"
    DOCUMENTS = "documents"
    ISCOMPILEDBY = "iscompiledby"
    COMPILES = "compiles"
    ISVARIANTFORMOF = "isvariantformof"
    ISORIGINALFORMOF = "isoriginalformof"
    ISIDENTICALTO = "isidenticalto"
    ISREVIEWEDBY = "isreviewedby"
    REVIEWS = "reviews"
    ISDERIVEDFROM = "isderivedfrom"
    ISSOURCEOF = "issourceof"
    ISREQUIREDBY = "isrequiredby"
    REQUIRES = "requires"
    ISOBSOLETEDBY = "isobsoletedby"
    OBSOLETES = "obsoletes"
    ISCOLLECTEDBY = "iscollectedby"
    COLLECTS = "collects"
    ISTRANSLATIONOF = "istranslationof"
    HASTRANSLATION = "hastranslation"
    OTHER = "other"


# These classes are used in multiple places in the metadata,
# so we define them here to avoid duplication.
class LocalizedTitle(BaseModel):
    """Represents a localized title value serialized as {"en": "some title"}."""

    lang: str
    title: str

    @field_validator("lang", mode="before")
    @classmethod
    def validate_iso_639_1(cls, value):
        """Validate that the value is a valid ISO 639-1 language code."""
        return normalize_iso_639_1(value)


class Iso639ThreeLanguage(BaseModel):
    """Represents a normalized ISO 639-3 language code."""

    id: str

    @field_validator("id", mode="before")
    @classmethod
    def validate_iso_639_3(cls, value):
        """Validate that the value is a valid ISO 639-3 language code."""
        return normalize_iso_639_3(value)
