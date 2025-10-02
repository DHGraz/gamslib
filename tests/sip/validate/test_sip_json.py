"""Test for validating the sip.json file."""

import json
import re

import jsonschema
import pytest
import referencing
import requests

from gamslib.sip import BagValidationError
from gamslib.sip.utils import fetch_json_schema, GAMS_SIP_SCHEMA_URL
from gamslib.sip.validation.sip_json import validate_sip_json


@pytest.fixture(name="tmp_bag_dir")
def tmp_bag_dir_fixture(tmp_path):
    """Create a temporary bag directory structure with sip.json."""
    bag_dir = tmp_path / "bag"
    sip_json_dir = bag_dir / "data" / "meta"
    sip_json_dir.mkdir(parents=True)
    sip_json = sip_json_dir / "sip.json"
    sip_json.write_text(
        json.dumps(
            {
                "$schema": GAMS_SIP_SCHEMA_URL,
                "mainResource": "res1",
                "contentFiles": [{"dsid": "res1"}],
            }
        ),
        encoding="utf-8",
    )
    return bag_dir


def test_fetch_schema_fails():
    """Test what happens if fetching the schema fails."""
    with pytest.raises(BagValidationError, match="Failed to fetch JSON schema from"):
        # a non 200 response
        fetch_json_schema("http://example.com/foo/bar.json")


def test_fetch_schema_invalid_json(monkeypatch):
    """Test if the fetched schema is detected as invalid JSON."""

    # pylint: disable=unused-argument, protected-access
    # we monkey patch the Response object to return invalid JSON
    def monkey_get(url, timeout=None):
        response = requests.Response()
        response._content = b"{\"foo\": 'http://example.com'}"
        response.status_code = 200
        return response

    # Response is invalid JSON
    monkeypatch.setattr("requests.get", monkey_get)
    with pytest.raises(BagValidationError) as excinfo:
        fetch_json_schema("http://example.com")
    monkeypatch.undo()
    assert "Schema referenced in 'sip.json' is not valid JSON" in str(excinfo.value)


def test_validate_schema(valid_bag_dir):
    """Test validating a valid Bagit directory."""
    assert validate_sip_json(valid_bag_dir) is None, (
        "Should not raise an exception for valid sip.json"
    )


def test_validate_schema_no_sip(valid_bag_dir):
    "Test if validator detects missing sip.json file."
    sip = valid_bag_dir / "data" / "meta" / "sip.json"
    sip.unlink()
    with pytest.raises(BagValidationError, match="sip.json file does not exist"):
        validate_sip_json(valid_bag_dir)


def test_validate_schema_no_schema(valid_bag_dir):
    "Test if validator detects sip.json file misses the $schema entry."
    sip = valid_bag_dir / "data" / "meta" / "sip.json"
    data = json.load(sip.open())
    data.pop("$schema")
    sip.write_text(json.dumps(data))
    with pytest.raises(
        BagValidationError, match=re.escape("Missing '$schema' in sip.json")
    ):
        validate_sip_json(valid_bag_dir)


def test_validate_schema_no_schema_value(valid_bag_dir):
    "Test if validator detects sip.json file misses the $schema entry."
    sip = valid_bag_dir / "data" / "meta" / "sip.json"
    data = json.load(sip.open())
    data["$schema"] = ""
    sip.write_text(json.dumps(data))
    with pytest.raises(BagValidationError, match="No scheme supplied"):
        validate_sip_json(valid_bag_dir)


def test_validate_schema_invalid_json(valid_bag_dir):
    "Test if validator detects sip.json file has invalid JSON content."
    sip = valid_bag_dir / "data" / "meta" / "sip.json"
    sip.write_text("foo")
    with pytest.raises(BagValidationError, match="Invalid JSON in sip.json"):
        validate_sip_json(valid_bag_dir)
    # assert "Invalid JSON in sip.json" in str(excinfo.value)


def test_validate_mainresource(valid_bag_dir):
    "Test if validator detects if mainResource does not exists."
    sip = valid_bag_dir / "data" / "meta" / "sip.json"
    data = json.load(sip.open())

    # if mainResource is set corectly, the should pass
    assert validate_sip_json(valid_bag_dir) is None, (
        "Should not raise an exception for valid sip.json"
    )

    # replace mainResource to a non existing resource
    data["mainResource"] = "inexistent"
    sip.write_text(json.dumps(data))
    with pytest.raises(BagValidationError, match="is not listed"):
        validate_sip_json(valid_bag_dir)


def test_validate_sip_json_issue_9(valid_bag_dir):
    "Opening sip.json had not explicit utf-8 set."
    json_path = valid_bag_dir / "data" / "meta" / "sip.json"
    data = json.load(json_path.open())
    data["description"] = (
        "This is a test description with special characters: ñ, é, ü, 字"
    )
    json_path.write_text(json.dumps(data), encoding="utf-8")

    assert validate_sip_json(valid_bag_dir) is None, (
        "Should not raise an exception for valid sip.json with special characters"
    )


