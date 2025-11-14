"""Unit tests for the gamspackaging.utils module."""

import json
from pathlib import Path
import shutil
from unittest.mock import MagicMock, patch

import pytest
import requests

from gamslib.sip import BagValidationError, ObjectDirectoryValidationError, utils

from gamslib.sip.utils import (
    GAMS_SIP_SCHEMA_URL,
    count_bytes,
    count_files,
    fetch_json_schema,
    find_object_folders,
    is_bag,
    md5hash,
    read_sip_schema_from_package,
    sha512hash,
    validate_object_dir,
)


class DummyCSVManager:
    """A dummy CSV manager for testing purposes.
    # This class is a placeholder to simulate the ObjectCSVManager in tests.
    # It should have the same interface as ObjectCSVManager.
    """

    def __init__(self, path):
        self.path = path

    def validate(self):
        pass


@pytest.fixture(name="bag_dir")
def fixture_bag_dir(tmp_path) -> Path:
    """Fixture that creates a minimal temporary bag directory."""
    bag_dir = tmp_path / "test_bag"
    bag_dir.mkdir()
    (bag_dir / "bagit.txt").touch()
    (bag_dir / "manifest-md5.txt").touch()
    (bag_dir / "manifest-sha512.txt").touch()
    (bag_dir / "data").mkdir()
    (bag_dir / "data" / "meta").mkdir()
    (bag_dir / "data" / "meta" / "sip.json").write_text(json.dumps({"version": "1.0"}))
    (bag_dir / "data" / "content").mkdir()
    (bag_dir / "data" / "content" / "DC.xml").touch()
    return bag_dir


@pytest.fixture(name="zipped_bag")
def fixture_zipped_bag(tmp_path, bag_dir):
    """Fixture that creates a minimal zipped bag."""
    zip_path = shutil.make_archive(str(tmp_path / "test_bag"), "zip", bag_dir)
    return Path(zip_path)


@pytest.fixture(
    name="incomplete_zipped_bag",
    params=[
        "bagit.txt",
        "manifest-md5.txt",
        "manifest-sha512.txt",
        "data/meta/sip.jsondata/content/DC.xml",
    ],
)
def incomplete_zipped_bag_fixture(request, tmp_path, bag_dir):
    """Return path to a zipped bag, based on bag_dir,
    where each time one required file is missing."""
    (bag_dir / request.param).unlink()
    zip_path = shutil.make_archive(str(tmp_path / "test_bag"), "zip", bag_dir)
    return Path(zip_path)


def test_find_project_folders(datadir):
    """Test if the find_object_folders function return all folder containing a DC.xml."""
    project_folders = list(find_object_folders(datadir))
    assert len(project_folders) == len(
        ["folder1", "folder2", "folder3", "folder3/folder_a"]
    )

    assert datadir in project_folders
    assert datadir / "folder1" in project_folders
    assert datadir / "folder2" in project_folders
    assert datadir / "folder3" / "folder_a" in project_folders
    assert datadir / "folder3" not in project_folders


# I removed the extract_id function as it is no longer needed.
# but the test might be usefull in the future.
# def test_extract_id():
#     "Test the create_id function."
#     assert extract_id(Path("/foo/bar/hsa.letter.1")) == "hsa.letter.1"
#     assert extract_id(Path("hsa.letter.1")) == "hsa.letter.1"
#     assert extract_id(Path("/foo/bar/hsa.letter.1/DC.xml")) == "DC.xml"
#     assert extract_id(Path("/foo/bar/hsa.le-tt_er.1")) == "hsa.le-tt_er.1"

#     assert (
#         extract_id(Path("/foo/bar/o%3Ahsa.letter.11745"), True)
#         == "o%3Ahsa.letter.11745"
#     )
#     assert extract_id("/foo/bar/o%3Ahsa.letter.11745", True) == "o%3Ahsa.letter.11745"

#     # traiiling slash
#     assert extract_id(Path("/foo/bar/hsa.letter.1/DC.xml/")) == "DC.xml"
#     assert extract_id(Path("/foo/bar/hsa.letter.1/DC.xml/.")) == "DC.xml"

#     # With remove_extension=True
#     assert extract_id(Path("/foo/bar/hsa.letter.1/DC.xml"), True) == "DC"
#     assert extract_id(Path("/foo/bar/hsa.letter.1/DC.X.Y.xml"), True) == "DC.X.Y"

