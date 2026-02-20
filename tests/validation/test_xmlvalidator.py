"""Tests for the XMLValidator class."""

import re
from pathlib import Path
import unittest

import pytest

from gamslib.validation.schemainfo import SchemaInfo, SchemaType
from gamslib.validation.xmlvalidator import XMLValidator


@pytest.fixture(name="make_schema_info")
def make_schema_info_fixture():
    "Provide a factory function for creating SchemaInfo objects."

    def _create(
        xsd_file: Path, schema_type: SchemaType, mimetype: str = "application/xml"
    ):
        return SchemaInfo(xsd_file.as_uri(), mimetype=mimetype, schema_type=schema_type)

    return _create


@pytest.mark.parametrize(
    "schema_file, schema_type",
    [
        ("simple.xsd", SchemaType.XSD),
        ("simple.rng", SchemaType.RNG),
        ("simple.rnc", SchemaType.RNC),
        ("simple.sch", SchemaType.SCH),
        ("simple.dtd", SchemaType.DTD),
    ],
)
def test_validate_valid(
    schema_file, schema_type, make_schema_info, lazy_shared_datadir
):
    """Test XMLValidator.validate() of a valid XML file against a single schema.

    All tests should succeed without setting any errors and warnings.
    """
    xml_file = lazy_shared_datadir / "simple.xml"
    schema_uri = lazy_shared_datadir / "schemas" / schema_file
    schemata = [
        make_schema_info(schema_uri, schema_type),
    ]
    result = XMLValidator().validate(xml_file, schemata)
    assert result.is_valid
    assert "Document validates against schema" in result.get_messages()[0]
    assert result.get_errors() == []
    assert result.get_warnings() == []

    subresult = next(result.get_subresults())
    assert subresult.is_valid
    assert subresult.validator_name in [
        "XML XSD Validator",
        "XML RelaxNG Validator",
        "XML RelaxNG Compact Validator",
        "XML Schematron Validator",
        "XML DTD Validator",
    ]
    assert subresult.schema_uri == schema_uri.as_uri()
    assert subresult.errors == []
    assert subresult.warnings == []


def test_validate_multiple_valid_schemas(make_schema_info, lazy_shared_datadir):
    """Run validate using multiple valid schemas."""
    xml_file = lazy_shared_datadir / "simple.xml"
    test_schemas = [
        ("simple.dtd", SchemaType.DTD, "XML DTD Validator"),
        ("simple.rnc", SchemaType.RNC, "XML RelaxNG Compact Validator"),
        ("simple.rng", SchemaType.RNG, "XML RelaxNG Validator"),
        ("simple.sch", SchemaType.SCH, "XML Schematron Validator"),
        ("simple.xsd", SchemaType.XSD, "XML XSD Validator"),
    ]
    schemata = []
    for schema_uri, schema_type, _ in test_schemas:
        schemata.append(
            make_schema_info(lazy_shared_datadir / "schemas" / schema_uri, schema_type)
        )

    result = XMLValidator().validate(xml_file, schemata)
    assert result.is_valid
    subresults = list(result.get_subresults())
    assert len(subresults) == len(schemata)

    assert all("Document validates against" in msg for msg in result.get_messages())
    assert subresults[0].validator_name == test_schemas[0][2]
    assert subresults[1].validator_name == test_schemas[1][2]
    assert subresults[2].validator_name == test_schemas[2][2]
    assert subresults[3].validator_name == test_schemas[3][2]
    assert subresults[4].validator_name == test_schemas[4][2]


