"""Test for validating the sip.json file."""

import json
import re


import pytest
import requests

from gamslib.sip import BagValidationError
from gamslib.sip.utils import fetch_json_schema
from gamslib.sip.validation.sip_json import validate_sip_json


@pytest.fixture
def tmp_bag_dir(tmp_path):
    """Create a temporary bag directory structure with sip.json."""
    bag_dir = tmp_path / "bag"
    sip_json_dir = bag_dir / "data" / "meta"
    sip_json_dir.mkdir(parents=True)
    return bag_dir

def test_fetch_schema_fails():
    """Test what happens if fetching the schema fails."""
    with pytest.raises(
        BagValidationError, match="Failed to fetch JSON schema from"
    ):
        # a non 200 response
        fetch_json_schema("http://example.com/foo/bar.json")


def test_fetch_schema_invalid_json(monkeypatch):
    """Test if the fetched schema is detected as invalid JSON."""

    #pylint: disable=unused-argument, protected-access
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
    sip_json_file = bag_dir / "data" / "meta" / "sip.json"
    sip_json_file.write_text(json.dumps(data), encoding="utf-8")
    return sip_json_file

def test_missing_sip_json(tmp_bag_dir):
    """Test error when sip.json file does not exist."""
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
    data = {
        "mainResource": "res1",
        "contentFiles": [{"dsid": "res1"}]
    }
    write_sip_json(tmp_bag_dir, data)
    with pytest.raises(BagValidationError, match="Missing '\\$schema' in sip.json"):
        validate_sip_json(tmp_bag_dir)

# we skip this because it's really slow (witing for timeout)
@pytest.mark.skip
def test_main_resource_not_in_content_files(tmp_bag_dir, monkeypatch):
    """Test error when mainResource is not listed in contentFiles."""
    data = {
        "$schema": "http://example.com/schema.json",
        "mainResource": "missing_resource",
        "contentFiles": [{"dsid": "res1"}]
    }
    write_sip_json(tmp_bag_dir, data)

    # Patch fetch_json_schema to return a minimal valid schema
    monkeypatch.setattr(
        "gamspackaging.utils.fetch_json_schema",
        lambda url: {"type": "object"}
    )

    with pytest.raises(BagValidationError, match="404"):
        validate_sip_json(tmp_bag_dir)

# def test_valid_sip_json(tmp_bag_dir, monkeypatch):
#     """Test successful validation of a correct sip.json."""
#     data = {
#         "$schema": "http://example.com/schema.json",
#         "mainResource": "res1",
#         "contentFiles": [{"dsid": "res1"}]
#     }
#     write_sip_json(tmp_bag_dir, data)

#     monkeypatch.setattr(
#         "gamspackaging.utils.fetch_json_schema",
#         lambda url: {"type": "object"}
#     )

#     assert validate_sip_json(tmp_bag_dir) is None

# def test_schema_validation_error(tmp_bag_dir, monkeypatch):
#     """Test error when JSON schema validation fails."""
#     data = {
#         "$schema": "http://example.com/schema.json",
#         "mainResource": "res1",
#         "contentFiles": [{"dsid": "res1"}],
#         "extra": "not allowed"
#     }
#     write_sip_json(tmp_bag_dir, data)

#     # Schema does not allow 'extra'
#     monkeypatch.setattr(
#         "gamspackaging.utils.fetch_json_schema",
#         lambda url: {
#             "type": "object",
#             "properties": {
#                 "mainResource": {"type": "string"},
#                 "contentFiles": {"type": "array"}
#             },
#             "additionalProperties": False
#         }
#     )

#     with pytest.raises(BagValidationError, match="Invalid JSON in sip.json"):
#         validate_sip_json(tmp_bag_dir)

