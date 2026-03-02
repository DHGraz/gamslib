"""Test the various schema validators defined in xmlvalidator.py.

Each SchemaValidator object provides a validate() method, which always 
returns a ValidationSubResult.
"""

import lxml.isoschematron
import pytest
import saxonche
from lxml import etree as ET

from gamslib.validation.xmlvalidator import (
    DTDValidator,
    RelaxNGCompactValidator,
    RelaxNGValidator,
    SchematronValidator,
    XMLSchemaValidator,
)

# --- fixtures ---


@pytest.fixture(name="dtd_validator")
def create_dtd_validator(lazy_shared_datadir):
    """Create a DTDValidator object."""
    schema_path = lazy_shared_datadir / "schemas" / "simple.dtd"
    assert schema_path.exists()
    schema_uri = schema_path.resolve().as_uri()
    validator = DTDValidator(schema_uri)
    return validator


@pytest.fixture(name="xmlschema_validator")
def create_xmlschema_validator(lazy_shared_datadir):
    """Create an XMLSchemaValidator object."""
    schema_uri = (lazy_shared_datadir / "schemas" / "simple.xsd").resolve().as_uri()
    validator = XMLSchemaValidator(schema_uri)
    return validator


@pytest.fixture(name="rng_validator")
def create_rng_validator(lazy_shared_datadir):
    """Create a RNGValidator object."""
    schema_path = lazy_shared_datadir / "schemas" / "simple.rng"
    assert schema_path.exists()
    schema_uri = schema_path.resolve().as_uri()
    validator = RelaxNGValidator(schema_uri)
    return validator


@pytest.fixture(name="rnc_validator")
def create_rnc_validator(lazy_shared_datadir):
    """Create a RNCValidator object."""
    schema_path = lazy_shared_datadir / "schemas" / "simple.rnc"
    assert schema_path.exists()
    schema_uri = schema_path.resolve().as_uri()
    validator = RelaxNGCompactValidator(schema_uri)
    return validator


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


@pytest.fixture(name="invalid_dtd_uri")
def create_invalid_dtd_uri(lazy_shared_datadir, tmp_path):
    """Create a invalid DTD and return its location as URI."""
    # Create an invalid DTD by taking a valid one and insert errors
    valid_dtd_path = lazy_shared_datadir / "schemas" / "simple.dtd"
    data = valid_dtd_path.read_text().replace("<!ELEMENT", "<<!ELEMENT")
    invalid_dtd_path = tmp_path / "invalid.dtd"
    invalid_dtd_path.write_text(data)
    return invalid_dtd_path.resolve().as_uri()


@pytest.fixture(name="invalid_schematron_uri")
def create_invalid_schematron_uri(lazy_shared_datadir, tmp_path):
    """Create a invalid schematron file and return its location as URI."""
    # Create an invalid schema by taking a valid one and insert errors
    valid_schema_path = lazy_shared_datadir / "schemas" / "simple.sch"
    data = valid_schema_path.read_text().replace("<schema", "<<schema")
    invalid_schema_path = tmp_path / "invalid.sch"
    invalid_schema_path.write_text(data)
    return invalid_schema_path.resolve().as_uri()


@pytest.fixture(name="invalid_rng_uri")
def create_invalid_rng_uri(lazy_shared_datadir, tmp_path):
    """Create a invalid RelaxNG file and return its location as URI."""
    # Create an invalid schema by taking a valid one and insert errors
    valid_schema_path = lazy_shared_datadir / "schemas" / "simple.rng"
    data = valid_schema_path.read_text().replace("<element", "<<element")
    invalid_schema_path = tmp_path / "invalid.rng"
    invalid_schema_path.write_text(data)
    return invalid_schema_path.resolve().as_uri()


@pytest.fixture(name="invalid_rnc_uri")
def create_invalid_rnc_uri(lazy_shared_datadir, tmp_path):
    """Create a invalid RelaxNG file and return its location as URI."""
    # Create an invalid schema by taking a valid one and insert errors
    valid_schema_path = lazy_shared_datadir / "schemas" / "simple.rnc"
    data = valid_schema_path.read_text().replace("start", "Xstart")
    invalid_schema_path = tmp_path / "invalid.rnc"
    invalid_schema_path.write_text(data)
    return invalid_schema_path.resolve().as_uri()


# ---- XSD ----


