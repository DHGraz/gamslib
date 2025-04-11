import shutil
import pytest
from pathlib import Path

from gamslib.formatdetect.magikadetector import MagikaDetector

from conftest import get_testfiles


@pytest.fixture(name="detector")
def get_detector():
    """Return a FormatDetector instance for the format detector to be tested."""
    return MagikaDetector()


files_to_try = get_testfiles()
param_ids = [f.filepath.name for f in files_to_try]


@pytest.mark.parametrize("testfile", files_to_try, ids=param_ids)
def test_get_file_type(detector, testfile):
    """Test that the detector can guess the file type of a file."""
    # We have some known issues with the magika detector v 0.5
    if testfile.filepath.name == "image.jp2":
        pytest.skip("jp2 is not detected by magika")
    else:
        result = detector.guess_file_type(testfile.filepath)
        assert result.mimetype == testfile.mimetype, (
            f"{detector}: Expected '{testfile.mimetype}', got '{result.mimetype}' for file {testfile.filepath.name}"
        )
        assert result.subtype == testfile.subtype, (
            f"{detector}: Expected '{testfile.subtype}', got '{result.subtype}' for file {testfile.filepath.name}"
        )


@pytest.mark.parametrize("testfile", files_to_try, ids=param_ids)
def test_get_common_filetypes_without_extension(detector, tmp_path, testfile):
    """Test that the detector can guess the file type of a file with now extension."""
    # We have some known issues with the magika detector v 0.5
    if testfile.filepath.name == "image.jp2":
        pytest.skip("jp2 is not detected by magika")
    elif testfile.filepath.name == "iiif_manifest.json":
        pytest.skip("jsonld without extension is detected by magika as javascript")
    else:
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
    extension = ".txt"
    if testfile.filepath.suffix == ".txt":
        extension = ".jpg"
    file_to_test = tmp_path / ("foo" + extension)

    # We have some known issues with the magika detector v 0.5
    if testfile.filepath.name == "image.jp2":
        pytest.skip("jp2 is not detected by magika")
    elif testfile.filepath.name == "iiif_manifest.json":
        pytest.skip("jsonld with wrong extension is detected by magika as javascript")
    else:
        shutil.copy(testfile.filepath, file_to_test)
        result = detector.guess_file_type(file_to_test)
        assert result.mimetype == testfile.mimetype, (
            f"{detector}: Expected '{testfile.mimetype}', got '{result.mimetype}' for file {testfile.filepath.name}"
        )
        assert result.subtype == testfile.subtype, (
            f"{detector}: Expected '{testfile.subtype}', got '{result.subtype}' for file {testfile.filepath.name}"
        )


def test_guess_file_type_no_mimetype(detector, tmp_path, monkeypatch):
    file_to_test = tmp_path / "foo"
    monkeypatch.setattr(MagikaDetector, "_fix_result", lambda *args: ("", None))
    with pytest.warns(UserWarning):
        f_info = detector.guess_file_type(file_to_test)
        assert f_info.mimetype == "application/octet-stream"


def test_repr(detector):
    assert repr(detector) == "MagikaDetector"

def test_fix_result():
    """Test the _fix_result method."""
    # Test for javascript with .jsonld extension
    path = Path("/path/to/file.jsonld")
    label, mime_type = MagikaDetector._fix_result(path, "javascript", "application/javascript")
    assert label == "json"
    assert mime_type == "application/json"

    # Test for javascript with .json extension
    path = Path("/path/to/file.json")
    label, mime_type = MagikaDetector._fix_result(path, "javascript", "application/javascript")
    assert label == "json"
    assert mime_type == "application/json"

    # Test for javascript with other extension
    path = Path("/path/to/file.js")
    label, mime_type = MagikaDetector._fix_result(path, "javascript", "application/javascript")
    assert label == "javascript"
    assert mime_type == "application/javascript"

    # Test for text/xml conversion
    path = Path("/path/to/file.xml")
    label, mime_type = MagikaDetector._fix_result(path, "xml", "text/xml")
    assert label == "xml"
    assert mime_type == "application/xml"

    # Test for non-special case
    path = Path("/path/to/file.txt")
    label, mime_type = MagikaDetector._fix_result(path, "text", "text/plain")
    assert label == "text"
    assert mime_type == "text/plain"


