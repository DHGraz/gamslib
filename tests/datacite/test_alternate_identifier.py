"""Tests for the AlternateIdentifier DataCite metadata model."""

import pytest
from pydantic import ValidationError

from gamslib.datacite.metadata_identifiers import AlternateIdentifier
from gamslib.datacite.vocabularies import AlternateIdentifierSchema


def test_alternate_identifier_accepts_enum_scheme():
    """AlternateIdentifier accepts an enum member as scheme."""
    identifier = AlternateIdentifier(
        identifier="10.1234/example",
        scheme=AlternateIdentifierSchema.DOI,
    )

    assert identifier.identifier == "10.1234/example"
    assert identifier.scheme is AlternateIdentifierSchema.DOI


def test_alternate_identifier_coerces_valid_string_scheme_to_enum():
    """AlternateIdentifier converts valid string schemes to enum members."""
    identifier = AlternateIdentifier(identifier="ark:/12345/abc", scheme="ark")

    assert identifier.scheme is AlternateIdentifierSchema.ARK
    assert identifier.model_dump(mode="json") == {
        "identifier": "ark:/12345/abc",
        "scheme": "ark",
    }


@pytest.mark.parametrize("value", ["DOI", "invalid", "", "123"])
def test_alternate_identifier_rejects_invalid_scheme_values(value):
    """AlternateIdentifier rejects scheme values outside the enum."""
    with pytest.raises(ValidationError, match="scheme"):
        AlternateIdentifier(identifier="10.1234/example", scheme=value)