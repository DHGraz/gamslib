"""Test for validating the sip.json file."""

import json
import re

import jsonschema
import pytest
import referencing
import requests

from gamslib.sip import BagValidationError
from gamslib.sip import CURRENT_SIP_JSON_SCHEMA_URL as GAMS_SIP_SCHEMA_URL
from gamslib.sip.utils import fetch_json_schema
from gamslib.sip.validation.sip_json import validate_sip_json, validate_tag


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
    assert "Schema referenced in 'sip.json' is not a valid JSON document" in str(
        excinfo.value
    )


def test_validate_schema(valid_bag_dir):
    """Test validating a valid Bagit directory."""
    assert validate_sip_json(valid_bag_dir) is None, (
        "Should not raise an exception for valid sip.json"
    )


def test_validate_schema_no_sip(valid_bag_dir):
    "Test if validator detects missing sip.json file."
    sip = valid_bag_dir / "data" / "meta" / "sip.json"
    sip.unlink()
    with pytest.raises(BagValidationError, match=r"sip.json file does not exist"):
        validate_sip_json(valid_bag_dir)


def test_validate_schema_no_schema(valid_bag_dir):
    "Test if validator detects sip.json file misses the $schema entry."
    sip_json_file = valid_bag_dir / "data" / "meta" / "sip.json"
    data = json.load(sip_json_file.open())
    data.pop("$schema")
    sip_json_file.write_text(json.dumps(data))
    with pytest.raises(
        BagValidationError, match=re.escape("Missing '$schema' in sip.json")
    ):
        validate_sip_json(valid_bag_dir)


def test_validate_schema_no_schema_value(valid_bag_dir):
    "Test if validator detects sip.json file misses the $schema entry."
    sip_json_file = valid_bag_dir / "data" / "meta" / "sip.json"
    data = json.load(sip_json_file.open())
    data["$schema"] = ""
    sip_json_file.write_text(json.dumps(data))
    with pytest.raises(
        BagValidationError, match=r"Unsupported JSON schema in sip.json"
    ):
        validate_sip_json(valid_bag_dir)


def test_validate_schema_invalid_json(valid_bag_dir):
    "Test if validator detects sip.json file has invalid JSON content."
    sip = valid_bag_dir / "data" / "meta" / "sip.json"
    sip.write_text("foo")
    with pytest.raises(BagValidationError, match="Invalid JSON in sip.json"):
        validate_sip_json(valid_bag_dir)


def test_validate_mainresource(valid_bag_dir):
    "Test if validator detects if mainResource does not exists."
    sip = valid_bag_dir / "data" / "meta" / "sip.json"
    data = json.load(sip.open())

    # if mainResource is set corectly, the test should pass
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


# def test_missing_sip_json(tmp_bag_dir):
def test_missing_sip_json(shared_datadir):
    """Test error when sip.json file does not exist."""
    sip_json_file = shared_datadir / "valid_bag" / "data" / "meta" / "sip.json"
    sip_json_file.unlink()
    with pytest.raises(BagValidationError, match=r"sip.json file does not exist"):
        validate_sip_json(shared_datadir / "valid_bag")


def test_invalid_json_in_sip_json(tmp_bag_dir):
    """Test error when sip.json contains invalid JSON."""
    sip_json_file = tmp_bag_dir / "data" / "meta" / "sip.json"
    sip_json_file.write_text("{invalid json", encoding="utf-8")
    with pytest.raises(BagValidationError, match=r"Invalid JSON in sip.json"):
        validate_sip_json(tmp_bag_dir)


def test_missing_schema_key(valid_bag_dir):
    """Test error when $schema key is missing in sip.json."""
    sip_json_file = valid_bag_dir / "data" / "meta" / "sip.json"
    data = json.load(sip_json_file.open())
    data.pop("$schema")
    sip_json_file.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(BagValidationError, match=r"Missing '\$schema' in sip.json"):
        validate_sip_json(valid_bag_dir)


