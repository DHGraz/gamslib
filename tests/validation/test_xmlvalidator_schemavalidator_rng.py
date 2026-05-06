"Tests for RelaxNGValidator and RelaxNGCompactValidator classes."

import pytest
from lxml import etree as ET

from gamslib.validation.xmlvalidator import RelaxNGCompactValidator, RelaxNGValidator


@pytest.fixture(name="rng_validator")
def create_rng_validator(lazy_shared_datadir):
    """Create a RNGValidator object."""
    schema_path = lazy_shared_datadir / "schemas" / "simple.rng"
    assert schema_path.exists()
    schema_uri = schema_path.resolve().as_uri()
    validator = RelaxNGValidator(schema_uri)
    return validator


# @pytest.fixture(name="rnc_validator")
# def create_rnc_validator(lazy_shared_datadir):
#     """Create a RNCValidator object."""
#     schema_path = lazy_shared_datadir / "schemas" / "simple.rnc"
#     assert schema_path.exists()
#     schema_uri = schema_path.resolve().as_uri()
#     validator = RelaxNGCompactValidator(schema_uri)
#     return validator


@pytest.fixture(name="invalid_rng_uri")
def create_invalid_rng_uri(lazy_shared_datadir, tmp_path):
    """Create a invalid RelaxNG file and return its location as URI."""
    # Create an invalid schema by taking a valid one and insert errors
    valid_schema_path = lazy_shared_datadir / "schemas" / "simple.rng"
    data = valid_schema_path.read_text().replace("<element", "<<element")
    invalid_schema_path = tmp_path / "invalid.rng"
    invalid_schema_path.write_text(data)
    return invalid_schema_path.resolve().as_uri()


# @pytest.fixture(name="invalid_rnc_uri")
# def create_invalid_rnc_uri(lazy_shared_datadir, tmp_path):
#     """Create a invalid RelaxNG file and return its location as URI."""
#     # Create an invalid schema by taking a valid one and insert errors
#     valid_schema_path = lazy_shared_datadir / "schemas" / "simple.rnc"
#     data = valid_schema_path.read_text().replace("start", "Xstart")
#     invalid_schema_path = tmp_path / "invalid.rnc"
#     invalid_schema_path.write_text(data)
#     return invalid_schema_path.resolve().as_uri()


# def test_rnc_validator_valid(rnc_validator, lazy_shared_datadir):
#     """Test the RelaxNG validator against a valid document."""
#     xml_path = lazy_shared_datadir / "simple.xml"
#     tree = ET.parse(xml_path)  # pylint: disable=c-extension-no-member
#     result = rnc_validator.validate(tree)
#     assert result.is_valid
#     assert (
#         result.message
#         == f"Document validates against schema {rnc_validator.schema_uri}"
#     )
#     assert result.validator_name == "RelaxNGCompact Validator"
#     assert not result.has_warnings


# def test_rnc_validator_invalid_document(rnc_validator, lazy_shared_datadir):
#     """Test the XSD validator with an invalid document."""
#     xml_path = lazy_shared_datadir / "simple_invalid.xml"
#     tree = ET.parse(xml_path)  # pylint: disable=c-extension-no-member
#     result = rnc_validator.validate(tree)
#     assert not result.is_valid
#     assert result.validator_name == "RelaxNGCompact Validator"
#     assert result.message.startswith("Document does not validate against schema")
#     assert not result.has_warnings
#     assert len(result.errors) == 1


# def test_rnc_validator_with_invalid_schema(lazy_shared_datadir, invalid_rnc_uri):
#     """Test the LelaxNG validator with an invalid schema."""

#     # pylint: disable=protected-access

#     # if creation of the validator fails, it should set the _creation_error
#     # attribute and not raise an exception
#     broken_validator = RelaxNGCompactValidator(invalid_rnc_uri)
#     assert broken_validator._creation_error is not None

#     # validating should always return the same error message, regardless of the input
#     # document, because the validator could not be created successfully.
#     xml_path = lazy_shared_datadir / "simple.xml"
#     tree = ET.parse(xml_path)  # pylint: disable=c-extension-no-member
#     result = broken_validator.validate(tree)
#     assert not result.is_valid
#     assert result.validator_name == "RelaxNGCompact Validator"
#     assert len(result.errors) > 0
#     assert result.message.startswith("Unable to create the validator")


# # --- RelaxNG ----


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
    assert result.validator_name == "RelaxNG Validator"
    assert not result.has_warnings


def test_rng_validator_invalid_document(rng_validator, lazy_shared_datadir):
    """Test the XSD validator with an invalid document."""
    xml_path = lazy_shared_datadir / "simple_invalid.xml"
    tree = ET.parse(xml_path)  # pylint: disable=c-extension-no-member
    result = rng_validator.validate(tree)
    assert not result.is_valid
    assert result.validator_name == "RelaxNG Validator"
    assert result.message.startswith("Document does not validate against schema")
    assert not result.has_warnings
    assert len(result.errors) == 1


def test_rng_validator_with_invalid_schema(lazy_shared_datadir, invalid_rng_uri):
    """Test the LelaxNG validator with an invalid schema."""

    # pylint: disable=protected-access

    # if creation of the validator fails, it should set the _creation_error
    # attribute and not raise an exception
    broken_validator = RelaxNGValidator(invalid_rng_uri)
    assert broken_validator._creation_error is not None

    # validating should always return the same error message, regardless of the input
    # document, because the validator could not be created successfully.
    xml_path = lazy_shared_datadir / "simple.xml"
    tree = ET.parse(xml_path)  # pylint: disable=c-extension-no-member
    result = broken_validator.validate(tree)
    assert not result.is_valid
    assert result.validator_name == "RelaxNG Validator"
    assert len(result.errors) > 0
    assert result.message.startswith("Unable to create the validator")
