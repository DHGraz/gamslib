"""Tests for the xmltypes module."""

import warnings

import pytest

from gamslib.formatdetect.formatinfo import SubType
from gamslib.formatdetect.xmltypes import (
    XMLSubFormats,
    detect_tei_version,
    get_format_info,
    guess_xml_subtype,
    is_xml_type,
)


def test_is_xml_type_known_mimetype():
    """Test that is_xml_type returns True for known XML types mime types."""
    assert is_xml_type("application/xml") is True
    assert is_xml_type("text/xml") is True
    assert is_xml_type("application/atom+xml") is True
    assert is_xml_type("application/rdf+xml") is True


def test_is_xml_type_unknown_mimetype():
    """Test that is_xml_type returns False for unknown  or none-XML types."""
    assert is_xml_type("application/json") is False
    assert is_xml_type("text/html") is False
    assert is_xml_type("image/png") is False
    assert is_xml_type("application/octet-stream") is False


def test_guess_xml_subtype_known_namespace(tmp_path):
    """Test that guess_xml_subtype returns the correct SubType for known namespaces."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root xmlns="http://www.w3.org/2005/Atom">
    </root>"""
    xml_file = tmp_path / "test_known_namespace.xml"
    xml_file.write_text(xml_content)

    assert guess_xml_subtype(xml_file) == SubType.ATOM


def test_guess_xml_subtype_unknown_namespace(tmp_path):
    """Test that guess_xml_subtype returns None for unknown namespaces."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root xmlns="http://unknown.namespace.com">
    </root>"""
    xml_file = tmp_path / "test_unknown_namespace.xml"
    xml_file.write_text(xml_content)

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        assert guess_xml_subtype(xml_file) is None
        assert len(w) == 1
        assert issubclass(w[-1].category, UserWarning)
        assert "XML format detection failed due to unknown namespace" in str(
            w[-1].message
        )


def test_guess_xml_subtype_no_namespace(tmp_path, shared_datadir):
    "A xml file without a namespace should return None (unless it's TEIP4)."
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root>
    </root>"""
    xml_file = tmp_path / "test_no_namespace.xml"
    xml_file.write_text(xml_content)

    assert guess_xml_subtype(xml_file) is None

    xml_file = shared_datadir / "xml_tei_p4.xml"
    assert guess_xml_subtype(xml_file) is SubType.TEIP4


def test_get_format_info_known_namespace(tmp_path):
    """Test that get_format_info returns the correct mimetype and subtype for known namespaces."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root xmlns="http://www.w3.org/2005/Atom">
    </root>"""
    xml_file = tmp_path / "test_known_namespace.xml"
    xml_file.write_text(xml_content)

    mimetype, subtype = get_format_info(xml_file, "application/xml")
    assert mimetype == "application/atom+xml"
    assert subtype == SubType.ATOM


def test_get_format_info_unknown_namespace(tmp_path, shared_datadir):
    """Test that get_format_info returns None for unknown namespaces (unless it's TEIP4)."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root xmlns="http://unknown.namespace.com">
    </root>"""
    xml_file = tmp_path / "test_unknown_namespace.xml"
    xml_file.write_text(xml_content)

    with pytest.warns(UserWarning):
        mimetype, subtype = get_format_info(xml_file, "application/xml")
        assert mimetype == "application/xml"
        assert subtype is None

    # TEI P4 has no namespace
    xml_file = shared_datadir / "xml_tei_p4.xml"
    mimetype, subtype = get_format_info(xml_file, "application/xml")
    assert mimetype == "application/tei+xml"
    assert subtype is SubType.TEIP4


def test_get_format_info_no_namespace(tmp_path):
    """A xml file without a namespace should return None."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root>
    </root>"""
    xml_file = tmp_path / "test_no_namespace.xml"
    xml_file.write_text(xml_content)

    mimetype, subtype = get_format_info(xml_file, "application/xml")
    assert mimetype == "application/xml"
    assert subtype is None


def test_detect_xml_version(shared_datadir):
    """Test that is_xml_type correctly detects XML files."""
    xml_file = shared_datadir / "xml_tei_p4.xml"
    assert detect_tei_version(xml_file) == SubType.TEIP4

    xml_file = shared_datadir / "xml_tei.xml"
    assert detect_tei_version(xml_file) == SubType.TEIP5

    # an now with namespace
    xml_file = shared_datadir / "xml_tei.xml"
    assert detect_tei_version(xml_file, "http://www.tei-c.org/ns/1.0") == SubType.TEIP5

    # a non-TEI file should return None
    xml_file = shared_datadir / "xml_lido.xml"
    assert detect_tei_version(xml_file) is None


def test_xmlsubformats_init():
    "Test creation of the XMLSubFormats object."
    sf = XMLSubFormats()
    assert len(sf.formats) > 0


def test_xmlsubformats_mimetypes():
    "Test if the mimetypes property returns a set of all MIME types defined in xml_subformats.csv."
    sf = XMLSubFormats()
    assert "application/xml" in sf.mimetypes
    assert "text/xml" in sf.mimetypes
    # the two above are added by default. Make sure there are more (from csv)
    assert len(sf.mimetypes) > 2


def test_get_mimetype_for_subtype():
    "Test get_mimetype_for_subtype"
    sf = XMLSubFormats()
    assert sf.get_mimetype_for_subtype(SubType.TEIP4) == "application/tei+xml"
    assert sf.get_mimetype_for_subtype(SubType.TEIP5) == "application/tei+xml"
    assert sf.get_mimetype_for_subtype(SubType.ATOM) == "application/atom+xml"
    assert sf.get_mimetype_for_subtype(SubType.RelaxNG) == "application/xml"

    # and now with default value: first we drop all formats to enforce default
    sf.formats = []
    assert (
        sf.get_mimetype_for_subtype(SubType.TEIP4, "application/xml")
        == "application/xml"
    )


def test_get_puid_for_format_type():
    "Test get_puid_for_format_type"
    sf = XMLSubFormats()
    # Test known format types
    assert sf.get_puid_for_format_type(SubType.TEIP4) == "fmt/1474"
    assert sf.get_puid_for_format_type(SubType.TEIP5) == "fmt/1476"

    # Test unknown format type returns default generic XML PUID
    assert sf.get_puid_for_format_type(SubType.ATOM) == "fmt/101"

    # Test with empty formats list enforces default
    sf.formats = []
    assert sf.get_puid_for_format_type(SubType.TEIP4) == "fmt/101"