#     assert extract_id(Path("/foo/bar/o%3ahsa.letter.1/DC.xml/"), True) == "DC"
#     assert extract_id(Path("/foo/bar/o%3ahsa.letter.1/DC.xml/"), True) == "DC"

#     # Invalid PID
#     with pytest.raises(ValueError):
#         extract_id(Path("/foo/bar/hsa.letter.1/DC.xml/.."))

#     with pytest.raises(ValueError):
#         extract_id(Path("/foo/bar/hsa.lätters.1"))

#     with pytest.raises(ValueError):
#         extract_id(Path("/foo/bar/hsa.letter.1/D C.xml"))


def test_md5hash(tmp_path):
    "Test the md5hash function."
    testfile = tmp_path / "foo.txt"
    testfile.write_text("foo", newline="")
    assert md5hash(testfile) == "acbd18db4cc2f85cedef654fccc4a4d8"

    testfile.write_text("foo\n", newline="")
    assert md5hash(testfile) == "d3b07384d113edec49eaa6238ad5ff00"

    testfile.write_bytes(b"foo")
    assert md5hash(testfile) == "acbd18db4cc2f85cedef654fccc4a4d8"


def test_sha512hash(tmp_path):
    "Test the sha512hash function."
    testfile = tmp_path / "foo.txt"
    testfile.write_text("foo", newline="")
    assert sha512hash(testfile) == (
        "f7fbba6e0636f890e56fbbf3283e524c6fa3204ae298382d624741d"
        "0dc6638326e282c41be5e4254d8820772c5518a2c5a8c0c7f7eda19"
        "594a7eb539453e1ed7"
    )
    testfile.write_text("foo\n", newline="")
    assert sha512hash(testfile) == (
        "0cf9180a764aba863a67b6d72f0918bc131c6772642cb2dce5a34f0a"
        "702f9470ddc2bf125c12198b1995c233c34b4afd346c54a2334c350a"
        "948a51b6e8b4e6b6"
    )
    testfile.write_bytes(b"foo")
    assert sha512hash(testfile) == (
        "f7fbba6e0636f890e56fbbf3283e524c6fa3204ae298382d624741d0"
        "dc6638326e282c41be5e4254d8820772c5518a2c5a8c0c7f7eda1959"
        "4a7eb539453e1ed7"
    )


def fix_linebreaks(root_path):
    """Fix linebreaks in textual content files.

    Checking out textual test content files with git under windows can
    modify the linebreaks in the files. This can
    lead to issues when comparing file sizes in the tests, as the linebreaks
    are different.

    As a hacky workaround, we normalize the linebreaks to before comparing sizes.
    """
    for path in root_path.rglob("*"):
        if path.is_file() and path.suffix in {".xml", ".txt"}:
            with open(path, "r", encoding="utf-8", newline="") as f:
                content = path.read_text()
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(content)


def test_count_bytes(datadir):
    "Test the count_bytes function."
    fix_linebreaks(datadir / "folder1")
    fix_linebreaks(datadir / "folder2")
    fix_linebreaks(datadir / "folder3")
    assert count_bytes(datadir / "folder1") == 3  # noqa: PLR2004
    assert count_bytes(datadir / "folder2") == 15  # noqa: PLR2004
    assert count_bytes(datadir / "folder3") == 48  # noqa: PLR2004


def test_count_files(datadir):
    "Test the count_files function."
    assert count_files(datadir / "folder1") == 1
    assert count_files(datadir / "folder2") == len(["DC.xml", "foo.txt"])
    assert count_files(datadir / "folder3") == len(["DC.xml", "foo.txt", "folder_a"])


def test_validate_object_dir_valid(monkeypatch, tmp_path):
    """Test the validate_object_dir function with a valid object directory."""
    # Patch ObjectCSVManager to DummyCSVManager
    monkeypatch.setattr("gamslib.sip.utils.ObjectCSVManager", DummyCSVManager)
    obj_dir = tmp_path
    (obj_dir / "DC.xml").write_text("<dc></dc>")
    (obj_dir / "object.csv").write_text("id,name\n1,test")
    # Should not raise
    validate_object_dir(obj_dir)


