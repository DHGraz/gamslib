"""Tests for the magika detector."""

import copy
import re
import shutil
from pathlib import Path

import pytest
from conftest import get_testfiles
import pygfried
from gamslib.formatdetect.formatinfo import SubType
from gamslib.formatdetect import siegfrieddetector
from gamslib.formatdetect.siegfrieddetector import SiegfriedDetector



@pytest.fixture(name="detector")
def get_detector():
    """Return a FormatDetector instance for the format detector to be tested."""
    return SiegfriedDetector()


files_to_try = get_testfiles()
param_ids = [f.filepath.name for f in files_to_try]


@pytest.mark.filterwarnings("ignore::UserWarning")
@pytest.mark.parametrize("testfile", files_to_try, ids=param_ids)
def test_get_file_type(detector, testfile):
    """Test that the detector can guess the file type of a file."""
    result = detector.guess_file_type(testfile.filepath)
    assert result.mimetype == testfile.mimetype, (
        f"{detector}: Expected '{testfile.mimetype}', got '{result.mimetype}' for file {testfile.filepath.name}"
    )
    assert result.subtype == testfile.subtype, (
        f"{detector}: Expected '{testfile.subtype}', got '{result.subtype}' for file {testfile.filepath.name}"
    )
    assert result.pronom_id == testfile.pronom_id, (
        f"{detector}: Expected PRONOM ID '{testfile.pronom_id}', got "
        f"'{result.pronom_id}' for file {testfile.filepath.name}"
    )


@pytest.mark.filterwarnings("ignore::UserWarning")
@pytest.mark.parametrize("testfile", files_to_try, ids=param_ids)
def test_get_common_filetypes_without_extension(detector, tmp_path, testfile):
    """Test that the detector can guess the file type of a file with now extension."""
    # We have to fix some parts as Siegfried detects some things other than eg. Magika
    # (but still not wrongly)
    if testfile.filepath.name in ("csv.csv", "markdown.md"):
        testfile.mimetype = "text/plain"
    elif testfile.filepath.name in ("json_schema.json", "jsonl.json"):
        testfile.subtype = SubType.JSON
    shutil.copy(testfile.filepath, tmp_path / "foo")
    result = detector.guess_file_type(tmp_path / "foo")
    assert result.mimetype == testfile.mimetype, (
        f"{detector}: Expected '{testfile.mimetype}', got '{result.mimetype}' for file {testfile.filepath.name}"
    )
    assert result.subtype == testfile.subtype, (
        f"{detector}: Expected '{testfile.subtype}', got '{result.subtype}' for file {testfile.filepath.name}"
    )

@pytest.mark.filterwarnings("ignore::UserWarning")
@pytest.mark.parametrize("testfile", files_to_try, ids=param_ids)
def test_get_common_filetypes_with_wrong_extension(detector, tmp_path, testfile):
    """Test that the detector can guess the file type of a file with a wrong extension."""
    # TODO: As Siegfried is not really goot if the extension is wrong, we possible should warn/fail. But how can we detect a wrong extension?
    extension = ".txt"
    if testfile.filepath.suffix == ".txt":
        extension = ".jpg"
    file_to_test = tmp_path / ("foo" + extension)

    # We have to fix some parts as Siegfried detects some things other than eg. Magika
    # (but still not wrongly)
    if testfile.filepath.name in ("csv.csv", "markdown.md"):
        testfile.mimetype = "text/plain"
    elif testfile.filepath.name in ("json_schema.json", "jsonl.json"):
        testfile.subtype = SubType.JSON
    # Siegfried is confused by a plain text file with extension jpg.
    elif testfile.filepath.name == "text.txt":
        testfile.mimetype = "application/octet-stream"
        testfile.subtype = None
    elif testfile.filepath.name == "xml_lido.xml":
        testfile.mimetype = "application/xml"
    shutil.copy(testfile.filepath, file_to_test)
    if (
        testfile.filepath.name == "text.txt"
    ):  # this one (with wrong extension) is always detected wrong
        with pytest.warns(UserWarning):
            result = detector.guess_file_type(file_to_test)
    else:
        result = detector.guess_file_type(file_to_test)
    assert result.subtype == testfile.subtype, (
        f"{detector}: Expected '{testfile.subtype}', got '{result.subtype}' for file {testfile.filepath.name}"
    )




