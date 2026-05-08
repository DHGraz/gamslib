"""Tests for the validation package (__init__.py)."""
from pathlib import Path
from unittest import mock

import pytest

from gamslib.validation import (
    jsonvalidator,
    pdfvalidator,
    validate,
    xmlvalidator,
)
from gamslib.validation.alwaysvalidvalidator import AlwaysValidValidator
from gamslib.validation.validator import ValidatorFactory


@pytest.mark.parametrize(
    "mimetype, expected_validator",
    [
        ("application/json", jsonvalidator.JSONValidator),
        ("application/pdf", pdfvalidator.PDFValidator),
        ("application/ld+json", jsonvalidator.JSONValidator),
        ("application/rdf+xml", xmlvalidator.XMLValidator),
        ("application/tei+xml", xmlvalidator.XMLValidator),
        ("application/xml", xmlvalidator.XMLValidator),
        ("text/xml", xmlvalidator.XMLValidator),
    ],
)
def test_get_validator(mimetype, expected_validator):
    """Make sure the correct validator class is returned.

    This only tests 'simple' cases. For more complex cases like XML we have
    separate tests.
    """
    formatinfo = mock.Mock()
    formatinfo.mimetype = mimetype
    validator = ValidatorFactory.get_validator(formatinfo)
    assert isinstance(validator, expected_validator)


def test_get_validator_with_missing_format_info():
    """Using None as format info should raise an error."""
    with pytest.raises(ValueError):
        ValidatorFactory.get_validator(None)


def test_make_validator_not_registered():
    "Requesting a validator for an unknown type should return the AlwaysValidValidator."
    formatinfo = mock.Mock()
    formatinfo.mimetype = "foo/bar"
    validator = ValidatorFactory.get_validator(formatinfo)
    assert isinstance(validator, AlwaysValidValidator)


def test_validate_wrong_path():
    "Test validation of a file that does not exist."
    with pytest.raises(FileNotFoundError):
        validate(Path("foo/bar.xml"))


def test_validate_wellformed_only(shared_datadir):
    "Validate a well-formed XML file withoud schema."
    file_to_validate = shared_datadir / "minimal_wellformed.xml"
    result = validate(file_to_validate)
    assert result.is_valid


def test_validate_xml_external_dtd(shared_datadir):
    "Test validation of an XML file with an external DTD."
    file_to_validate = shared_datadir / "simple_with_external_dtd.xml"
    result = validate(file_to_validate)
    assert result.is_valid


def test_validate_xml_xsd_in_root(shared_datadir):
    "Test validation of an XML referencing an XSD."
    file_to_validate = shared_datadir / "simple_with_external_dtd.xml"
    result = validate(file_to_validate)
    assert result.is_valid


def test_validate_xml_rng_and_sch(shared_datadir):
    "Test validation of an XML referencing an rng and schematron file."
    file_to_validate = shared_datadir / "simple_with_external_dtd.xml"
    result = validate(file_to_validate)
    assert result.is_valid


def test_validate_xml_rng_and_sch_in_pi(shared_datadir):
    "Test validation of an XML referencing in PI an rng and schematron file."
    file_to_validate = shared_datadir / "simple_with_external_dtd.xml"
    result = validate(file_to_validate)
    assert result.is_valid


def test_validate_for_warning_if_default_type(lazy_shared_datadir):
    "If the format cannot be detected, result should contain a warning."
    mock_formatinfo = mock.Mock()
    mock_formatinfo.mimetype = "foo/bar"

    result = validate(lazy_shared_datadir / "simple.xml", format_info=mock_formatinfo)
    assert result.is_valid
    assert result.get_warnings() == ["This file type has no validator registered."]


def test_validate_with_explicit_schema_location(lazy_shared_datadir):
    """Test validation of an XML file with an explicit schema location.

    The validate function expects an optional schema location.
    If this is given, it should be used for validation.
    """
    file_to_validate = lazy_shared_datadir / "simple.xml"
    schema_location = lazy_shared_datadir / "schemas" / "simple.xsd"
    result = validate(file_to_validate, schema_location=schema_location)
    assert result.is_valid
    assert len(list(result.get_subresults())) == 1
    subresult = next(iter(result.get_subresults()))
    assert subresult.schema_uri == schema_location.resolve().as_uri()
    assert subresult.validator_name == "XMLSchema Validator"


def test_validate_with_explicit_and_referenced_schema_location(lazy_shared_datadir):
    """Test validation of an XML file with an explicit and a referenced schema location.

    The validate function expects an optional schema location.
    If this is given, it should be used for validation.
    """
    file_to_validate = lazy_shared_datadir / "simple_with_external_dtd.xml"
    schema_location = lazy_shared_datadir / "schemas" / "simple.xsd"
    result = validate(file_to_validate, schema_location=schema_location)
    assert result.is_valid
    subresults = list(result.get_subresults())
    assert len(subresults) == 2
    assert any("DTD Validator" in subresult.validator_name for subresult in subresults)
    assert any("XMLSchema Validator" in subresult.validator_name for subresult in subresults)
