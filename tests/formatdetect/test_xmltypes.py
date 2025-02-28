import pytest
from gamslib.formatdetect.xmltypes import is_xml_type
from pathlib import Path
from gamslib.formatdetect.xmltypes import guess_xml_subtype
import warnings
from gamslib.formatdetect.xmltypes import get_format_info
from gamslib.formatdetect.formatinfo import FormatInfo, SubType

def test_is_xml_type_known_mimetype():
    assert is_xml_type("application/xml") == True
    assert is_xml_type("text/xml") == True
    assert is_xml_type("application/atom+xml") == True
    assert is_xml_type("application/rdf+xml") == True

def test_is_xml_type_unknown_mimetype():
    assert is_xml_type("application/json") == False
    assert is_xml_type("text/html") == False
    assert is_xml_type("image/png") == False
    assert is_xml_type("application/octet-stream") == False

def test_guess_xml_subtype_known_namespace(tmp_path):
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root xmlns="http://www.w3.org/2005/Atom">
    </root>"""
    xml_file = tmp_path / "test_known_namespace.xml"
    xml_file.write_text(xml_content)

    assert guess_xml_subtype(xml_file) == SubType.ATOM

def test_guess_xml_subtype_unknown_namespace(tmp_path):
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
        assert "xml format detection failed because of unknown namespace" in str(w[-1].message)

def test_guess_xml_subtype_no_namespace(tmp_path):
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root>
    </root>"""
    xml_file = tmp_path / "test_no_namespace.xml"
    xml_file.write_text(xml_content)

    assert guess_xml_subtype(xml_file) is None
    
def test_get_format_info_known_namespace(tmp_path):
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root xmlns="http://www.w3.org/2005/Atom">
    </root>"""
    xml_file = tmp_path / "test_known_namespace.xml"
    xml_file.write_text(xml_content)

    mimetype, subtype = get_format_info(xml_file, "application/xml")
    assert mimetype == "application/atom+xml"
    assert subtype == SubType.ATOM

def test_get_format_info_unknown_namespace(tmp_path):
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root xmlns="http://unknown.namespace.com">
    </root>"""
    xml_file = tmp_path / "test_unknown_namespace.xml"
    xml_file.write_text(xml_content)

    with pytest.warns(UserWarning):
        mimetype, subtype = get_format_info(xml_file, "application/xml")
        assert mimetype == "application/xml"
        assert subtype is None

def test_get_format_info_no_namespace(tmp_path):
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root>
    </root>"""
    xml_file = tmp_path / "test_no_namespace.xml"
    xml_file.write_text(xml_content)

    mimetype, subtype = get_format_info(xml_file, "application/xml")
    assert mimetype == "application/xml"
    assert subtype is None