@pytest.fixture(name="multifile_test_data")
def multifile_test_data_fixture(shared_datadir):
    "Return a dict with a pygfried result as second file added."
    testdata = pygfried.identify(str(shared_datadir / "xml_tei_p4.xml"), True)
    second_file = copy.deepcopy(testdata["files"][0])
    second_file["name"] = "foo2.xml"
    testdata["files"].append(second_file)
    return testdata

def test_guess_file_type_multiple_files(detector, shared_datadir, multifile_test_data, monkeypatch):
    "Test the unlikely case that pygried detects multiple files."

    monkeypatch.setattr(pygfried, "identify", lambda *args, **kwargs: multifile_test_data)
    testfile = shared_datadir / "xml_tei_p4.xml"
    with pytest.warns(UserWarning):
        f_info = detector.guess_file_type(testfile)
    assert f_info.mimetype == "application/octet-stream"

@pytest.fixture(name="empty_test_data")
def empty_test_data_fixture(shared_datadir):
    "Return a dict with a pygfried result without files."
    testdata = pygfried.identify(str(shared_datadir / "xml_tei_p4.xml"), True)
    testdata["files"] = []
    return testdata

def test_guess_file_type_no_files(detector, shared_datadir, empty_test_data, monkeypatch):
    "Test the very unlikely case that pygried detects no files."

    monkeypatch.setattr(pygfried, "identify", lambda *args, **kwargs: empty_test_data)
    testfile = shared_datadir / "xml_tei_p4.xml"
    with pytest.warns(UserWarning):
        f_info = detector.guess_file_type(testfile)
    assert f_info.mimetype == "application/octet-stream"


@pytest.fixture(name="no_mime_type_test_data")
def no_mime_type_test_data_fixture(shared_datadir):
    "Return a dict with a pygfried result without mimetype."
    testdata = pygfried.identify(str(shared_datadir / "xml_tei_p4.xml"), True)
    testdata["files"][0]["mimeType"] = None
    testdata["files"][0]["matches"][0]["mime"] = None
    return testdata

def test_guess_file_type_no_mimetype(detector, shared_datadir, no_mime_type_test_data, monkeypatch):
    "Test the unlikely case that pygried detects no mimetype."
    monkeypatch.setattr(pygfried, "identify", lambda *args, **kwargs: no_mime_type_test_data)
    testfile = shared_datadir / "xml_tei_p4.xml"
    with pytest.warns(UserWarning):
        f_info = detector.guess_file_type(testfile)
    assert f_info.mimetype == "application/octet-stream"

def _test_guess_file_type_no_mimetype(detector, tmp_path, monkeypatch):
    file_to_test = tmp_path / "foo.strange_extension"
    file_to_test.touch()
    monkeypatch.setattr(SiegfriedDetector, "_fix_result", lambda *args: ("", None, ""))
    with pytest.warns(UserWarning):
        f_info = detector.guess_file_type(file_to_test)
        assert f_info.mimetype == "application/octet-stream"

@pytest.fixture(name="undefined_mime_types_test_data")
def undefined_mime_types_test_data_fixture(shared_datadir):
    "Return a dict with a pygfried result without mimetype."
    testdata = pygfried.identify(str(shared_datadir / "xml_tei_p4.xml"), True)
    testdata["files"][0]["mimeType"] = "application/undefined"
    testdata["files"][0]["matches"][0]["mime"] = "application/undefined"
    return testdata