# we skip this because it's really slow (waiting for timeout)
# @pytest.mark.skip
def test_main_resource_not_in_content_files(valid_bag_dir):
    """Test error when mainResource is not listed in contentFiles."""
    sip_json_file = valid_bag_dir / "data" / "meta" / "sip.json"
    # set mainResource to a value that is not in contentFiles
    data = json.load(sip_json_file.open())
    data["mainResource"] = "missing_resource"
    sip_json_file.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(BagValidationError, match="is not listed in contentFiles"):
        validate_sip_json(valid_bag_dir)


def test_validate_sip_json_valid(shared_datadir):
    """Test successful validation of a correct sip.json."""
    bag_dir = shared_datadir / "valid_bag"
    assert validate_sip_json(bag_dir) is None


def test_validate_sip_json_invalid_schema(tmp_bag_dir):
    """The schema referenced in sip.json must be the GAMS schema."""
    data = {
        "$schema": "http://example.com/unsupported-schema.json",
        "mainResource": "res1",
        "contentFiles": [{"dsid": "res1"}],
        "extra": "not allowed",
    }
    write_sip_json(tmp_bag_dir, data)
    with pytest.raises(BagValidationError, match="Unsupported JSON schema"):
        validate_sip_json(tmp_bag_dir)


# def test_validate_sip_json_schema_validation_error(monkeypatch, tmp_bag_dir):
def test_validate_sip_json_schema_validation_error(valid_bag_dir):
    """Test error when JSON schema validation fails (extra property not allowed)."""
    sip_json_file = valid_bag_dir / "data" / "meta" / "sip.json"
    data = json.load(sip_json_file.open())
    data["extra"] = "not allowed"
    sip_json_file.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(BagValidationError, match=r"Invalid JSON in sip.json"):
        validate_sip_json(valid_bag_dir)


def test_validate_sip_json_schema_error(monkeypatch, tmp_bag_dir):
    """Test error when the schema itself is invalid."""

    # patch the jsonschema.validate to raise a SchemaError
    def raise_schema_error(data, schema):
        raise jsonschema.SchemaError("Invalid schema")

    monkeypatch.setattr("jsonschema.validate", raise_schema_error)
    with pytest.raises(
        BagValidationError,
        match=r"The JSON Schema referenced in 'sip.json' is not valid",
    ):
        validate_sip_json(tmp_bag_dir)


def test_validate_sip_json_unresolvable_schema(monkeypatch, tmp_bag_dir):
    """Test error when a schema reference cannot be resolved."""

    def raise_unresolvable(data, schema):
        raise referencing.exceptions.Unresolvable("Unresolvable reference")

    monkeypatch.setattr("jsonschema.validate", raise_unresolvable)

    with pytest.raises(
        BagValidationError, match=r"Failed to resolve a reference in the JSON Schema"
    ):
        validate_sip_json(tmp_bag_dir)


@pytest.mark.parametrize(
    "tag",
    [
        "abc",
        "tag-01",
        "tag._~withchars",
        "  spaced_tag  ",
        "A" * 50,
    ],
)
def test_validate_tag_valid_values(tag):
    """validate_tag accepts allowed characters and valid lengths."""
    assert validate_tag(tag) is None


@pytest.mark.parametrize("tag", ["", "   "])
def test_validate_tag_rejects_empty_or_whitespace(tag):
    """Empty values after stripping are invalid."""
    with pytest.raises(ValueError, match=r"must not be empty"):
        validate_tag(tag)


@pytest.mark.parametrize("tag", ["ab", "  a "])
def test_validate_tag_rejects_too_short_values(tag):
    """Tags shorter than the configured minimum length are invalid."""
    with pytest.raises(ValueError, match=r"minimum length"):
        validate_tag(tag)


def test_validate_tag_rejects_too_long_values():
    """Tags longer than the configured maximum length are invalid."""
    with pytest.raises(ValueError, match=r"exceeds maximum length"):
        validate_tag("a" * 51)


@pytest.mark.parametrize("tag", ["bad tag", "bad/tag", "bad+tag", "täg"])
def test_validate_tag_rejects_invalid_characters(tag):
    """Only letters, digits, and - . _ ~ are allowed."""
    with pytest.raises(ValueError, match=r"contains invalid characters"):
        validate_tag(tag)
