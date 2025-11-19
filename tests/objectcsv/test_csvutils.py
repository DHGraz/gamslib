"""Tests for the objectcsv.utils module."""

from pathlib import Path
from unittest.mock import MagicMock
from xml.etree import ElementTree as ET

import pytest

from gamslib.formatdetect import formatinfo
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


def test_extract_id_from_tei_success(shared_datadir):
    """Test successful extraction of ID from TEI file."""
    tei_file = shared_datadir / "obj1" / "xml_tei.xml"
    result = utils.extract_id_from_tei(tei_file)
    assert result == "o:hsa.letter.12137"


def test_extract_id_from_tei_success_from_str(shared_datadir):
    """Test successful extraction of ID from TEI file if path is given as str."""
    tei_file = shared_datadir / "obj1" / "xml_tei.xml"
    result = utils.extract_id_from_tei(str(tei_file))
    assert result == "o:hsa.letter.12137"


def test_extract_id_from_tei_id_not_found(monkeypatch):
    """Test extraction when ID node is not found in TEI file."""
    mock_tree = MagicMock()
    mock_tree.find.return_value = None
    monkeypatch.setattr("gamslib.objectcsv.utils.ET.parse", lambda x: mock_tree)

    tei_file = Path("/some/path/tei.xml")
    result = utils.extract_id_from_tei(tei_file)
    assert result == ""


def test_extract_id_from_tei_empty_text(monkeypatch):
    """Test extraction when ID node exists but has empty text."""
    mock_tree = MagicMock()
    mock_node = MagicMock()
    mock_node.text = ""
    mock_tree.find.return_value = mock_node
    monkeypatch.setattr("gamslib.objectcsv.utils.ET.parse", lambda x: mock_tree)

    tei_file = Path("/some/path/tei.xml")
    result = utils.extract_id_from_tei(tei_file)

    assert result == ""


def test_extract_id_from_lido_success(shared_datadir):
    """Test successful extraction of ID from LIDO file."""
    lido_file = shared_datadir / "obj1" / "xml_lido.xml"
    result = utils.extract_id_from_lido(lido_file)
    assert result == "o:ges.a-88"


def test_extract_id_from_lido_success_with_string_path(shared_datadir):
    """Test successful extraction of ID from LIDO file as string."""
    lido_file = shared_datadir / "obj1" / "xml_lido.xml"
    result = utils.extract_id_from_lido(str(lido_file))
    assert result == "o:ges.a-88"


def test_extract_id_from_lido_not_found(monkeypatch):
    """Test extraction when ID node is not found in LIDO file."""
    mock_tree = MagicMock()
    mock_tree.find.return_value = None
    monkeypatch.setattr("gamslib.objectcsv.utils.ET.parse", lambda x: mock_tree)

    lido_file = Path("/some/path/lido.xml")
    result = utils.extract_id_from_lido(lido_file)

    assert result == ""


def test_extract_id_from_lido_empty_text(monkeypatch):
    """Test extraction when ID node exists but has empty text."""
    mock_tree = MagicMock()
    mock_node = MagicMock()
    mock_node.text = ""
    mock_tree.find.return_value = mock_node
    monkeypatch.setattr("gamslib.objectcsv.utils.ET.parse", lambda x: mock_tree)

    lido_file = Path("/some/path/lido.xml")
    result = utils.extract_id_from_lido(lido_file)
    assert result == ""


def test_check_if_object_dir_matches_object_id_no_main_resource_not_raises(shared_datadir):
    """Test that function returns without error when main_resource is None."""
    object_dir = shared_datadir / "obj1"
    utils.check_if_object_dir_matches_object_id(object_dir, main_resource=None)


def test_check_if_object_dir_matches_object_id_tei_file_not_raises(shared_datadir, tmp_path):
    """Test TEI file with matching object ID does not raise."""
    main_resource = shared_datadir / "obj1" / "xml_tei.xml"
    object_dir = tmp_path / "o%3Ahsa.letter.12137"
    utils.check_if_object_dir_matches_object_id(object_dir, main_resource)

def test_check_if_object_dir_non_matching_object_id_tei_file_raises(shared_datadir, tmp_path):
    """Test TEI file with non-matching object ID does not raise."""
    main_resource = shared_datadir / "obj1" / "xml_tei.xml"
    object_dir = tmp_path / "foo"
    with pytest.raises(ValueError, match="does not match"):
        utils.check_if_object_dir_matches_object_id(object_dir, main_resource)


def test_check_if_object_dir_matches_object_id_lidofile_not_raises(shared_datadir, tmp_path):
    """Test LIDO file with matching object ID does not raise."""
    main_resource = shared_datadir / "obj1" / "xml_lido.xml"
    object_dir = tmp_path / "o%3Ages.a-88"
    utils.check_if_object_dir_matches_object_id(object_dir, main_resource)
                                                
def test_check_if_object_dir_non_matching_object_id_lidofile_not_raises(shared_datadir, tmp_path):
    """Test TEI file with matching object ID does not raise."""
    main_resource = shared_datadir / "obj1" / "xml_lido.xml"
    object_dir = tmp_path / "foo"
    with pytest.raises(ValueError, match="does not match"): 
        utils.check_if_object_dir_matches_object_id(object_dir, main_resource)




def test_non_tei_non_lido_file_does_not_check(monkeypatch):
    """Test that non-TEI/LIDO files are not checked."""
    object_dir = Path("/some/path/object789")
    main_resource = Path("/some/path/object789/main.txt")

    mock_format = MagicMock()
    mock_format.subtype = formatinfo.SubType.SVG
    monkeypatch.setattr("gamslib.formatdetect.detect_format", lambda x: mock_format)
    utils.check_if_object_dir_matches_object_id(object_dir, main_resource)
    
