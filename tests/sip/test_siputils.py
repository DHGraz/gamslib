"""Unit tests for the gamspackaging.utils module."""

from pathlib import Path

import pytest

from gamslib.sip import ObjectDirectoryValidationError

from gamslib.sip.utils import (
    count_bytes,
    count_files,
    extract_id,
    find_object_folders,
    md5hash,
    sha512hash,
    validate_object_dir
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

def test_find_project_folders(datadir):
    """Test if the find_object_folders function return all folder containing a DC.xml."""
    project_folders = list(find_object_folders(datadir))
    assert len(project_folders) == len(["folder1", "folder2", "folder3", "folder3/folder_a"]) 

    assert datadir in project_folders
    assert datadir / "folder1" in project_folders
    assert datadir / "folder2" in project_folders
    assert datadir / "folder3" / "folder_a" in project_folders
    assert datadir / "folder3" not in project_folders


def test_extract_id():
    "Test the create_id function."
    assert extract_id(Path("/foo/bar/hsa.letter.1")) == "hsa.letter.1"
    assert extract_id(Path("hsa.letter.1")) == "hsa.letter.1"
    assert extract_id(Path("/foo/bar/hsa.letter.1/DC.xml")) == "DC.xml"
    assert extract_id(Path("/foo/bar/hsa.le-tt_er.1")) == "hsa.le-tt_er.1"

    
    assert extract_id(Path("/foo/bar/o%3Ahsa.letter.11745"), True) == "o%3Ahsa.letter.11745"
    assert extract_id("/foo/bar/o%3Ahsa.letter.11745", True) == "o%3Ahsa.letter.11745"

    # traiiling slash
    assert extract_id(Path("/foo/bar/hsa.letter.1/DC.xml/")) == "DC.xml"
    assert extract_id(Path("/foo/bar/hsa.letter.1/DC.xml/.")) == "DC.xml"

    # With remove_extension=True
    assert extract_id(Path("/foo/bar/hsa.letter.1/DC.xml"), True) == "DC"
    assert extract_id(Path("/foo/bar/hsa.letter.1/DC.X.Y.xml"), True) == "DC.X.Y"

    assert extract_id(Path("/foo/bar/o%3ahsa.letter.1/DC.xml/"), True) == "DC"
    assert extract_id(Path("/foo/bar/o%3ahsa.letter.1/DC.xml/"), True) == "DC"

    

    # Invalid PID
    with pytest.raises(ValueError):
        extract_id(Path("/foo/bar/hsa.letter.1/DC.xml/.."))

    with pytest.raises(ValueError):
        extract_id(Path("/foo/bar/hsa.lätters.1"))

    with pytest.raises(ValueError):
        extract_id(Path("/foo/bar/hsa.letter.1/D C.xml"))


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
        def __init__(self, path): pass
        def validate(self): raise Exception("CSV error")
    monkeypatch.setattr("gamslib.sip.utils.ObjectCSVManager", FailingCSVManager)
    obj_dir = tmp_path
    (obj_dir / "DC.xml").write_text("<dc></dc>")
    (obj_dir / "object.csv").write_text("id,name\n1,test")
    with pytest.raises(Exception, match="CSV error"):
        validate_object_dir(obj_dir)



