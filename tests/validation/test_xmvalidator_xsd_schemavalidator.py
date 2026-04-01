"""Tests for the XMLSchemaValidator class in xmlvalidator.py."""
import pytest

from gamslib.validation.xmlvalidator import XMLSchemaValidator


from lxml import etree as ET

# pylint: disable=protected-access
# pylint: disable=c-extension-no-member

@pytest.fixture(name="xmlschema_validator")
def create_xmlschema_validator(lazy_shared_datadir):
    """Create a XMLSchemaValidator object based on a valid schema."""
    schema_uri = (lazy_shared_datadir / "schemas" / "simple.xsd").resolve().as_uri()
    validator = XMLSchemaValidator(schema_uri)
    return validator

@pytest.fixture(name="invalid_xmlschema_uri")
def create_invalid_xmlschema_uri(lazy_shared_datadir, tmp_path):
    """Create a invalid xmlschema file and return its location as URI."""
    # Create an invalid schema by taking a valid one and insert errors
    valid_schema_path = lazy_shared_datadir / "schemas" / "simple.xsd"
    data = valid_schema_path.read_text().replace("<xs:element", "<<xs:element")
    invalid_schema_path = tmp_path / "invalid.xsd"
    invalid_schema_path.write_text(data)
    return invalid_schema_path.resolve().as_uri()

def test_invalid_schema(lazy_shared_datadir, invalid_xmlschema_uri):
    """Test the XSD validator with an invalid schema."""
    # if creation of the validator fails, it should set the _creation_error
    # attribute and not raise an exception
    broken_validator = XMLSchemaValidator(invalid_xmlschema_uri)
    assert broken_validator._creation_error is not None

    # validating should always return the same error message, regardless of the input
    # document, because creation of the validator failed.
    xml_path = lazy_shared_datadir / "simple.xml"
    tree = ET.parse(xml_path)  
    result = broken_validator.validate(tree)
    assert not result.is_valid
    assert result.validator_name == XMLSchemaValidator.VALIDATOR_NAME
    assert len(result.errors) > 0
    assert result.message.startswith("Unable to create the validator")


def test_remote_schema_via_catalog():
    """Create a validator with a schema URI that is only resolvable via the catalog.
    """
    schema_uri = "http://www.lido-schema.org/schema/v1.1/lido-v1.1.xsd"
    validator = XMLSchemaValidator(schema_uri)
    assert validator.schema_uri == schema_uri
    assert validator._creation_error is None
    assert validator.schema_validator is not None

def test_remote_schema_not_in_catalog_not_allowed(monkeypatch):
    """Test a remote schema not in catalog and not in allowed.
    """
    schema_uri = "http://gams.uni-graz.at/lido/1.1/lido.xsd"

    # Not in catalog, not in safe hosts should fail
    validator = XMLSchemaValidator(schema_uri)
    assert validator.schema_uri == schema_uri
    assert validator._creation_error is not None


def test_remote_schema_not_in_catalog_allowed(monkeypatch):
    "Test for remote schema on allowed host."
    monkeypatch.setenv("GAMSLIB_SAFE_XML_HOSTS", "gams.uni-graz.at,localhost")

    #schema_uri = "http://localhost:8000/opengis/gml/3.1.1/base/dynamicFeature.xsd"
    schema_uri = "http://schemas.opengis.net/gml/3.3.1/base/gml.xsd"
    #schema_uri = "http://localhost:8000/lido/1.0/lido.xsd"
    #schema_uri = "http://localhost:8000/lido/1.0/tei.xsd"
    #schema_uri = "http://localhost:8000/lido/1.0/dcr.xsd"
    # parser = ET.XMLParser(no_network=False)
    # try:
    #     tree = ET.parse(file=schema_uri, parser=parser)  # pylint: disable=c-extension-no-member
    #     x = ET.XMLSchema(tree)
    # except Exception as exp:
    #     print(parser.error_log)
    #     assert False
    validator = XMLSchemaValidator(schema_uri)
    assert validator.schema_uri == schema_uri
    assert validator._creation_error is None


def test_validate_valid_document(xmlschema_validator, lazy_shared_datadir):
    """Test the XSD validator against valid documents."""
    xml_path = lazy_shared_datadir / "simple.xml"
    tree = ET.parse(xml_path)
    result = xmlschema_validator.validate(tree)
    assert result.is_valid
    assert (
        result.message
        == f"Document validates against schema {xmlschema_validator.schema_uri}"
    )
    assert result.validator_name == XMLSchemaValidator.VALIDATOR_NAME
    assert not result.has_warnings
    assert result.errors == []

def test_validate_invalid_document(xmlschema_validator, lazy_shared_datadir):
    """Test the XSD validator with an invalid document."""
    xml_path = lazy_shared_datadir / "simple_invalid.xml"
    tree = ET.parse(xml_path)  # pylint: disable=c-extension-no-member
    result = xmlschema_validator.validate(tree)
    assert not result.is_valid
    assert result.validator_name == XMLSchemaValidator.VALIDATOR_NAME
    assert result.message.startswith("Document does not validate against schema")
    assert not result.has_warnings
    assert len(result.errors) == 1

@pytest.mark.parametrize(
    "xml_file, schema_file",
    [
        ("simple.xml", "simple.xsd"),
        ("lido.xml", "https://gams.uni-graz.at/lido/1.0/lido.xsd"),
#         "http://www.lido-schema.org/schema/v1.0/lido-v1.0.xsd"),
#        ("lido.xml", "http://www.lido-schema.org/schema/v1.1/lido-v1.1.xsd"),
    ])
def test_xsd_validator_validiate_with_real_schemas(xml_file, schema_file, lazy_shared_datadir, monkeypatch):
    """Test the XSD validator with real schemas and documents.

    We need this, as we've noticed problems with some schema files.
    """
    monkeypatch.setenv("GAMSLIB_SAFE_XML_HOSTS", "gams.uni-graz.at")
    if schema_file.startswith("http://") or schema_file.startswith("https://"):
        schema_uri = schema_file
    else:
        schema_path = lazy_shared_datadir / "schemas" / schema_file
        assert schema_path.exists()
        schema_uri = schema_path.resolve().as_uri()

    validator = XMLSchemaValidator(schema_uri)
    xml_path = lazy_shared_datadir / xml_file
    tree = ET.parse(xml_path)  # pylint: disable=c-extension-no-member
    result = validator.validate(tree)
    assert result.is_valid








