"""Tests for the FormatInfo class."""

import csv
import io
from importlib import resources
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from gamslib.formatdetect.formatinfo import (
    FormatInfo,
    SubType,
    extract_subtype_info_from_csv,
    load_subtypes_from_csv,
)


def test_load_subtypes_from_csv():
    """Test that load_subtypes_from_csv returns a list of dictionaries with the expected structure."""
    subtypes = load_subtypes_from_csv()
    assert isinstance(subtypes, list)
    assert len(subtypes) > 0
    assert all(isinstance(item, dict) for item in subtypes)
    assert all("subformat" in item for item in subtypes)
    assert all("fullname" in item for item in subtypes)
    assert all("dsname" in item for item in subtypes)
    assert all("mimetype" in item for item in subtypes)
    assert all("maintype" in item for item in subtypes)


def test_load_subtypes_from_csv_whitespace_handling(tmp_path, monkeypatch):
    """Test that whitespace is properly stripped from keys and values."""

    def mock_find_subtype_csv_files():
        return [tmp_path / "xml_subformats.csv"]

    csv_content = " subformat , full name , ds name , mimetype \n SUBFORMAT , FULL NAME, DS NAME, MIMETYPE \n"
    (tmp_path / "xml_subformats.csv").write_text(csv_content, encoding="utf-8")
    monkeypatch.setattr(
        "gamslib.formatdetect.formatinfo.find_subtype_csv_files",
        mock_find_subtype_csv_files,
    )

    result = load_subtypes_from_csv()
    assert len(result) == 1
    assert result[0]["subformat"] == "SUBFORMAT"
    assert result[0]["full name"] == "FULL NAME"
    assert result[0]["ds name"] == "DS NAME"
    assert result[0]["mimetype"] == "MIMETYPE"
    assert result[0]["maintype"] == "xml"


def test_extract_subtype_info_from_csv():
    """Test that extract_subtype_info_from_csv returns the expected dictionary structure."""
    result = extract_subtype_info_from_csv()
    # Verify that result is a dictionary
    assert isinstance(result, dict)

    # Verify that the dictionary is not empty
    assert len(result) > 0

    # Verify that the keys and values are strings
    assert all(isinstance(k, str) for k in result)
    assert all(isinstance(v, str) for v in result.values())

    # Verify that the dictionary contains the expected data
    # by comparing with what we'd get directly from load_subtypes_from_csv
    subtypes = load_subtypes_from_csv()
    expected = {item["subformat"]: item["fullname"] for item in subtypes}
    assert result == expected


def test_is_xml_type():
    """Test that is_xml_type returns True for known XML types."""

    formatinfo = FormatInfo(
        detector="test_detector", mimetype="application/xml", subtype=SubType.TEIP5
    )
    assert formatinfo.is_xml_type()

    # Test with a non-XML type
    formatinfo = (
        FormatInfo(
            detector="test_detector", mimetype="application/json", subtype=SubType.JSON
        )
        is False
    )


def test_is_json_type():
    """Test that is_xml_type returns True for known XML types."""
    formatinfo = FormatInfo(
        detector="test_detector", mimetype="application/json", subtype=SubType.JSON
    )
    assert formatinfo.is_json_type()

    # Test with a non-JSON type
    formatinfo = FormatInfo(
        detector="test_detector", mimetype="application/xml", subtype=SubType.TEIP5
    )
    assert formatinfo.is_json_type() is False


def test_description():
    """Test that the description property returns the expected value."""
    formatinfo = FormatInfo(
        detector="test_detector", mimetype="application/xml", subtype=SubType.TEIP5
    )
    assert formatinfo.description == "XML TEI P5 document"

    formatinfo = FormatInfo(
        detector="test_detector", mimetype="application/json", subtype=SubType.JSON
    )
    assert formatinfo.description == "JSON document"

    # Tests with no subtype
    formatinfo = FormatInfo(detector="test_detector", mimetype="text/plain")
    assert formatinfo.description == "Text document"
    formatinfo = FormatInfo(detector="test_detector", mimetype="image/jpeg")
    assert formatinfo.description == "Image document"
    formatinfo = FormatInfo(detector="test_detector", mimetype="audio/mpeg")
    assert formatinfo.description == "Audio document"
    formatinfo = FormatInfo(detector="test_detector", mimetype="video/mp4")
    assert formatinfo.description == "Video document"
    formatinfo = FormatInfo(
        detector="test_detector", mimetype="application/octet-stream"
    )
    assert formatinfo.description == "Binary document"