def test_guess_file_type_undefined_mimetype(detector, shared_datadir, undefined_mime_types_test_data, monkeypatch):
    "Test the unlikely case that pygried detects no mimetype."
    monkeypatch.setattr(pygfried, "identify", lambda *args, **kwargs: undefined_mime_types_test_data)
    testfile = shared_datadir / "xml_tei_p4.xml"
    with pytest.warns(UserWarning):
        f_info = detector.guess_file_type(testfile)
    assert f_info.mimetype == "application/octet-stream"


def test_str(detector):
    assert (
        re.match(r"^SiegfriedDetector \(Siegfried \d+\.\d+\.\d+", str(detector))
        is not None
    )


def test_looks_like_xml(detector, shared_datadir):
    "Test the _looks_like_xml method."
    assert detector._looks_like_xml(shared_datadir / "xml_lido.xml")  # pylint: disable=protected-access
    assert not detector._looks_like_xml(shared_datadir / "text.txt")  # pylint: disable=protected-access


def test_extract_pronom_info_with_pronom_match(detector):
    """Test _extract_pronom_info returns pronom match when present."""
    matches = [
        {"ns": "other", "id": "fmt/1"},
        {"ns": "pronom", "id": "fmt/817", "mime": "application/json"},
    ]
    result = detector._extract_pronom_info(matches)  # pylint: disable=protected-access
    assert result == {"ns": "pronom", "id": "fmt/817", "mime": "application/json"}


def test_extract_pronom_info_no_pronom_match(detector):
    """Test _extract_pronom_info returns None when no pronom match."""
    matches = [
        {"ns": "other", "id": "fmt/1"},
        {"ns": "different", "id": "fmt/2"},
    ]
    result = detector._extract_pronom_info(matches)  # pylint: disable=protected-access
    assert result is None


def test_extract_pronom_info_empty_list(detector):
    """Test _extract_pronom_info returns None for empty matches list."""
    result = detector._extract_pronom_info([])  # pylint: disable=protected-access
    assert result is None


def test_extract_pronom_info_first_pronom_match(detector):
    """Test _extract_pronom_info returns first pronom match."""
    matches = [
        {"ns": "pronom", "id": "fmt/100"},
        {"ns": "pronom", "id": "fmt/200"},
    ]
    result = detector._extract_pronom_info(matches)  # pylint: disable=protected-access
    assert result == {"ns": "pronom", "id": "fmt/100"}


def test_fix_xml_info_xhtml(detector, tmp_path, monkeypatch):
    """Test _fix_xml_info returns correct PRONOM ID for XHTML."""
    file_to_test = tmp_path / "test.xml"
    file_to_test.touch()
    monkeypatch.setattr(
        "gamslib.formatdetect.siegfrieddetector.xmltypes.get_format_info",
        lambda *args: ("application/xml", SubType.XHTML),
    )
    result = detector._fix_xml_info(file_to_test)  # pylint: disable=protected-access
    assert result == ("application/xml", SubType.XHTML, "fmt/103")

def test_fix_xml_info_xhtml_rdfa(detector, tmp_path, monkeypatch):
    """Test _fix_xml_info returns correct PRONOM ID for XHTML with RDFa."""
    file_to_test = tmp_path / "test.xml"
    file_to_test.touch()
    monkeypatch.setattr(
        "gamslib.formatdetect.siegfrieddetector.xmltypes.get_format_info",
        lambda *args: ("application/xml", SubType.XHTML_RDFa),
    )
    result = detector._fix_xml_info(file_to_test)  # pylint: disable=protected-access
    assert result == ("application/xml", SubType.XHTML_RDFa, "fmt/103")

def test_fix_xml_info_gml(detector, tmp_path, monkeypatch):
    """Test _fix_xml_info returns correct PRONOM ID for GML."""
    file_to_test = tmp_path / "test.xml"
    file_to_test.touch()
    monkeypatch.setattr(
        "gamslib.formatdetect.siegfrieddetector.xmltypes.get_format_info",
        lambda *args: ("application/xml", SubType.GML),
    )
    result = detector._fix_xml_info(file_to_test)  # pylint: disable=protected-access
    assert result == ("application/xml", SubType.GML, "fmt/1047")

