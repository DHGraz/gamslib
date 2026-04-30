"These tests make sure that the sip schema does what it is supposed to do."
import json

import pytest
import jsonschema

from gamslib.sip.utils import read_sip_schema_from_package

gams_schema = read_sip_schema_from_package()

@pytest.fixture(name="sip_json")
def get_valid_sip_json(datadir) -> dict:
    """Return a valid sip.json as a dict."""
    sip_path = datadir / "sip.json"
    return json.loads(sip_path.read_text(encoding="utf-8"))

def test_validate_valid_sip_json(sip_json):
    """Test successful validation of a correct sip.json."""
    jsonschema.validate(instance=sip_json, schema=gams_schema)
   
@pytest.mark.parametrize(
    "field", [
            "recid",
            "title",
            "project",
            "creator",
            "rights",
            "contentFiles",
            "publisher",
            "source",
            "objectType",
            "sip_creation_timestamp"
    ])
def test_validate_missing_required_field(field, sip_json):
    """Test: Missing required field should raise ValidationError."""
    del sip_json[field]
    with pytest.raises(jsonschema.ValidationError, match=field) as exp:
        jsonschema.validate(instance=sip_json, schema=gams_schema)

@pytest.mark.parametrize("field", [
                "bagpath",
                "dsid",
                "mimetype",
                "creator",
                "size",
                "checksum"
    ])
def tests_validate_missing_contenttype_field(field, sip_json):
    """Test: Missing required field in contentType should raise ValidationError."""
    del sip_json["contentFiles"][0][field]
    with pytest.raises(jsonschema.ValidationError, match=field) as exp:
        jsonschema.validate(instance=sip_json, schema=gams_schema)

def test_validate_empty_content_files(sip_json):
    """Test: The contentFiles array must not be empty."""
    sip_json["contentFiles"] = []
    with pytest.raises(jsonschema.ValidationError, match="non-empty") as exp:
        jsonschema.validate(instance=sip_json, schema=gams_schema)

@pytest.mark.parametrize(
    "field, min_size", [
        ("recid", 4),
        ("title", 5),
        ("project", 2),
        ("creator", 4),
        ("rights", 3),
        ("publisher", 3),
        ("source", 3),
        ("objectType", 3)
    ]
)
def test_validate_min_object_field_sizes(field, min_size, sip_json):
    """Test: Fields with minimum size constraints should raise ValidationError if too small."""
    sip_json[field] = "x" * (min_size - 1)  # Set field to a string that is too short
    with pytest.raises(jsonschema.ValidationError, match=field):
        jsonschema.validate(instance=sip_json, schema=gams_schema)

@pytest.mark.parametrize(
    "field, min_size", [
        ("dsid", 3),
        ("mimetype", 6),
        ("creator", 3),
        ("checksum", 32),
        ("bagpath", 3),
    ]
)
def  test_validate_min_ds_field_sizes(field, min_size, sip_json):
    """Test: Fields with minimum size constraints in contentFiles should raise ValidationError if too small."""
    sip_json["contentFiles"][0][field] = "x" * (min_size - 1)  # Set field to a string that is too short
    with pytest.raises(jsonschema.ValidationError, match=field):
        jsonschema.validate(instance=sip_json, schema=gams_schema)


def test_validate_extra_field(sip_json):
    """Test: Extra fields not defined in the schema should raise ValidationError."""
    sip_json["extraField"] = "not allowed"
    with pytest.raises(jsonschema.ValidationError, match="extraField") as exp:
        jsonschema.validate(instance=sip_json, schema=gams_schema)


def test_validate_extra_field_in_content_file(sip_json):
    """Test: Extra fields in contentFiles should raise ValidationError."""
    sip_json["contentFiles"][0]["extraField"] = "not allowed"
    with pytest.raises(jsonschema.ValidationError, match="extraField") as exp:
        jsonschema.validate(instance=sip_json, schema=gams_schema)

def test_invalid_checkum_prefix(sip_json):
    """Test: Only a few prefix values are allowed."""
    sip_json["contentFiles"][0]["checksum"] = "invalidchecksum"
    with pytest.raises(jsonschema.ValidationError, match="checksum") as exp:
        jsonschema.validate(instance=sip_json, schema=gams_schema)


def test_invalid_checksum_length(sip_json):
    """Test: Checksum must be minimum  32 characters long."""
    sip_json["contentFiles"][0]["checksum"] = "md5:" + "x" * 31  # Too short
    with pytest.raises(jsonschema.ValidationError, match="checksum") as exp:
        jsonschema.validate(instance=sip_json, schema=gams_schema)  


def test_invalid_checksum_value(sip_json):
    """Test: Checksums must be hex chars .""" 
    sip_json["contentFiles"][0]["checksum"] = "md5:" + "g" * 32  # Invalid hex character
    with pytest.raises(jsonschema.ValidationError, match="checksum") as exp:
        jsonschema.validate(instance=sip_json, schema=gams_schema)