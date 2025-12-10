"""Tests for the magika detector."""
import re
import shutil
from pathlib import Path

import pytest
from conftest import get_testfiles

from gamslib.formatdetect.formatinfo import SubType
from gamslib.formatdetect.siegfrieddetector import SiegfriedDetector


@pytest.fixture(name="detector")
def get_detector():
    """Return a FormatDetector instance for the format detector to be tested."""
    return SiegfriedDetector()


files_to_try = get_testfiles()
param_ids = [f.filepath.name for f in files_to_try]


@pytest.mark.parametrize("testfile", files_to_try, ids=param_ids)
def test_get_file_type(detector, testfile):
    """Test that the detector can guess the file type of a file."""
    # # We have to fix some parts as Siegfried detects some things other than eg. Magika 
    # # (but still not wrongly)
    # if testfile.filepath.name in ("csv.csv", "markdown.md"):
    #     testfile.mimetype = "text/plain"
    # elif testfile.filepath.name in ("json_schema.json", "jsonl.json"):
    #     testfile.subtype = SubType.JSON
    # # Siegfried is confused by a plain text file with extension jpg. 
    # elif testfile.filepath.name == "text.txt": 
    #     testfile.mimetype = "application/octet-stream"
    # elif testfile.filepath.name == "xml_lido.xml":
    #     testfile.mimetype = "application/xml"
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
    if testfile.filepath.name == "text.txt": # this one (with wrong extension) is always detected wrong
        with pytest.warns(UserWarning):
            result = detector.guess_file_type(file_to_test)
    else:
        result = detector.guess_file_type(file_to_test)
    assert result.subtype == testfile.subtype, (
        f"{detector}: Expected '{testfile.subtype}', got '{result.subtype}' for file {testfile.filepath.name}"
    )


def test_guess_file_type_no_mimetype(detector, tmp_path, monkeypatch):
    file_to_test = tmp_path / "foo.strange_extension"
    file_to_test.touch()
    monkeypatch.setattr(SiegfriedDetector, "_fix_result", lambda *args: ("", None, ""))
    with pytest.warns(UserWarning):
        f_info = detector.guess_file_type(file_to_test)
        assert f_info.mimetype == "application/octet-stream"


def test_str(detector):
    assert re.match(r"^SiegfriedDetector \(Siegfried \d+\.\d+\.\d+", str(detector)) is not None

# def test_fix_result():
#     """Test the _fix_result method."""
#     # Test for javascript with .jsonld extension
#     path = Path("/path/to/file.jsonld")
#     label, mime_type = MagikaDetector._fix_result(path, "javascript", "application/javascript")
#     assert label == "json"
#     assert mime_type == "application/json"

#     # Test for javascript with .json extension
#     path = Path("/path/to/file.json")
#     label, mime_type = MagikaDetector._fix_result(path, "javascript", "application/javascript")
#     assert label == "json"
#     assert mime_type == "application/json"

#     # Test for javascript with other extension
#     path = Path("/path/to/file.js")
#     label, mime_type = MagikaDetector._fix_result(path, "javascript", "application/javascript")
#     assert label == "javascript"
#     assert mime_type == "application/javascript"

#     # Test for text/xml conversion
#     path = Path("/path/to/file.xml")
#     label, mime_type = MagikaDetector._fix_result(path, "xml", "text/xml")
#     assert label == "xml"
#     assert mime_type == "application/xml"

#     # Test for non-special case
#     path = Path("/path/to/file.txt")
#     label, mime_type = MagikaDetector._fix_result(path, "text", "text/plain")
#     assert label == "text"
#     assert mime_type == "text/plain"


