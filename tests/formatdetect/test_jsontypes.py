import json
import pytest
from gamslib.formatdetect.jsontypes import is_json_type
from gamslib.formatdetect.jsontypes import is_jsonl
from pathlib import Path
from gamslib.formatdetect.jsontypes import guess_json_format
from gamslib.formatdetect.jsontypes import get_format_info
from gamslib.formatdetect.formatinfo import FormatInfo
from gamslib.formatdetect.formatinfo import SubType


def test_is_json_type_with_known_json_mime_types():
    """Test if known JSON MIME types are recognized as JSON."""
    assert is_json_type("application/json") is True
    assert is_json_type("application/ld+json") is True
    assert is_json_type("application/schema+json") is True
    assert is_json_type("application/jsonl") is True


# def test_is_json_type_with_known_mimetypes():
#     assert is_json_type("application/json") is True
#     assert is_json_type("application/ld+json") is True


def test_is_json_type_with_unknown_mime_types():
    """Test if unknown MIME types are not recognized as JSON."""
    assert is_json_type("text/plain") is False
    assert is_json_type("application/xml") is False
    assert is_json_type("image/png") is False


def test_is_json_type_with_empty_string():
    """Test if empty string is not recognized as JSON."""
    assert is_json_type(None) is False
    assert is_json_type("") is False


def test_is_json_type_with_invalid_mime_type():
    """Test if invalid MIME types are not recognized as JSON."""
    assert is_json_type("invalid/mime") is False


def test_is_jsonl_with_valid_jsonl():
    """Test if valid JSONL is recognized as JSONL."""
    data = '{"name": "John"}\n{"name": "Jane"}'
    assert is_jsonl(data) is True


def test_is_jsonl_with_invalid_jsonl():
    """Test if invalid JSONL is not recognized as JSONL."""
    data = '{"name": "John"}\n{"name": "Jane"\n{"name": "Doe"}'
    assert is_jsonl(data) is False


def test_is_jsonl_with_empty_string():
    """Test if empty string is not recognized as JSONL."""
    data = ""
    assert is_jsonl(data) is False


def test_is_jsonl_with_single_valid_json():
    """Test if single valid JSON is not recognized as JSONL."""
    data = '{"name": "John"}'
    assert is_jsonl(data) is True


def test_is_jsonl_with_mixed_valid_and_invalid_json():
    """Test if mixed valid and invalid JSON is not recognized as JSONL."""
    data = '{"name": "John"}\n{"name": "Jane"}\nInvalid JSON'
    assert is_jsonl(data) is False


def test_guess_json_format_with_jsonld_extension(tmp_path):
    """Test if a file with .jsonld extension is recognized as JSON-LD."""
    file = tmp_path / "test.jsonld"
    file.write_text('{"@context": "http://schema.org"}', encoding="utf-8")
    assert guess_json_format(file) == SubType.JSONLD


def test_guess_json_format_with_json_schema(tmp_path):
    """Test if a file with JSON Schema is recognized as JSON-Schema."""
    file = tmp_path / "test.json"
    file.write_text(
        '{"$schema": "https://json-schema.org/draft/2020-12/schema"}', encoding="utf-8"
    )
    assert guess_json_format(file) == SubType.JSONSCHEMA


def test_guess_json_format_with_jsonld_content(tmp_path):
    """Test if a file with JSON-LD content is recognized as JSON-LD."""
    file = tmp_path / "test.json"
    file.write_text('{"@context": "http://schema.org"}', encoding="utf-8")
    assert guess_json_format(file) == SubType.JSONLD


def test_guess_json_format_with_jsonl_content(tmp_path):
    """Test if a file with JSON Lines content is recognized as JSON Lines."""
    file = tmp_path / "test.json"
    file.write_text('{"name": "John"}\n{"name": "Jane"}', encoding="utf-8")
    assert guess_json_format(file) == SubType.JSONL


def test_guess_json_format_with_plain_json(tmp_path):
    """Test if a plain JSON file is recognized as JSON."""
    file = tmp_path / "test.json"
    file.write_text('{"name": "John"}', encoding="utf-8")
    assert guess_json_format(file) == SubType.JSON


def test_guess_json_format_with_invalid_json(tmp_path):
    """Test if an invalid JSON file raises JSONDecodeError."""
    file = tmp_path / "test.json"
    file.write_text('{"name": "John"', encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        guess_json_format(file)


def test_get_format_info_with_jsonld(tmp_path):
    """Test get_format_info with a JSON-LD file."""
    file = tmp_path / "test.jsonld"
    file.write_text('{"@context": "http://schema.org"}', encoding="utf-8")
    mimetype, subtype = get_format_info(file, "application/ld+json")
    assert mimetype == "application/ld+json"
    assert subtype == "JSON-LD"


def test_get_format_info_with_json_schema(tmp_path):
    """Test get_format_info with a JSON Schema file."""
    file = tmp_path / "test.json"
    file.write_text(
        '{"$schema": "https://json-schema.org/draft/2020-12/schema"}', encoding="utf-8"
    )
    mimetype, subtype = get_format_info(file, "application/schema+json")
    assert mimetype == "application/json"
    assert subtype == "JSON-Schema"


def test_get_format_info_with_jsonl(tmp_path):
    """Test get_format_info with a JSON Lines file."""
    file = tmp_path / "test.json"
    file.write_text('{"name": "John"}\n{"name": "Jane"}', encoding="utf-8")
    mimetype, subtype = get_format_info(file, "application/jsonl")
    assert mimetype == "application/json"
    assert subtype == "JSON Lines"


def test_get_format_info_with_plain_json(tmp_path):
    """Test get_format_info with a plain JSON file."""
    file = tmp_path / "test.json"
    file.write_text('{"name": "John"}', encoding="utf-8")
    mimetype,subtype = get_format_info(file, "application/json")
    assert mimetype == "application/json"
    assert subtype == "JSON"


def test_get_format_info_with_unknown_mime_type(tmp_path):
    """Test get_format_info with an unknown MIME type."""
    file = tmp_path / "test.json"
    file.write_text('{"name": "John"}', encoding="utf-8")
    mimetype, subtype = get_format_info(file, "unknown/mime")
    assert mimetype == "application/json"
    assert subtype == "JSON"