def test_validate_object_dir_missing_dir(tmp_path):
    """Test the validate_object_dir function with a missing directory."""
    non_dir = tmp_path / "not_a_dir"
    with pytest.raises(ObjectDirectoryValidationError):
        validate_object_dir(non_dir)


def test_validate_object_dir_missing_dcxml(tmp_path):
    """Test the validate_object_dir function with a missing DC.xml file."""
    obj_dir = tmp_path
    (obj_dir / "object.csv").write_text("id,name\n1,test")
    with pytest.raises(ObjectDirectoryValidationError):
        validate_object_dir(obj_dir)


def test_validate_object_dir_missing_object_csv(tmp_path):
    """Test the validate_object_dir function with a missing object.csv file."""
    obj_dir = tmp_path
    (obj_dir / "DC.xml").write_text("<dc></dc>")
    with pytest.raises(ObjectDirectoryValidationError):
        validate_object_dir(obj_dir)


def test_validate_object_dir_csv_manager_raises(monkeypatch, tmp_path):
    """Test the validate_object_dir function with a CSV manager that raises an error."""

    class FailingCSVManager:
        def __init__(self, path):
            pass

        def validate(self):
            raise Exception("CSV error")

    monkeypatch.setattr("gamslib.sip.utils.ObjectCSVManager", FailingCSVManager)
    obj_dir = tmp_path
    (obj_dir / "DC.xml").write_text("<dc></dc>")
    (obj_dir / "object.csv").write_text("id,name\n1,test")
    with pytest.raises(Exception, match="CSV error"):
        validate_object_dir(obj_dir)


def test_read_sip_schema_from_package_reads_json(monkeypatch, tmp_path):
    "Test reading the embedded JSON schema from the package."
    schema_dict = read_sip_schema_from_package()
    schema_file = Path(utils.__file__).parent / "resources" / "sip-schema-d1.json"
    schema_content = json.loads(schema_file.read_text(encoding="utf-8"))
    assert isinstance(schema_dict, dict)
    assert schema_dict == schema_content


def test_read_sip_schema_from_package_raises_if_missing(monkeypatch, tmp_path):
    "Test if validator detects missing sip.json file."
    missing_schema_file = tmp_path / "missing_sip.json"
    monkeypatch.setattr("gamslib.sip.utils.SCHEMA_PATH", missing_schema_file)

    # Act & Assert
    with pytest.raises(FileNotFoundError):
        read_sip_schema_from_package()


def test_read_sip_schema_from_package_raises_on_invalid_json(monkeypatch, tmp_path):
    "Test if validator detects sip.json file has invalid JSON content."
    # Arrange: create invalid JSON in sip.json
    resources_dir = tmp_path / "resources"
    resources_dir.mkdir()
    schema_path = resources_dir / "sip.json"
    schema_path.write_text("{invalid json}")
    monkeypatch.setattr(
        "gamslib.sip.utils.SCHEMA_PATH", schema_path
    )  # "gamslib.sip.utils.    schema_path", str(fake_module_file))

    with pytest.raises(json.JSONDecodeError):
        read_sip_schema_from_package()


def test_fetch_json_schema_embedded(monkeypatch):
    "Test fetching the embedded JSON schema from the package."
    # Patch read_sip_schema_from_package to return a known dict
    expected_schema = {"type": "object"}
    monkeypatch.setattr(
        "gamslib.sip.utils.read_sip_schema_from_package", lambda: expected_schema
    )
    result = fetch_json_schema(GAMS_SIP_SCHEMA_URL)
    assert result == expected_schema


@patch("gamslib.sip.utils.requests.get")
def test_fetch_json_schema_success(mock_get):
    "Test fetching a JSON schema successfully from a URL."
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.json.return_value = {"foo": "bar"}
    mock_get.return_value = mock_response
    url = "http://example.com/schema.json"
    result = fetch_json_schema(url)
    assert result == {"foo": "bar"}
    mock_get.assert_called_once_with(url, timeout=20)


@patch("gamslib.sip.utils.requests.get")
def test_fetch_json_schema_http_error(mock_get):
    "Test fetching a JSON schema that results in an HTTP error."
    mock_response = MagicMock()
    mock_response.ok = False
    mock_response.status_code = 404
    mock_get.return_value = mock_response
    url = "http://example.com/notfound.json"
    with pytest.raises(BagValidationError) as excinfo:
        fetch_json_schema(url)
    assert "HTTP status code 404" in str(excinfo.value)


