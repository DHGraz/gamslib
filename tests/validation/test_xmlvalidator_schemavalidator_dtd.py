"Tests for the xmlvalidator.DTDValidator class."

import pytest
from lxml import etree as ET

from gamslib.validation.xmlvalidator import DTDValidator


@pytest.fixture(name="dtd_validator")
def create_dtd_validator(lazy_shared_datadir):
    """Create a DTDValidator object."""
    schema_path = lazy_shared_datadir / "schemas" / "simple.dtd"
    assert schema_path.exists()
    schema_uri = schema_path.resolve().as_uri()
    validator = DTDValidator(schema_uri)
    return validator


@pytest.fixture(name="invalid_dtd_uri")
def create_invalid_dtd_uri(lazy_shared_datadir, tmp_path):
    """Create a invalid DTD and return its location as URI."""
    # Create an invalid DTD by taking a valid one and insert errors
    valid_dtd_path = lazy_shared_datadir / "schemas" / "simple.dtd"
    data = valid_dtd_path.read_text().replace("<!ELEMENT", "<<!ELEMENT")
    invalid_dtd_path = tmp_path / "invalid.dtd"
    invalid_dtd_path.write_text(data)
    return invalid_dtd_path.resolve().as_uri()


def test_dtd_validator_valid(dtd_validator, lazy_shared_datadir):
    """Test the XSD validator."""
    xml_path = lazy_shared_datadir / "simple.xml"
    try:
        tree = ET.parse(xml_path)  # pylint: disable=c-extension-no-member
    except ET.ParseError as err:
        pytest.fail(f"Could not parse {xml_path}: {err}")
    result = dtd_validator.validate(tree)
    assert result.is_valid
    assert (
        result.message == f"Document validates against DTD {dtd_validator.schema_uri}"
    )
    assert result.validator_name == "DTD Validator"
    assert not result.has_warnings


def test_dtd_validator_invalid_document(dtd_validator, lazy_shared_datadir):
    """Test the XSD validator with an invalid document."""
    xml_path = lazy_shared_datadir / "simple_invalid.xml"
    tree = ET.parse(xml_path)  # pylint: disable=c-extension-no-member
    result = dtd_validator.validate(tree)
    assert not result.is_valid
    assert result.validator_name == "DTD Validator"
    assert result.message.startswith("Document does not validate against DTD")
    assert not result.has_warnings
    assert len(result.errors) == 2


def test_dtd_validator_with_invalid_schema(lazy_shared_datadir, invalid_dtd_uri):
    """Test the DTD validator with an invalid schema."""

    # pylint: disable=protected-access

    # if creation of the validator fails, it should set the _creation_error
    # attribute and not raise an exception
    broken_validator = DTDValidator(invalid_dtd_uri)
    assert broken_validator._creation_error is not None

    # validating should always return the same error message, regardless of the input
    # document, because the validator could not be created successfully.
    xml_path = lazy_shared_datadir / "simple.xml"
    tree = ET.parse(xml_path)  # pylint: disable=c-extension-no-member
    result = broken_validator.validate(tree)
    assert not result.is_valid
    assert result.validator_name == "DTD Validator"
    assert len(result.errors) > 0
    assert result.message.startswith("Unable to create the validator")
