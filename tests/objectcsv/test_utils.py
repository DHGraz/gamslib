"""Tests for the objectcsv.utils module."""

from xml.etree import ElementTree as ET

import pytest

from gamslib.objectcsv import defaultvalues, utils


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
        result = list(utils.find_object_folders(tmp_path))
    assert len(result) == len(["]object1", "object3"])
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
        result = list(utils.find_object_folders(tmp_path))
    assert len(result) == len(["object1", "object3"])
    assert "object2" not in [p.name for p in result]
    assert tmp_path / "foo" / "object1" in result
    assert tmp_path / "bar" / "object3" in result


def test_extract_title_from_tei(datadir):
    "Ensure that the function returns the title"
    tei_file = datadir / "tei.xml"
    assert utils.extract_title_from_tei(tei_file) == "The TEI Title"

    # remove the title element and ensure that function return an empty string
    tei = ET.parse(tei_file)
    root = tei.getroot()
    title = root.find(
        "tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:title",
        namespaces=defaultvalues.NAMESPACES,
    )
    root.find(
        "tei:teiHeader/tei:fileDesc/tei:titleStmt", namespaces=defaultvalues.NAMESPACES
    ).remove(title)
    tei.write(tei_file)
    assert utils.extract_title_from_tei(tei_file) == ""


def test_extract_title_from_lido(datadir):
    "Ensure that the function returns the title"
    lido_file = datadir / "lido.xml"
    assert utils.extract_title_from_lido(lido_file) == "Bratspieß"

    # remove the titleSet element and ensure that function return an empty string
    tei = ET.parse(lido_file)
    root = tei.getroot()
    title = root.find(
        "lido:descriptiveMetadata/lido:objectIdentificationWrap/lido:titleWrap/lido:titleSet",
        namespaces=defaultvalues.NAMESPACES,
    )
    root.find(
        "lido:descriptiveMetadata/lido:objectIdentificationWrap/lido:titleWrap",
        namespaces=defaultvalues.NAMESPACES,
    ).remove(title)
    tei.write(lido_file)
    assert utils.extract_title_from_tei(lido_file) == ""


def test_split_entry():
    "Test the split_entry method."
    assert utils.split_entry("foo bar  ") == ["foo bar"]
    assert utils.split_entry("foo;bar") == ["foo", "bar"]
    assert utils.split_entry("foo; bar") == ["foo", "bar"]
    assert utils.split_entry("foo,bar") == ["foo,bar"]
    assert utils.split_entry("foo , bar") == ["foo , bar"]
    assert utils.split_entry("foo:foo, bar-bar;") == ["foo:foo, bar-bar"]
