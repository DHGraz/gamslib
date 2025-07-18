import pytest
from unittest.mock import patch, mock_open, MagicMock
import csv
import io
from pathlib import Path
from importlib import resources
from gamslib.formatdetect.formatinfo import FormatInfo, SubType, load_subtypes_from_csv
from gamslib.formatdetect.formatinfo import extract_subtype_info_from_csv, load_subtypes_from_csv
from gamslib.formatdetect.formatinfo import extract_subtype_info_from_csv


def test_load_subtypes_from_csv():
    """Test that load_subtypes_from_csv returns a list of dictionaries with the expected structure."""
    subtypes = load_subtypes_from_csv()
    assert isinstance(subtypes, list)
    assert len(subtypes) > 0
    assert all(isinstance(item, dict) for item in subtypes)
    assert all("subformat" in item for item in subtypes)
    assert all("full name" in item for item in subtypes)
    assert all("ds name" in item for item in subtypes)
    assert all("mimetype" in item for item in subtypes)
    assert all("maintype" in item for item in subtypes)


def test_load_subtypes_from_csv_whitespace_handling(tmp_path, monkeypatch):
    """Test that whitespace is properly stripped from keys and values."""
    
    def mock_find_subtype_csv_files():
        return [tmp_path / "xml_subformats.csv"]

    csv_content = " subformat , full name , ds name , mimetype \n SUBFORMAT , FULL NAME, DS NAME, MIMETYPE \n"
    (tmp_path / "xml_subformats.csv").write_text(csv_content, encoding="utf-8")
    monkeypatch.setattr("gamslib.formatdetect.formatinfo.find_subtype_csv_files", mock_find_subtype_csv_files)


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
    expected = {item["subformat"]: item["full name"] for item in subtypes}
    assert result == expected


def test_is_xml_type():
    """Test that is_xml_type returns True for known XML types."""

    formatinfo = FormatInfo(
        detector="test_detector",
        mimetype="application/xml",
        subtype=SubType.TEI)
    assert formatinfo.is_xml_type()

    # Test with a non-XML type
    formatinfo = FormatInfo(
        detector="test_detector",
        mimetype="application/json",
        subtype=SubType.JSON) is False

def test_is_json_type():
    """Test that is_xml_type returns True for known XML types."""
    formatinfo = FormatInfo(
        detector="test_detector",
        mimetype="application/json",
        subtype=SubType.JSON)
    assert formatinfo.is_json_type()

    # Test with a non-JSON type
    formatinfo = FormatInfo(
        detector="test_detector",
        mimetype="application/xml",
        subtype=SubType.TEI)
    assert formatinfo.is_json_type() is False

def test_description():
    """Test that the description property returns the expected value."""
    formatinfo = FormatInfo(
        detector="test_detector",
        mimetype="application/xml",
        subtype=SubType.TEI)
    assert formatinfo.description == "XML TEI document"

    formatinfo = FormatInfo(
        detector="test_detector",
        mimetype="application/json",
        subtype=SubType.JSON)
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
    formatinfo = FormatInfo(detector="test_detector", mimetype="application/octet-stream")
    assert formatinfo.description == "Binary document"
    