def test_fix_xml_info_kml(detector, tmp_path, monkeypatch):
    """Test _fix_xml_info returns correct PRONOM ID for KML."""
    file_to_test = tmp_path / "test.xml"
    file_to_test.touch()
    monkeypatch.setattr(
        "gamslib.formatdetect.siegfrieddetector.xmltypes.get_format_info",
        lambda *args: ("application/xml", SubType.KML),
    )
    result = detector._fix_xml_info(file_to_test)  # pylint: disable=protected-access
    assert result == ("application/xml", SubType.KML, "fmt/244")

def test_fix_xml_info_svg(detector, tmp_path, monkeypatch):
    """Test _fix_xml_info returns correct PRONOM ID for SVG."""
    file_to_test = tmp_path / "test.xml"
    file_to_test.touch()
    monkeypatch.setattr(
        "gamslib.formatdetect.siegfrieddetector.xmltypes.get_format_info",
        lambda *args: ("application/xml", SubType.SVG),
    )
    result = detector._fix_xml_info(file_to_test)  # pylint: disable=protected-access
    assert result == ("application/xml", SubType.SVG, "fmt/92")

def test_fix_xml_info_generic_xml(detector, tmp_path, monkeypatch):
    """Test _fix_xml_info returns default PRONOM ID for generic XML."""
    file_to_test = tmp_path / "test.xml"
    file_to_test.touch()
    monkeypatch.setattr(
        "gamslib.formatdetect.siegfrieddetector.xmltypes.get_format_info",
        lambda *args: ("application/xml", SubType.XML),
    )
    result = detector._fix_xml_info(file_to_test)  # pylint: disable=protected-access
    assert result == ("application/xml", SubType.XML, "fmt/101")

def test_fix_xml_info_none_detected_format(detector, tmp_path, monkeypatch):
    """Test _fix_xml_info returns None when detection fails."""
    file_to_test = tmp_path / "test.xml"
    file_to_test.touch()
    monkeypatch.setattr(
        "gamslib.formatdetect.siegfrieddetector.xmltypes.get_format_info",
        lambda *args: None,
    )
    result = detector._fix_xml_info(file_to_test)  # pylint: disable=protected-access
    assert result is None

def test_fix_xml_info_exception_handling(detector, tmp_path, monkeypatch):
    """Test _fix_xml_info returns None on exception."""
    file_to_test = tmp_path / "test.xml"
    file_to_test.touch()
    monkeypatch.setattr(
        "gamslib.formatdetect.siegfrieddetector.xmltypes.get_format_info",
        lambda *args: (_ for _ in ()).throw(ValueError("test error")),
    )
    result = detector._fix_xml_info(file_to_test)  # pylint: disable=protected-access
    assert result is None

def test_fix_result_jsonld_subtype(detector, tmp_path):
    """Test _fix_result returns correct format for JSONLD subtype."""
    file_to_test = tmp_path / "test.json"
    file_to_test.touch()
    result = detector._fix_result(file_to_test, "application/json", SubType.JSONLD)  # pylint: disable=protected-access
    assert result == ("application/ld+json", SubType.JSONLD, "fmt/880")


def test_fix_result_jsonld_extension(detector, tmp_path):
    """Test _fix_result returns correct format for .jsonld extension."""
    file_to_test = tmp_path / "test.jsonld"
    file_to_test.touch()
    result = detector._fix_result(file_to_test, "application/json", SubType.JSON)  # pylint: disable=protected-access
    assert result == ("application/ld+json", SubType.JSONLD, "fmt/880")


def test_fix_result_xz_file(detector, tmp_path):
    """Test _fix_result returns correct format for XZ files."""
    file_to_test = tmp_path / "test.xz"
    file_to_test.touch()
    result = detector._fix_result(file_to_test, "", SubType.JSON, "fmt/1098")  # pylint: disable=protected-access
    assert result == ("application/x-xz", SubType.JSON, "fmt/1098")


