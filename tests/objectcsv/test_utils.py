"""Tests for the objectcsv.utils module."""

import pytest
from gamslib.objectcsv.utils import find_object_folders


def test_find_object_objects(tmp_path):
    "Check if all object directories are found."
    # Create some objects
    (tmp_path / "object1").mkdir()
    (tmp_path / "object2").mkdir()
    (tmp_path / "object3").mkdir()

    # Create DC.xml files - no DC file in object2
    (tmp_path / "object1" / "DC.xml").touch()
    (tmp_path / "object3" / "DC.xml").touch()

    # Create some files
    (tmp_path / "object2" / "file1.txt").touch()

    # Test the function
    with pytest.warns(UserWarning):
        result = list(find_object_folders(tmp_path))
    assert len(result) == 2
    assert "object2" not in [p.name for p in result]
    assert tmp_path / "object1" in result


def test_find_object_objects_nested_dirs(tmp_path):
    """Test the function with nested directories."""
    (tmp_path / "foo" / "object1").mkdir(parents=True)
    (tmp_path / "foo" / "object2").mkdir()
    (tmp_path / "bar" / "object3").mkdir(parents=True)

    # Create DC.xml files - no DC file in object2
    (tmp_path / "foo" / "object1" / "DC.xml").touch()
    (tmp_path / "bar" / "object3" / "DC.xml").touch()

    # Create some files
    (tmp_path / "foo" / "object2" / "file1.txt").touch()

    # Test the function
    with pytest.warns(UserWarning):
        result = list(find_object_folders(tmp_path))
    assert len(result) == 2
    assert "object2" not in [p.name for p in result]
    assert tmp_path / "foo" / "object1" in result
    assert tmp_path / "bar" / "object3" in result
