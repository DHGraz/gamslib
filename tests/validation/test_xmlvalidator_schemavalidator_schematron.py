"""Tests for the xmlvalidator.SchematronValidator."""

import lxml.isoschematron
import pytest
import saxonche  # pylint: disable=import-error
from lxml import etree as ET

from gamslib.validation.xmlvalidator import SchematronValidator

# pylint: disable=c-extension-no-member

@pytest.fixture(name="lxml_schematron_validator")
def create_lxml_schematron_validator(lazy_shared_datadir):
    """Create an lxml Schematron validator object."""
    schema_uri = (lazy_shared_datadir / "schemas" / "simple.sch").resolve().as_uri()
    validator = SchematronValidator(schema_uri)
    return validator


@pytest.fixture(name="saxon_schematron_validator")
def create_saxon_schematron_validator(lazy_shared_datadir):
    """Create a Saxon Schematron validator object."""
    schema_uri = (
        (lazy_shared_datadir / "schemas" / "simple_xslt3.sch").resolve().as_uri()
    )
    validator = SchematronValidator(schema_uri)
    return validator


@pytest.fixture(name="invalid_schematron_uri")
def create_invalid_schematron_uri(lazy_shared_datadir, tmp_path):
    """Create a invalid schematron file and return its location as URI."""
    # Create an invalid schema by taking a valid one and insert errors
    valid_schema_path = lazy_shared_datadir / "schemas" / "simple.sch"
    data = valid_schema_path.read_text().replace("<schema", "<<schema")
    invalid_schema_path = tmp_path / "invalid.sch"
    invalid_schema_path.write_text(data)
    return invalid_schema_path.resolve().as_uri()


def test_schematron_validator_init_lxml(lxml_schematron_validator):
    "Test if the validator used in the validator the lxml Schematron validator."
    assert isinstance(
        lxml_schematron_validator.schema_validator, lxml.isoschematron.Schematron
    )


def test_schematron_validator_init_saxon(saxon_schematron_validator):
    "Test if the validator used in the validator the saxon Schematron validator."
    assert isinstance(
        saxon_schematron_validator.schema_validator, saxonche.PyXsltExecutable
    )  # pylint: disable=c-extension-no-member


@pytest.mark.parametrize(
    "schematron_location, expected",
    [
        ("simple.sch", "xslt"),
        ("simple_exslt.sch", "exslt"),
        ("simple_stx.sch", "stx"),
        ("simple_xpath2.sch", "xpath2"),
        ("simple_xpath3.sch", "xpath3"),
        ("simple_xslt2.sch", "xslt2"),
        ("simple_xslt3.sch", "xslt3"),
        ("http://example.com/simple.sch", "xslt"),
        ("http://example.com/simple_xpath2.sch", "xpath2"),
        ("http://example.com/simple_xslt2.sch", "xslt2"),
        ("http://example.com/simple_xslt3.sch", "xslt3"),
    ],
)
def test_get_schematron_binding(schematron_location, expected, lazy_shared_datadir):
    """Test that the correct Schematron query binding is detected based on the schema URI."""
    if schematron_location.startswith("http://") or schematron_location.startswith(
        "file://"
    ):
        schema_uri = schematron_location
    else:
        schema_path = lazy_shared_datadir / "schemas" / schematron_location
        assert schema_path.exists()
        schema_uri = schema_path
    # get_binding is called in init. So all we have to do ist to create a Validator instance
    validator = SchematronValidator(schema_uri)
    assert validator.binding == expected


def test_schematron_validator_with_invalid_schema(
    lazy_shared_datadir, invalid_schematron_uri
):
    """Test the Schematron validator with an invalid schema."""

    # pylint: disable=protected-access

    # if creation of the validator fails, it should set the _creation_error
    # attribute and not raise an exception
    broken_validator = SchematronValidator(invalid_schematron_uri)
    assert broken_validator._creation_error is not None

    # validating should return the SubResult set when object initialiation failed
    # (and not try to validate the document)
    xml_path = lazy_shared_datadir / "simple.xml"
    tree = ET.parse(xml_path)  # pylint: disable=c-extension-no-member
    result = broken_validator.validate(tree)
    assert not result.is_valid
    assert result.validator_name == "XML Schematron Validator (lxml)"
    assert len(result.errors) >= 0
    assert result.message.startswith("Unable to create the validator")


def test_schematron_lxml_validator_valid_document(
    lxml_schematron_validator, lazy_shared_datadir
):
    """Test the Schematron validator."""
    xml_path = lazy_shared_datadir / "simple.xml"
    tree = ET.parse(xml_path)  # pylint: disable=c-extension-no-member
    result = lxml_schematron_validator.validate(tree)
    assert result.is_valid
    assert result.validator_name == "XML Schematron Validator (lxml)"
    assert (
        result.message
        == f"Document validates against schema {lxml_schematron_validator.schema_uri}"
    )
    assert not result.has_warnings


def test_schematron_lxml_validator_invalid_document(
    lxml_schematron_validator, lazy_shared_datadir
):
    """Test the saxon validator gainst a invalid document."""
    xml_path = lazy_shared_datadir / "simple_invalid.xml"
    tree = ET.parse(xml_path)  # pylint: disable=c-extension-no-member
    result = lxml_schematron_validator.validate(tree)
    assert not result.is_valid
    assert len(result.errors) == 1
    assert "Only 'product' nodes are allowed inside of 'products'" in result.errors[0]


def test_schematron_saxon_validator_valid_document(
    saxon_schematron_validator, lazy_shared_datadir
):
    """Test the Schematron validator."""
    xml_path = lazy_shared_datadir / "simple.xml"
    tree = ET.parse(xml_path)  # pylint: disable=c-extension-no-member
    result = saxon_schematron_validator.validate(tree)
    assert result.is_valid
    assert result.validator_name == "XML Schematron Validator (saxon)"
    assert (
        result.message
        == f"Document validates against schema {saxon_schematron_validator.schema_uri}"
    )
    assert not result.has_warnings


def test_schematron_saxon_validator_invalid_document(
    saxon_schematron_validator, lazy_shared_datadir
):
    """Test the Schematron validator with an invalid document."""
    xml_path = lazy_shared_datadir / "simple_invalid.xml"
    tree = ET.parse(xml_path)  # pylint: disable=c-extension-no-member
    result = saxon_schematron_validator.validate(tree)
    assert not result.is_valid
    assert result.validator_name == "XML Schematron Validator (saxon)"

    assert result.message.startswith("Document does not validate against schema")
    assert not result.has_warnings
    assert len(result.errors) > 0
    assert "Only 'product' nodes are allowed" in result.errors[0]


def test_schematron_validator_no_params_given(lxml_schematron_validator):
    """The schematron validato allows to use a tree or a file as input.
    If no parameters are given, it should raise an error and not crash.
    """
    with pytest.raises(
        ValueError, match=r"Either a tree or a file_path must be given."
    ):
        lxml_schematron_validator.validate()


def test_schematron_validator_both_params_given(
    lxml_schematron_validator, lazy_shared_datadir
):
    """The schematron validato allows to use a tree or a file as input.
    If both parameters are given, it should raise an error and not crash.
    """
    xml_path = lazy_shared_datadir / "simple.xml"
    tree = ET.parse(xml_path)  # pylint: disable=c-extension-no-member
    with pytest.raises(
        ValueError, match=r"Either a tree or a file_path must be given, but not both."
    ):
        lxml_schematron_validator.validate(tree=tree, file_path=xml_path)