def test_xsd_validator_valid(xmlschema_validator, lazy_shared_datadir):
    """Test the XSD validator."""
    xml_path = lazy_shared_datadir / "simple.xml"
    tree = ET.parse(xml_path)  # pylint: disable=c-extension-no-member
    result = xmlschema_validator.validate(tree)
    assert result.is_valid
    assert (
        result.message
        == f"Document validates against schema {xmlschema_validator.schema_uri}"
    )
    assert result.validator_name == XMLSchemaValidator.VALIDATOR_NAME
    assert not result.has_warnings


def test_xsd_validator_invalid_document(xmlschema_validator, lazy_shared_datadir):
    """Test the XSD validator with an invalid document."""
    xml_path = lazy_shared_datadir / "simple_invalid.xml"
    tree = ET.parse(xml_path)  # pylint: disable=c-extension-no-member
    result = xmlschema_validator.validate(tree)
    assert not result.is_valid
    assert result.validator_name == XMLSchemaValidator.VALIDATOR_NAME
    assert result.message.startswith("Document does not validate against schema")
    assert not result.has_warnings
    assert len(result.errors) == 1


def test_xsd_validator_with_invalid_schema(lazy_shared_datadir, invalid_schematron_uri):
    """Test the XSD validator with an invalid schema."""
    # if creation of the validator fails, it should set the _creation_error
    # attribute and not raise an exception
    broken_validator = XMLSchemaValidator(invalid_schematron_uri)
    assert (
        broken_validator._creation_error
        is not None  ## pylint: disable=protected-access
    )

    # validating should always return the same error message, regardless of the input
    # document, because the validator could not be created successfully.
    xml_path = lazy_shared_datadir / "simple.xml"
    tree = ET.parse(xml_path)  # pylint: disable=c-extension-no-member
    result = broken_validator.validate(tree)
    assert not result.is_valid
    assert result.validator_name == XMLSchemaValidator.VALIDATOR_NAME
    assert len(result.errors) > 0
    assert result.message.startswith("Unable to create the validator")


# --- external DTD ---


def test_dtd_validator_valid(dtd_validator, lazy_shared_datadir):
    """Test the XSD validator."""
    xml_path = lazy_shared_datadir / "simple.xml"
    tree = ET.parse(xml_path)  # pylint: disable=c-extension-no-member
    result = dtd_validator.validate(tree)
    assert result.is_valid
    assert (
        result.message == f"Document validates against DTD {dtd_validator.schema_uri}"
    )
    assert result.validator_name == DTDValidator.VALIDATOR_NAME
    assert not result.has_warnings


def test_dtd_validator_invalid_document(dtd_validator, lazy_shared_datadir):
    """Test the XSD validator with an invalid document."""
    xml_path = lazy_shared_datadir / "simple_invalid.xml"
    tree = ET.parse(xml_path)  # pylint: disable=c-extension-no-member
    result = dtd_validator.validate(tree)
    assert not result.is_valid
    assert result.validator_name == DTDValidator.VALIDATOR_NAME
    assert result.message.startswith("Document does not validate against DTD")
    assert not result.has_warnings
    assert len(result.errors) == 2


# --- RelaxNG Compact ----


def test_rnc_validator_valid(rnc_validator, lazy_shared_datadir):
    """Test the RelaxNG validator against a valid document."""
    xml_path = lazy_shared_datadir / "simple.xml"
    tree = ET.parse(xml_path)  # pylint: disable=c-extension-no-member
    result = rnc_validator.validate(tree)
    assert result.is_valid
    assert (
        result.message
        == f"Document validates against schema {rnc_validator.schema_uri}"
    )
    assert result.validator_name == RelaxNGCompactValidator.VALIDATOR_NAME
    assert not result.has_warnings


def test_rnc_validator_invalid_document(rnc_validator, lazy_shared_datadir):
    """Test the XSD validator with an invalid document."""
    xml_path = lazy_shared_datadir / "simple_invalid.xml"
    tree = ET.parse(xml_path)  # pylint: disable=c-extension-no-member
    result = rnc_validator.validate(tree)
    assert not result.is_valid
    assert result.validator_name == RelaxNGCompactValidator.VALIDATOR_NAME
    assert result.message.startswith("Document does not validate against schema")
    assert not result.has_warnings
    assert len(result.errors) == 1