@patch("gamslib.sip.utils.requests.get")
def test_fetch_json_schema_request_exception(mock_get):
    "Test fetching a JSON schema that raises a request exception."
    mock_get.side_effect = requests.RequestException("Connection error")
    url = "http://example.com/error.json"
    with pytest.raises(BagValidationError) as excinfo:
        fetch_json_schema(url)
    assert "Failed to fetch JSON schema" in str(excinfo.value)


@patch("gamslib.sip.utils.requests.get")
def test_fetch_json_schema_invalid_json(mock_get):
    "Test fetching a JSON schema that returns invalid JSON."
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.json.side_effect = requests.exceptions.InvalidJSONError(
        "Invalid JSON"
    )
    mock_get.return_value = mock_response
    url = "http://example.com/invalid.json"
    with pytest.raises(BagValidationError) as excinfo:
        fetch_json_schema(url)
    assert "not valid JSON" in str(excinfo.value)


@patch("gamslib.sip.utils.requests.get")
def test_fetch_json_schema_json_decode_error(mock_get):
    "Test fetching a JSON schema that returns invalid JSON (decode error)."
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.json.side_effect = requests.JSONDecodeError("Expecting value", "", 0)
    mock_get.return_value = mock_response
    url = "http://example.com/invalid.json"
    with pytest.raises(BagValidationError) as excinfo:
        fetch_json_schema(url)
    assert "not valid JSON" in str(excinfo.value)


@patch("gamslib.sip.utils.requests.get")
def test_fetch_json_schema_json_type_error(mock_get):
    "Test fetching a JSON schema that returns invalid JSON (type error)."
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.json.side_effect = TypeError("Type error")
    mock_get.return_value = mock_response
    url = "http://example.com/invalid.json"
    with pytest.raises(BagValidationError) as excinfo:
        fetch_json_schema(url)
    assert "not valid JSON" in str(excinfo.value)


def test_is_bag_with_valid_directory(bag_dir):
    """Test that is_bag returns True for a directory with bagit.txt."""
    assert is_bag(bag_dir)


def test_is_bag_with_incomplete_directory(bag_dir: Path):
    """Test that is_bag returns False for a directory without bagit.txt."""
    (bag_dir / "bagit.txt").unlink()
    with pytest.warns(UserWarning, match="missing"):
        assert is_bag(bag_dir) is False 


def test_is_bag_with_valid_zip(zipped_bag: Path):
    """Test that is_bag returns True for a zip file containing bagit.txt."""
    # Create a temporary directory with bagit.txt
    assert is_bag(zipped_bag)


@pytest.mark.parametrize(
    "incomplete_zipped_bag", ["bagit.txt", "manifest-md5.txt"], indirect=True
)
def test_is_bag_with_incomplete_zip(incomplete_zipped_bag):
    """Test that is_bag returns False if one of the required files is missing."""
    with pytest.warns(UserWarning, match="missing"):
        assert is_bag(incomplete_zipped_bag) is False


def test_is_bag_with_non_zip_file(tmp_path):
    """Test that is_bag returns False for a non-zip file."""
    txt_file = tmp_path / "file.txt"
    txt_file.touch()

    with pytest.warns(UserWarning, match="missing"):
        assert is_bag(txt_file) is False


def test_is_bag_with_nonexistent_path(tmp_path):
    """Test that is_bag returns False for a nonexistent path."""
    nonexistent = tmp_path / "does_not_exist"

    with pytest.warns(UserWarning, match="missing"):
        assert is_bag(nonexistent) is False


def test_is_bag_with_empty_directory(tmp_path):
    """Test that is_bag returns False for an empty directory."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    with pytest.warns(UserWarning, match="missing"):
        assert is_bag(empty_dir) is False


def test_is_bag_with_bagit_as_directory(tmp_path):
    """Test that is_bag returns False when bagit.txt is a directory, not a file."""
    bag_dir = tmp_path / "test_bag.zip"
    bag_dir.mkdir()

    with pytest.warns(UserWarning, match="missing"):
        assert is_bag(bag_dir) is False