def test_is_xml_type_true(monkeypatch):
    """Test is_xml_type returns True when subtype maintype is 'xml' and subformat matches."""

    class DummySubType:
        name = "TEIP5"

    # Mock _get_subtype_info to return xml maintype and matching subformat
    fi = FormatInfo(detector="det", mimetype="application/xml", subtype=DummySubType())
    monkeypatch.setattr(
        fi, "_get_subtype_info", lambda: {"subformat": "TEIP5", "maintype": "xml"}
    )
    assert fi.is_xml_type() is True


def test_is_xml_type_false_wrong_maintype(monkeypatch):
    """Test is_xml_type returns False when maintype is not 'xml'."""

    class DummySubType:
        name = "TEIP5"

    fi = FormatInfo(detector="det", mimetype="application/xml", subtype=DummySubType())
    monkeypatch.setattr(
        fi, "_get_subtype_info", lambda: {"subformat": "TEIP5", "maintype": "json"}
    )
    assert fi.is_xml_type() is False


def test_is_xml_type_false_wrong_subformat(monkeypatch):
    """Test is_xml_type returns False when subformat does not match subtype name."""

    class DummySubType:
        name = "OTHER"

    fi = FormatInfo(detector="det", mimetype="application/xml", subtype=DummySubType())
    monkeypatch.setattr(
        fi, "_get_subtype_info", lambda: {"subformat": "TEIP5", "maintype": "xml"}
    )
    assert fi.is_xml_type() is False


def test_is_xml_type_false_no_subtype_info(monkeypatch):
    """Test is_xml_type returns False when _get_subtype_info returns None."""

    class DummySubType:
        name = "TEIP5"

    fi = FormatInfo(detector="det", mimetype="application/xml", subtype=DummySubType())
    monkeypatch.setattr(fi, "_get_subtype_info", lambda: None)
    assert fi.is_xml_type() is False


def test_is_xml_type_false_no_subtype():
    """Test is_xml_type returns False when subtype is None."""
    fi = FormatInfo(detector="det", mimetype="application/xml", subtype=None)
    assert fi.is_xml_type() is False


def test_is_json_type_true(monkeypatch):
    """Test is_json_type returns True when subtype maintype is 'json' and subformat matches."""

    class DummySubType:
        name = "JSON"

    fi = FormatInfo(detector="det", mimetype="application/json", subtype=DummySubType())
    monkeypatch.setattr(
        fi, "_get_subtype_info", lambda: {"subformat": "JSON", "maintype": "json"}
    )
    assert fi.is_json_type() is True


def test_is_json_type_false_wrong_maintype(monkeypatch):
    """Test is_json_type returns False when maintype is not 'json'."""

    class DummySubType:
        name = "JSON"

    fi = FormatInfo(detector="det", mimetype="application/json", subtype=DummySubType())
    monkeypatch.setattr(
        fi, "_get_subtype_info", lambda: {"subformat": "JSON", "maintype": "xml"}
    )
    assert fi.is_json_type() is False


def test_is_json_type_false_wrong_subformat(monkeypatch):
    """Test is_json_type returns False when subformat does not match subtype name."""

    class DummySubType:
        name = "OTHER"

    fi = FormatInfo(detector="det", mimetype="application/json", subtype=DummySubType())
    monkeypatch.setattr(
        fi, "_get_subtype_info", lambda: {"subformat": "JSON", "maintype": "json"}
    )
    assert fi.is_json_type() is False


def test_is_json_type_false_no_subtype_info(monkeypatch):
    """Test is_json_type returns False when _get_subtype_info returns None."""

    class DummySubType:
        name = "JSON"

    fi = FormatInfo(detector="det", mimetype="application/json", subtype=DummySubType())
    monkeypatch.setattr(fi, "_get_subtype_info", lambda: None)
    assert fi.is_json_type() is False


def test_is_json_type_false_no_subtype():
    """Test is_json_type returns False when subtype is None."""
    fi = FormatInfo(detector="det", mimetype="application/json", subtype=None)
    assert fi.is_json_type() is False