def test_fix_result_text_plain_json_detected(detector, tmp_path, monkeypatch):
    """Test _fix_result detects JSON from text/plain."""
    file_to_test = tmp_path / "test.txt"
    file_to_test.touch()
    monkeypatch.setattr(
        "gamslib.formatdetect.siegfrieddetector.SiegfriedDetector._fix_json_info",
        lambda *args: ("application/json", SubType.JSON, "fmt/817"),
    )
    result = detector._fix_result(file_to_test, "text/plain", None, "x-fmt/111")  # pylint: disable=protected-access
    assert result == ("application/json", SubType.JSON, "fmt/817")


def test_fix_result_text_plain_xml_detected(detector, tmp_path, monkeypatch):
    """Test _fix_result detects XML from text/plain when JSON detection fails."""
    file_to_test = tmp_path / "test.txt"
    file_to_test.touch()
    monkeypatch.setattr(
        "gamslib.formatdetect.siegfrieddetector.SiegfriedDetector._fix_json_info",
        lambda *args: None,
    )
    monkeypatch.setattr(
        "gamslib.formatdetect.siegfrieddetector.SiegfriedDetector._fix_xml_info",
        lambda *args: ("application/xml", SubType.XML, "fmt/101"),
    )
    result = detector._fix_result(file_to_test, "text/plain", None, "x-fmt/111")  # pylint: disable=protected-access
    assert result == ("application/xml", SubType.XML, "fmt/101")


def test_fix_result_unknown_with_xml_warning(detector, tmp_path, monkeypatch):
    """Test _fix_result handles UNKNOWN pronom_id with XML warning."""
    file_to_test = tmp_path / "test.xml"
    file_to_test.touch()
    monkeypatch.setattr(
        "gamslib.formatdetect.siegfrieddetector.xmltypes.get_format_info",
        lambda *args: ("application/xml", SubType.XML),
    )
    result = detector._fix_result(file_to_test, "text/plain", None, "UNKNOWN", "fmt/101")  # pylint: disable=protected-access
    assert result == ("application/xml", SubType.XML, "fmt/101")


def test_fix_result_unknown_with_json_warning(detector, tmp_path, monkeypatch):
    """Test _fix_result handles UNKNOWN pronom_id with JSON warning."""
    file_to_test = tmp_path / "test.json"
    file_to_test.touch()
    monkeypatch.setattr(
        "gamslib.formatdetect.siegfrieddetector.jsontypes.get_format_info",
        lambda *args: ("application/json", SubType.JSON),
    )
    result = detector._fix_result(file_to_test, "text/plain", None, "UNKNOWN", "fmt/817")  # pylint: disable=protected-access
    assert result == ("application/json", SubType.JSON, "UNKNOWN")


def test_fix_result_no_modification(detector, tmp_path):
    """Test _fix_result returns original values when no conditions match."""
    file_to_test = tmp_path / "test.pdf"
    file_to_test.touch()
    result = detector._fix_result(file_to_test, "application/pdf", SubType.ODF, "fmt/20")  # pylint: disable=protected-access
    assert result == ("application/pdf", SubType.ODF, "fmt/20")

def test_fix_json_info_with_exception(detector, tmp_path, monkeypatch):
    """Test _fix_json_info if detec_format raises an exception."""
    file_to_test = tmp_path / "test.json"
    file_to_test.touch()
    monkeypatch.setattr(
        "gamslib.formatdetect.siegfrieddetector.jsontypes.get_format_info",
        lambda *args: (_ for _ in ()).throw(ValueError("test error")),
    )
    result = detector._fix_json_info(file_to_test)  # pylint: disable=protected-access
    assert result is None


def test_fix_json_info_with_none(detector, tmp_path, monkeypatch):
    """Test _fix_json_info if detec_format returns None."""
    file_to_test = tmp_path / "test.json"
    file_to_test.touch()
    monkeypatch.setattr(
        "gamslib.formatdetect.siegfrieddetector.jsontypes.get_format_info",
        lambda *args: None),
    
    result = detector._fix_json_info(file_to_test)  # pylint: disable=protected-access
    assert result is None    