def write_sip_json(bag_dir, data):
    """Helper to write a sip.json file with given data."""
    sip_json_file = bag_dir / "data" / "meta" / "sip.json"
    sip_json_file.write_text(json.dumps(data), encoding="utf-8")
    return sip_json_file


def test_missing_sip_json(tmp_bag_dir):
    """Test error when sip.json file does not exist."""
    sip_json_file = tmp_bag_dir / "data" / "meta" / "sip.json"
    sip_json_file.unlink()
    with pytest.raises(BagValidationError, match="sip.json file does not exist"):
        validate_sip_json(tmp_bag_dir)


def test_invalid_json_in_sip_json(tmp_bag_dir):
    """Test error when sip.json contains invalid JSON."""
    sip_json_file = tmp_bag_dir / "data" / "meta" / "sip.json"
    sip_json_file.write_text("{invalid json", encoding="utf-8")
    with pytest.raises(BagValidationError, match="Invalid JSON in sip.json"):
        validate_sip_json(tmp_bag_dir)


def test_missing_schema_key(tmp_bag_dir):
    """Test error when $schema key is missing in sip.json."""
    data = {"mainResource": "res1", "contentFiles": [{"dsid": "res1"}]}
    write_sip_json(tmp_bag_dir, data)
    with pytest.raises(BagValidationError, match="Missing '\\$schema' in sip.json"):
        validate_sip_json(tmp_bag_dir)


# we skip this because it's really slow (waiting for timeout)
@pytest.mark.skip
def test_main_resource_not_in_content_files(tmp_bag_dir, monkeypatch):
    """Test error when mainResource is not listed in contentFiles."""
    data = {
        "$schema": "http://example.com/schema.json",
        "mainResource": "missing_resource",
        "contentFiles": [{"dsid": "res1"}],
    }
    write_sip_json(tmp_bag_dir, data)

    # Patch fetch_json_schema to return a minimal valid schema
    monkeypatch.setattr(
        "gamspackaging.utils.fetch_json_schema", lambda url: {"type": "object"}
    )

    with pytest.raises(BagValidationError, match="404"):
        validate_sip_json(tmp_bag_dir)


def test_validate_sip_json_valid(monkeypatch, tmp_bag_dir):
    """Test successful validation of a correct sip.json."""
    data = {
        "$schema": "http://example.com/schema.json",
        "mainResource": "res1",
        "contentFiles": [{"dsid": "res1"}],
    }
    write_sip_json(tmp_bag_dir, data)

    # Patch fetch_json_schema to return a minimal valid schema
    monkeypatch.setattr(
        "gamslib.sip.utils.fetch_json_schema",
        lambda url: {
            "type": "object",
            "properties": {
                "$schema": {"type": "string"},
                "mainResource": {"type": "string"},
                "contentFiles": {"type": "array"},
            },
            "required": ["mainResource", "contentFiles"],
            "additionalProperties": False,
        },
    )

    assert validate_sip_json(tmp_bag_dir) is None


def test_validate_sip_json_schema_validation_error(monkeypatch, tmp_bag_dir):
    """Test error when JSON schema validation fails (extra property not allowed)."""
    data = {
        "$schema": "http://example.com/schema.json",
        "mainResource": "res1",
        "contentFiles": [{"dsid": "res1"}],
        "extra": "not allowed",
    }
    write_sip_json(tmp_bag_dir, data)

    # Schema does not allow 'extra'
    monkeypatch.setattr(
        "gamslib.sip.utils.fetch_json_schema",
        lambda url: {
            "type": "object",
            "properties": {
                "mainResource": {"type": "string"},
                "contentFiles": {"type": "array"},
            },
            "required": ["mainResource", "contentFiles"],
            "additionalProperties": False,
        },
    )

    with pytest.raises(BagValidationError, match="Invalid JSON in sip.json"):
        validate_sip_json(tmp_bag_dir)


def test_validate_sip_json_schema_error(monkeypatch, tmp_bag_dir):
    """Test error when the schema itself is invalid."""

    # patch the jsonschema.validate to raise a SchemaError
    def raise_schema_error(data, schema):
        raise jsonschema.SchemaError("Invalid schema")

    monkeypatch.setattr("jsonschema.validate", raise_schema_error)
    with pytest.raises(
        BagValidationError,
        match="The JSON Schema referenced in 'sip.json' is not valid",
    ):
        validate_sip_json(tmp_bag_dir)


def test_validate_sip_json_unresolvable_schema(monkeypatch, tmp_bag_dir):
    """Test error when a schema reference cannot be resolved."""

    def raise_unresolvable(data, schema):
        raise referencing.exceptions.Unresolvable("Unresolvable reference")

    monkeypatch.setattr("jsonschema.validate", raise_unresolvable)

    with pytest.raises(
        BagValidationError, match="Failed to resolve a reference in the JSON Schema"
    ):
        validate_sip_json(tmp_bag_dir)