@pytest.mark.parametrize(
    "schema_file, schema_type",
    [
        ("simple.xsd", SchemaType.XSD),
        ("simple.rng", SchemaType.RNG),
        ("simple.rnc", SchemaType.RNC),
        ("simple.sch", SchemaType.SCH),
        ("simple.dtd", SchemaType.DTD),
    ],
)
def test_validate_invalid(
    schema_file, schema_type, make_schema_info, lazy_shared_datadir
):
    """Test XMLValidator.validate() on an invalid XML file.

    All tests should succeed without setting any errors and warnings.
    """
    xml_file = lazy_shared_datadir / "simple_invalid.xml"
    schema_uri = lazy_shared_datadir / "schemas" / schema_file
    schemata = [
        make_schema_info(schema_uri, schema_type),
    ]
    result = XMLValidator().validate(xml_file, schemata)
    assert not result.is_valid
    assert "Document does not validate" in result.get_messages()[0]
    assert (
        re.search(r"element.*produkt", result.get_errors()[0], re.IGNORECASE)
        or "Only 'product' nodes are allowed" in result.get_errors()[0]
    )  # schematron is different, therefore the second condition
    assert result.get_warnings() == []


def test_parse_error_returns_syntax_error(lazy_shared_datadir, make_schema_info):
    """Test XMLValidator.validate() on a not well-formed XML file."""
    xml_file = lazy_shared_datadir / "minimal_not_wellformed.xml"
    xsd_file = lazy_shared_datadir / "schemas" / "simple.xsd"

    schemata = [make_schema_info(xsd_file, SchemaType.XSD)]
    result = XMLValidator().validate(xml_file, schemata)

    assert result.is_valid is False
    assert "syntax error" in result.get_messages()[0]
    assert all(err.startswith("Syntax error") for err in result.get_errors())


def test_validate_no_schema(lazy_shared_datadir):
    """Test XMLValidator.validate() If no schema is given(nor explicitely nore referenced in the XML)."""
    xml_file = lazy_shared_datadir / "minimal_wellformed.xml"
    result = XMLValidator().validate(xml_file, [])
    assert result.is_valid
    assert result.get_errors() == []
    assert any("has no schemas" in warning for warning in result.get_warnings())


def test_validate_usupported_schema_type(lazy_shared_datadir, make_schema_info):
    """Test XMLValidator.validate() on an unsupported schema type."""
    xml_file = lazy_shared_datadir / "minimal_wellformed.xml"
    schema_uri = lazy_shared_datadir / "schemas" / "simple.xsd"
    schemata = [make_schema_info(schema_uri, SchemaType.UNKNOWN)]
    result = XMLValidator().validate(xml_file, schemata)
    assert not result.is_valid
    assert "Unknown schema type" in result.get_messages()[0]
    assert all(err.startswith("Unknown schema format") for err in result.get_errors())


@pytest.mark.parametrize(
    "method_name",
    [
        "_validate_xsd",
        "_validate_schematron",
        "_validate_relaxng",
        "_validate_relaxng_compact",  
        "_validate_dtd",
    ],
)
def test_validate_with_generic_error(method_name, monkeypatch):
    """The various validate methods catch any errors as last resort Exception.

    Check if this is handled correctly and does not cause the whole validation 
    to fail without a result.
    """
    # mocking a generic error is a little bit tricky, since the error should be 
    # raised during validation, but we also need to provide a valid schema info 
    # to trigger the validation. Therefore, we mock the SchemaProvider to 
    # return a MockValidator that raises an error during validation.
    schema_info = unittest.mock.Mock()
    schema_info.schema_uri = "dummy_schema.xsd"

    class MockValidator:
        "A mock validator that raises an unexpected error during validation."

        def validate(self, *args, **kwargs):
            "always raise an unexpected error during validation."
            raise RuntimeError("Unexpected error during validation")

    class MockSchemaProvider:
        "A mock schema provider that returns a MockValidator for any schema URI."

        @staticmethod
        def get_xsd(schema_uri: str):  # pylint: disable=unused-argument
            "always return a MockValidator for any schema URI."
            return MockValidator()

    monkeypatch.setattr(
        "gamslib.validation.xmlvalidator.SchemaProvider", MockSchemaProvider
    )
    xml_file = Path("dummy.xml")
    xml_validator = XMLValidator()
    method_to_test = getattr(xml_validator, method_name)
    result = method_to_test(xml_file, schema_info)  # pylint: disable=protected-access
    assert not result.is_valid
    assert "Document does not validate against schema" in result.message
