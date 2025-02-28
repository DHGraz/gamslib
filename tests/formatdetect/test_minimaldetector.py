import shutil
import pytest
from pathlib import Path

from gamslib.formatdetect.minimaldetector import MinimalDetector
from gamslib.formatdetect.formatdetector import DEFAULT_TYPE
from conftest import get_testfiles


@pytest.fixture(name="detector")
def get_detector():
    """Return a FormatDetector instance for the format detector to be tested."""
    return MinimalDetector()


files_to_try = get_testfiles()
param_ids = [f.filepath.name for f in files_to_try]


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


# @pytest.mark.xfail(reason="Detecting files without extension is not supported by the mimetypes module.")
@pytest.mark.parametrize("testfile", files_to_try, ids=param_ids)
def test_get_common_filetypes_without_extension(detector, tmp_path, testfile):
    """Test that the detector can guess the file type of a file with now extension.

    As this does not work with the mimetypes module, we expect the default type and a warning.
    """
    shutil.copy(testfile.filepath, tmp_path / "foo")
    with pytest.warns(UserWarning):
        result = detector.guess_file_type(tmp_path / "foo")
        assert result.mimetype == DEFAULT_TYPE, (
            f"{detector}: Expected '{DEFAULT_TYPE}', got '{result.mimetype}' for file {testfile.filepath.name}"
        )
        assert result.subtype is None, (
            f"{detector}: Expected '"
            "', got '{result.subtype}' for file {testfile.filepath.name}"
        )


@pytest.mark.parametrize("testfile", files_to_try, ids=param_ids)
def test_get_common_filetypes_with_wrong_extension(detector, tmp_path, testfile):
    """Test that the detector can guess the file type of a file with a wrong extension."""
    extension = ".txt"
    expected_wrong_type = "text/plain"
    if testfile.filepath.suffix == ".txt":
        extension = ".jpg"
        expected_wrong_type = "image/jpeg"
    file_to_test = tmp_path / ("foo" + extension)

    # We have some known issues with the mimetype detector v 0.5
    if testfile.filepath.name == "image.jp2":
        pytest.skip("jp2 is not detected by magika")
    elif testfile.filepath.name == 'iiif_manifest.json':
        pytest.skip("jsonld with wrong extension is detected by magika as javascript")
    else:
        shutil.copy(testfile.filepath, file_to_test)
        result = detector.guess_file_type(file_to_test)
        assert result.mimetype == expected_wrong_type, (
            f"{detector}: Expected '{DEFAULT_TYPE}', got '{result.mimetype}' for file {testfile.filepath.name}"
        )
        assert result.subtype is None, (
            f"{detector}: Expected '"
            "', got '{result.subtype}' for file {testfile.filepath.name}"
        )