def test_rnc_validator_with_invalid_schema(lazy_shared_datadir, invalid_rnc_uri):
    """Test the LelaxNG validator with an invalid schema."""

    # pylint: disable=protected-access

    # if creation of the validator fails, it should set the _creation_error
    # attribute and not raise an exception
    broken_validator = RelaxNGCompactValidator(invalid_rnc_uri)
    assert (
        broken_validator._creation_error
        is not None  
    )

    # validating should always return the same error message, regardless of the input
    # document, because the validator could not be created successfully.
    xml_path = lazy_shared_datadir / "simple.xml"
    tree = ET.parse(xml_path)  # pylint: disable=c-extension-no-member
    result = broken_validator.validate(tree)
    assert not result.is_valid
    assert result.validator_name == RelaxNGCompactValidator.VALIDATOR_NAME
    assert len(result.errors) > 0
    assert result.message.startswith("Unable to create the validator")


# --- RelaxNG ----


def test_rng_validator_valid(rng_validator, lazy_shared_datadir):
    """Test the RelaxNG validator against a valid document."""
    xml_path = lazy_shared_datadir / "simple.xml"
    tree = ET.parse(xml_path)  # pylint: disable=c-extension-no-member
    result = rng_validator.validate(tree)
    assert result.is_valid
    assert (
        result.message
        == f"Document validates against schema {rng_validator.schema_uri}"
    )
    assert result.validator_name == RelaxNGValidator.VALIDATOR_NAME
    assert not result.has_warnings


def test_rng_validator_invalid_document(rng_validator, lazy_shared_datadir):
    """Test the XSD validator with an invalid document."""
    xml_path = lazy_shared_datadir / "simple_invalid.xml"
    tree = ET.parse(xml_path)  # pylint: disable=c-extension-no-member
    result = rng_validator.validate(tree)
    assert not result.is_valid
    assert result.validator_name == RelaxNGValidator.VALIDATOR_NAME
    assert result.message.startswith("Document does not validate against schema")
    assert not result.has_warnings
    assert len(result.errors) == 1


def test_rng_validator_with_invalid_schema(lazy_shared_datadir, invalid_rng_uri):
    """Test the LelaxNG validator with an invalid schema."""
    # if creation of the validator fails, it should set the _creation_error
    # attribute and not raise an exception
    broken_validator = RelaxNGValidator(invalid_rng_uri)
    assert (
        broken_validator._creation_error
        is not None  ## pylint: disable=protected-access
    )

    # validating should always return the same error message, regardless of the input
    # document, because the validator could not be created successfully.
    xml_path = lazy_shared_datadir / "simple.xml"
    tree = ET.parse(xml_path)  # pylint: disable=c-extension-no-member
    result = broken_validator.validate(tree)
    assert not result.is_valid
    assert result.validator_name == RelaxNGValidator.VALIDATOR_NAME
    assert len(result.errors) > 0
    assert result.message.startswith("Unable to create the validator")


# ---- Schematron ----


def test_schematron_validator_init(
    lxml_schematron_validator, saxon_schematron_validator
):
    "Test if the validator used in the validator factory is the correct one."
    assert isinstance(
        lxml_schematron_validator.schema_validator, lxml.isoschematron.Schematron
    )
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
        ("simple.unknown", None),
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
    assert (
        broken_validator._creation_error
        is not None  
    )

    # validating should return the SubResult set when object initialiation failed
    # (and not try to validate the document)
    xml_path = lazy_shared_datadir / "simple.xml"
    tree = ET.parse(xml_path)  # pylint: disable=c-extension-no-member
    result = broken_validator.validate(tree)
    assert not result.is_valid
    assert result.validator_name == SchematronValidator.LXML_VALIDATOR_NAME
    assert len(result.errors) >= 0
    assert result.message.startswith("Unable to create the Schematron validator")


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
    assert result.validator_name == SchematronValidator.SAXON_VALIDATOR_NAME
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
    x = saxon_schematron_validator.schema_uri
    tree = ET.parse(xml_path)  # pylint: disable=c-extension-no-member
    result = saxon_schematron_validator.validate(tree)
    assert not result.is_valid
    assert result.validator_name == SchematronValidator.SAXON_VALIDATOR_NAME

    assert result.message.startswith("Document does not validate against schema")
    assert not result.has_warnings
    assert len(result.errors) > 0
    assert "Only 'product' nodes are allowed" in result.errors[0]
