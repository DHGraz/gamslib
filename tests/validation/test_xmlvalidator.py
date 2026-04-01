"""Tests for the XMLValidator class."""

import re
from pathlib import Path
import unittest
from unittest.mock import MagicMock
from lxml import etree as ET

import pytest

from gamslib.validation.schemainfo import SchemaInfo, SchemaType
from gamslib.validation.xmlvalidator import (
    DTDValidator,
    RelaxNGCompactValidator,
    RelaxNGValidator,
    SchemaValidator,
    SchematronValidator,
    XMLSchemaValidator,
    XMLValidator,
)


@pytest.fixture(name="make_schema_info")
def make_schema_info_fixture():
    "Provide a factory function for creating SchemaInfo objects."

    def _create(
        xsd_file: Path, schema_type: SchemaType, mimetype: str = "application/xml"
    ):
        return SchemaInfo(xsd_file.as_uri(), mimetype=mimetype, schema_type=schema_type)

    return _create


@pytest.mark.parametrize(
    "schema_file, schema_type, validator_name",
    [
        ("simple.xsd", SchemaType.XSD, "XMLSchema Validator"),
        ("simple.rng", SchemaType.RNG, "RelaxNG Validator"),
        ("simple.rnc", SchemaType.RNC, "RelaxNGCompactValidator"),
        ("simple.sch", SchemaType.SCH, "Schematron Validator (lxml)"),
        ("simple.dtd", SchemaType.DTD, "DTD Validator"),
    ],
)
def test_validate_valid(
    schema_file, schema_type, validator_name, make_schema_info, lazy_shared_datadir
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
    assert "Document validates against " in result.get_messages()[0]
    assert result.get_errors() == []
    assert result.get_warnings() == []

    subresult = next(result.get_subresults())
    assert subresult.is_valid
    assert subresult.validator_name == validator_name
    assert subresult.schema_uri == schema_uri.as_uri()
    assert subresult.errors == []
    assert subresult.warnings == []


def test_validate_multiple_valid_schemas(make_schema_info, lazy_shared_datadir):
    """Run validate using multiple valid schemas."""
    xml_file = lazy_shared_datadir / "simple.xml"
    test_schemas = [
        ("simple.dtd", SchemaType.DTD, DTDValidator.VALIDATOR_NAME),
        ("simple.rnc", SchemaType.RNC, RelaxNGCompactValidator.VALIDATOR_NAME),
        ("simple.rng", SchemaType.RNG, RelaxNGValidator.VALIDATOR_NAME),
        ("simple.sch", SchemaType.SCH, SchematronValidator.LXML_VALIDATOR_NAME),
        ("simple.xsd", SchemaType.XSD, XMLSchemaValidator.VALIDATOR_NAME),
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


def test_validate_unsupported_schema_type(lazy_shared_datadir, make_schema_info):
    """Test XMLValidator.validate() on an unsupported schema type."""
    xml_file = lazy_shared_datadir / "minimal_wellformed.xml"
    schema_uri = lazy_shared_datadir / "schemas" / "simple.xsd"
    schemata = [make_schema_info(schema_uri, SchemaType.UNKNOWN)]
    result = XMLValidator().validate(xml_file, schemata)
    errors = result.get_errors()
    assert not result.is_valid
    assert "Unknown schema format" in result.get_messages()[0]
    assert all("Unknown schema type" in err for err in errors)


def test_srvl_to_message_lists_empty_report_returns_empty_lists():
    """srvl_to_message_lists should return empty lists if no assertions/reports exist."""
    report_root = ET.fromstring(
        """
        <svrl:schematron-output xmlns:svrl="http://purl.oclc.org/dsdl/svrl"/>
        """
    )

    errors, warnings = SchematronValidator.srvl_to_message_lists(report_root)

    assert errors == []
    assert warnings == []


def test_srvl_to_message_lists_extracts_errors_and_warnings():
    """srvl_to_message_lists should extract both failed-assert errors and successful-report warnings."""
    report_root = ET.fromstring(
        """
        <svrl:schematron-output xmlns:svrl="http://purl.oclc.org/dsdl/svrl">
          <svrl:failed-assert location="/catalog/product[1]" test="@id">
            <svrl:text>Missing required @id</svrl:text>
          </svrl:failed-assert>
          <svrl:successful-report location="/catalog/product[1]" test="@deprecated='true'">
            <svrl:text>Deprecated product entry</svrl:text>
          </svrl:successful-report>
        </svrl:schematron-output>
        """
    )

    errors, warnings = SchematronValidator.srvl_to_message_lists(report_root)

    assert errors == [
        "Error at /catalog/product[1] (@id): Missing required @id",
    ]
    assert warnings == [
        "Warning at /catalog/product[1] (@deprecated='true'): Deprecated product entry",
    ]


def test_srvl_to_message_lists_missing_attrs_use_empty_defaults():
    """srvl_to_message_lists should fall back to empty strings for missing location/test attributes."""
    report_root = ET.fromstring(
        """
        <svrl:schematron-output xmlns:svrl="http://purl.oclc.org/dsdl/svrl">
          <svrl:failed-assert>
            <svrl:text>Generic validation failure</svrl:text>
          </svrl:failed-assert>
        </svrl:schematron-output>
        """
    )

    errors, warnings = SchematronValidator.srvl_to_message_lists(report_root)

    assert errors == ["Error at  (): Generic validation failure"]
    assert not warnings


@pytest.mark.parametrize(
    "schema_uri,expected", [
        ("file://path/to/schema.xsd", False),
        ("http://example.com/schema.xsd", True),
        ("https://gams.uni-graz.at/schema.xsd", True),
        ("http://unallowed.example.org/schema.xsd", False)
    ]
)
def test_is_safe_uri_validates_safe_host(schema_uri, expected, monkeypatch, lazy_shared_datadir):
    """Before using the schema, we should check if the URI is safe to be loaded from the internet

    Only hosts configured as as safe (safe_xml_hosts) should be allowed. 
    All other URIs (including file:// URIs and local paths) should not be allowed.
    """
    # pylint: disable=protected-access

    configfile = lazy_shared_datadir / "cfg" / "project.toml"
    monkeypatch.setenv("GAMSCFG_PROJECT_TOML", str(configfile))
                        
    assert SchemaValidator._is_allowed_remote_schema_uri(schema_uri) is expected
