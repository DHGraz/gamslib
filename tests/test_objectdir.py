"""Tests for the objectdir module."""

import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

# from gamslib.sip import ObjectDirectoryValidationError
import pytest
from lxml import etree as ET

import gamslib
from gamslib.formatdetect import formatinfo
from gamslib.objectcsv import defaultvalues
from gamslib.objectcsv.objectcsvmanager import ObjectCSVManager
from gamslib.objectdir import (
    ObjectDirectoryValidationError,
    find_object_folders,
    validate_csv_files,
    validate_directory_structure,
    validate_object_dir,
)

# from gamslib.sip import ObjectDirectoryValidationError


def make_valid_object_dir(obj_path: Path, id_suffix: int) -> ObjectCSVManager:
    """Create a valid object.csv and a datastreams.csv file for testing."""
    # object_dir = obj_path / "object"
    (obj_path / "DC.xml").touch()

    mgr = ObjectCSVManager(obj_path)
    obj_dict = {}
    for field in gamslib.objectcsv.objectdata.ObjectData.fieldnames():
        if field == "recid":
            obj_dict[field] = f"{obj_path.name}"
        else:
            obj_dict[field] = f"{field}_{id_suffix}"
    csv_obj = gamslib.objectcsv.objectdata.ObjectData(**obj_dict)
    mgr.set_object(csv_obj)

    files = [
        ("foo.pdf", "application/pdf"),
        ("DC.xml", "application/xml"),
        ("baz.png", "image/png"),
    ]
    for fname, contentype in files:
        ds_dict = {}
        for field in gamslib.objectcsv.dsdata.DSData.fieldnames():
            if field == "dspath":
                ds_dict[field] = fname
                (obj_path / fname).touch()
            elif field == "dsid":
                ds_dict[field] = f"{fname}_id_{id_suffix}"
            elif field == "mimetype":
                ds_dict[field] = contentype
            else:
                ds_dict[field] = f"{field}_{id_suffix}"

        ds = gamslib.objectcsv.dsdata.DSData(**ds_dict)
        mgr.add_datastream(ds)
    mgr.save()
    return mgr


@pytest.fixture(name="object_dir")
def valid_object_dir_fixture(tmp_path: Path) -> Path:
    """Create a valid object directory for testing."""
    obj_dir = tmp_path / "valid_object"
    obj_dir.mkdir()
    return make_valid_object_dir(obj_dir, 1).obj_dir


@pytest.fixture(name="tei_content")
def tei_content_fixture(request: pytest.FixtureRequest) -> str:
    """Return full and valid TEI file as string."""
    tei_path = Path(request.fspath.dirname) / "objectcsv" / "data" / "obj1" / "xml_tei.xml"
    return tei_path.read_text(encoding="utf-8")

@pytest.fixture(name="lido_content")
def lido_content_fixture(request: pytest.FixtureRequest) -> str:
    """Return full and valid LDIO file as string."""
    lido_path = Path(request.fspath.dirname) / "objectcsv" / "data" / "obj1" / "xml_lido.xml"
    return lido_path.read_text(encoding="utf-8")

@pytest.fixture(name="tei_object_dir")
def tei_object_dir_fixture(tmp_path: Path, tei_content: str) -> Path:
    """Create a minimal TEI Object dir and return path to it."""
    obj_dir = tmp_path / "o%3Ahsa.letter.12137" # "o:hsa.letter.12137"
    obj_dir.mkdir()
    tei_path = obj_dir / "tei.xml"
    tei_path.write_text(tei_content, encoding="utf-8")
    #(obj_dir / "DC.xml").touch()
    yield obj_dir

@pytest.fixture(name="lido_object_dir")
def lido_object_dir_fixture(tmp_path: Path, lido_content: str) -> Path:
    """Create a minimal TEI Object dir and return path to it."""
    obj_dir = tmp_path / "o%3Ages.a-88" # "o:ges.a-88"
    obj_dir.mkdir()
    tei_path = obj_dir / "lido.xml"
    tei_path.write_text(lido_content, encoding="utf-8")
    (obj_dir / "DC.xml").touch()
    yield obj_dir

# ------------- basic functionality tests ---------
def test_find_object_folders(tmp_path: Path):
    """Test if the find_object_folders function returns all folder containing a DC.xml."""
    object_folder_names = [
        "object1",
        "object2",
        "object3/subobject1",
        "object3/subobject2",
    ]
    object_folders: list[ObjectCSVManager] = []
    for i, folder_name in enumerate(object_folder_names):
        folder_path = tmp_path / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)
        object_folders.append(make_valid_object_dir(folder_path, i))

    found_folders = list(find_object_folders(tmp_path))
    assert len(found_folders) == len(object_folder_names)
    assert set(found_folders) == {obj.obj_dir for obj in object_folders}


# ---- directory structure validation tests ----
def test_validate_directory_structure_valid(object_dir: Path):
    """Test the validate_object_dir function with a valid object directory."""
    validate_object_dir(object_dir)


def test_validate_directory_structure_not_a_directory(tmp_path):
    """Test that validation fails when path is not a directory."""
    non_dir = tmp_path / "not_a_dir.txt"
    non_dir.touch()

    with pytest.raises(
        ObjectDirectoryValidationError, match="does not exist or is not a directory"
    ):
        validate_directory_structure(non_dir)


def test_validate_directory_structure_object_dir_does_not_exist(tmp_path):
    """Test that validation fails when directory does not exist."""
    non_existent = tmp_path / "non_existent"

    with pytest.raises(
        ObjectDirectoryValidationError, match="does not exist or is not a directory"
    ):
        validate_directory_structure(non_existent)


def test_validate_directory_structure_missing_dc_xml(object_dir: Path):
    """Test that validation fails when DC.xml is missing."""
    (object_dir / "DC.xml").unlink()

    with pytest.raises(
        ObjectDirectoryValidationError, match=r"does not contain a DC.xml file"
    ):
        validate_directory_structure(object_dir)


def test_validate_directory_structure_missing_object_csv(object_dir: Path):
    """Test that validation fails when object.csv is missing."""
    (object_dir / "object.csv").unlink()

    with pytest.raises(
        ObjectDirectoryValidationError, match=r"does not contain an object\.csv file"
    ):
        validate_directory_structure(object_dir)


def test_validate_directory_structure_missing_ds_csv(object_dir: Path):
    """Test that validation fails when datastreams.csv is missing."""
    (object_dir / "datastreams.csv").unlink()

    with pytest.raises(
        ObjectDirectoryValidationError,
        match=r"does not contain a datastreams\.csv file",
    ):
        validate_directory_structure(object_dir)


# ---- validate_object_dir tests ----
def test_validate_object_dir_valid(object_dir: Path):
    """Test the validate_object_dir function with a valid object directory."""
    validate_object_dir(object_dir)


def test_validate_object_dir_missing_rec_id(object_dir: Path):
    """Test that validation fails when object.csv is missing the record id."""
    # Corrupt the object.csv file: remove the record id column
    lines = (object_dir / "object.csv").read_text().splitlines()
    header = lines[0].split(",")
    if "recid" in header:
        id_index = header.index("recid")
        new_header = header[:id_index] + header[id_index + 1 :]
        new_lines = [",".join(new_header)]
        for line in lines[1:]:
            parts = line.split(",")
            new_line = parts[:id_index] + parts[id_index + 1 :]
            new_lines.append(",".join(new_line))
        (object_dir / "object.csv").write_text("\n".join(new_lines))

    with pytest.raises(
        ObjectDirectoryValidationError, match="missing a required field 'recid'"
    ):
        validate_object_dir(object_dir)


def test_validate_object_dir_incomplete_object_csv(object_dir: Path):
    """Test that validation fails when object.csv is invalid."""
    # Corrupt the object.csv file: remove the header line
    lines = (object_dir / "object.csv").read_text().splitlines()
    (object_dir / "object.csv").write_text(lines[1])

    with pytest.raises(ObjectDirectoryValidationError, match="are missing or empty"):
        validate_object_dir(object_dir)


def test_validate_object_dir_missing_dir(tmp_path: Path):
    """Test the validate_object_dir function with a missing directory."""
    non_dir = tmp_path / "not_a_dir"
    with pytest.raises(ObjectDirectoryValidationError):
        validate_object_dir(non_dir)


def test_validate_csv_files_missing_datastream_file(object_dir: Path):
    """Test that validation fails when a datastream file referenced in datastreams.csv is missing."""
    # Remove one of the datastream files
    (object_dir / "foo.pdf").unlink()

    with pytest.raises(
        ObjectDirectoryValidationError,
        match=r"Datastream file 'foo\.pdf'.*does not exist",
    ):
        validate_csv_files(object_dir)


def test_validate_csv_files_recid_mismatch(object_dir: Path):
    """Test that validation fails when directory name doesn't match recid in object.csv."""
    # rename object directory to mismatch recid
    new_dirname = object_dir.parent / "wrong_name"
    shutil.move(str(object_dir), str(new_dirname))

    with pytest.raises(
        ObjectDirectoryValidationError, match=r"Directory name.*does not match.*recid"
    ):
        validate_csv_files(new_dirname)


def test_validate_csv_files_csv_manager_validation_error(object_dir: Path):
    """Test that validation fails when ObjectCSVManager.validate() raises ValueError."""

    with patch.object(
        ObjectCSVManager, "validate", side_effect=ValueError("Invalid data")
    ):
        with pytest.raises(ObjectDirectoryValidationError, match="Invalid data"):
            validate_csv_files(object_dir)


def test_validate_csv_files_missing_field_in_object_csv(tmp_path: Path):
    """Test that validation fails with proper error when object.csv is missing a required field."""
    obj_dir = tmp_path / "object"
    obj_dir.mkdir()
    (obj_dir / "DC.xml").touch()
    (obj_dir / "object.csv").write_text("id,name\n1,test")
    (obj_dir / "datastreams.csv").touch()

    with pytest.raises(
        ObjectDirectoryValidationError, match=r"object.csv contains an unexpected field"
    ):
        validate_csv_files(obj_dir)


def test_validate_csv_files_unexpected_field_in_object_csv(object_dir: Path):
    """Test that validation fails with proper error when object.csv has an unexpected field."""
    obj_csv_path = object_dir / "object.csv"
    lines = obj_csv_path.read_text().splitlines()
    # Add an unexpected field to the header
    lines[0] += ",unexpected_field"
    lines[1] += ",unexpected_value"
    obj_csv_path.write_text("\n".join(lines))
    with pytest.raises(
        ObjectDirectoryValidationError, match=r"object.csv contains an unexpected field"
    ):
        validate_csv_files(object_dir)


def test_validate_csv_files_missing_field_in_datastreams_csv(object_dir: Path):
    """Test that validation fails with proper error when datastreams.csv is missing a required field."""
    # Remove the 'title' field from the header
    with open(object_dir / "datastreams.csv", "r", encoding="utf-8") as f:
        lines = f.readlines()
    newlines = []
    header = lines[0].strip().split(",")
    # currently, dspath is the only required field
    idx = header.index("dspath")
    header.pop(idx)
    newlines.append(",".join(header))
    # Remove the corresponding data from each line
    for line in lines[1:]:
        data = line.strip().split(",")
        data.pop(idx)
        newlines.append(",".join(data))
    with open(object_dir / "datastreams.csv", "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(newlines))

    with pytest.raises(
        ObjectDirectoryValidationError,
        match=r"datastreams.csv is missing a required field",
    ):
        validate_csv_files(object_dir)


def test_validate_csv_files_unexpected_field_in_datastreams_csv(object_dir: Path):
    """Test that validation fails with proper error when datastreams.csv has an unexpected field."""
    ds_csv_path = object_dir / "datastreams.csv"
    lines = ds_csv_path.read_text().splitlines()
    # Add an unexpected field to the header
    lines[0] += ",unexpected_field"
    for i, line in enumerate(lines[1:]):
        lines[i] = line + ",unexpected_value"
    ds_csv_path.write_text("\n".join(lines))
    with pytest.raises(
        ObjectDirectoryValidationError,
        match=r"datastreams.csv contains an unexpected field",
    ):
        validate_csv_files(object_dir)


def test_validate_csv_files_type_error_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Test that validation handles unexpected TypeError messages."""
    obj_dir = tmp_path / "object"
    obj_dir.mkdir()
    (obj_dir / "DC.xml").touch()
    (obj_dir / "object.csv").touch()
    (obj_dir / "datastreams.csv").touch()

    def mock_init(*args, **kwargs):
        raise TypeError("Unexpected error message format")

    monkeypatch.setattr(ObjectCSVManager, "__init__", mock_init)

    with pytest.raises(
        ObjectDirectoryValidationError, match="Unexpected error message format"
    ):
        validate_csv_files(obj_dir)

def test_extract_id_from_tei_success(tei_object_dir):
    """Test successful extraction of ID from TEI file."""
    tei_path  = tei_object_dir / "tei.xml"
    result = gamslib.objectdir._extract_id_from_tei(tei_path)  # pylint: disable=protected-access
    assert result == "o:hsa.letter.12137"


def test_extract_id_from_tei_success_from_str(tei_object_dir):
    """Test successful extraction of ID from TEI file if path is given as str."""
    tei_file = tei_object_dir / "tei.xml"
    result = gamslib.objectdir._extract_id_from_tei(str(tei_file))  # pylint: disable=protected-access
    assert result == "o:hsa.letter.12137"


def test_extract_id_from_tei_id_node_missing(tei_object_dir):
    """Test extraction when ID node is not found in TEI file."""
    tei_file = tei_object_dir / "tei.xml" 
    tree = ET.parse(tei_file)  # pylint: disable=c-extension-no-member
    # remove the idno element
    root = tree.getroot()
    idno = root.find(
        "tei:teiHeader/tei:fileDesc/tei:publicationStmt/tei:idno",
        namespaces=defaultvalues.NAMESPACES,
    )
    root.find(
        "tei:teiHeader/tei:fileDesc/tei:publicationStmt", namespaces=defaultvalues.NAMESPACES
    ).remove(idno)
    tree.write(tei_file)
    result = gamslib.objectdir._extract_id_from_tei(tei_file)  # pylint: disable=protected-access
    assert result is None

def test_extract_id_from_tei_empty_text(tei_object_dir):
    """Test extraction when ID node exists but has empty text."""

    tei_file = tei_object_dir / "tei.xml" 
    xml = tei_file.read_text(encoding="utf-8")
    xml = xml.replace("o:hsa.letter.12137", "")
    tei_file.write_text(xml, encoding="utf-8")  
    result = gamslib.objectdir._extract_id_from_tei(tei_file)  # pylint: disable=protected-access
    assert result is None


def test_extract_id_from_lido_success(lido_object_dir):
    """Test successful extraction of ID from LIDO file."""
    lido_file = lido_object_dir / "lido.xml"
    result = gamslib.objectdir._extract_id_from_lido(lido_file)  # pylint: disable=protected-access
    assert result == "o:ges.a-88"


def test_extract_id_from_lido_success_with_string_path(lido_object_dir):
    """Test successful extraction of ID from LIDO file as string."""
    lido_file = lido_object_dir / "lido.xml"
    result = gamslib.objectdir._extract_id_from_lido(str(lido_file))  # pylint: disable=protected-access
    assert result == "o:ges.a-88"


def test_extract_id_from_lido_node_missing(lido_object_dir):
    """Test extraction when ID node is not found in LIDO file."""
    lido_file = lido_object_dir / "lido.xml"
    # remove the LidoRecID node from XML
    root = ET.parse(lido_file).getroot()
    id_node = root.find('lido:lidoRecID[@lido:type="PID"]',
        namespaces=defaultvalues.NAMESPACES,
    )
    root.remove(id_node)    
    ET.ElementTree(root).write(lido_file)  # pylint: disable=c-extension-no-member
    result = gamslib.objectdir._extract_id_from_lido(lido_file)  # pylint: disable=protected-access
    assert result is None


def test_extract_id_from_lido_empty_text(lido_object_dir):
    """Test extraction when ID node exists but has empty text."""
    lido_file = lido_object_dir / "lido.xml"
    xml = lido_file.read_text(encoding="utf-8")
    xml = xml.replace("o:ges.a-88", "")
    lido_file.write_text(xml, encoding="utf-8") 
    result = gamslib.objectdir._extract_id_from_lido(lido_file)  # pylint: disable=protected-access
    assert result == None


def test_check_if_object_dir_matches_object_id_no_main_resource(tei_object_dir):
    "If object dir does not define a main resource it should not raise."
    gamslib.objectdir.check_if_object_dir_matches_object_id(tei_object_dir, main_resource=None)


def test_check_if_object_dir_matches_object_id_tei_file_not_raises(tei_object_dir):
    """Test TEI file with matching object ID does not raise."""
    main_resource = tei_object_dir / "tei.xml" 
    gamslib.objectdir.check_if_object_dir_matches_object_id(tei_object_dir, main_resource)

def test_check_if_object_dir_non_matching_object_id_tei_file_raises(tei_object_dir):
    """Test TEI file with non-matching object ID does not raise."""
    main_resource = tei_object_dir / "tei.xml"
    xml = main_resource.read_text(encoding="utf-8")
    xml = xml.replace("o:hsa.letter.12137", "o:hsa.letter.12138")
    main_resource.write_text(xml, encoding="utf-8")
    
    with pytest.raises(ValueError, match="does not match"):
        gamslib.objectdir.check_if_object_dir_matches_object_id(tei_object_dir, main_resource)


def test_check_if_object_dir_matches_object_id_lidofile_not_raises(lido_object_dir):
    """Test LIDO file with matching object ID does not raise."""
    main_resource = lido_object_dir / "lido.xml"
    gamslib.objectdir.check_if_object_dir_matches_object_id(lido_object_dir, main_resource)
                                                
def test_check_if_object_dir_non_matching_object_id_lidofile_not_raises(lido_object_dir):
    """Test TEI file with matching object ID does not raise."""
    main_resource = lido_object_dir / "lido.xml"
    xml = main_resource.read_text(encoding="utf-8")
    xml = xml.replace("o:ges.a-88", "o:ges.a-89")
    main_resource.write_text(xml, encoding="utf-8") 
    with pytest.raises(ValueError, match="does not match"): 
        gamslib.objectdir.check_if_object_dir_matches_object_id(lido_object_dir, main_resource)

def test_non_tei_non_lido_file_does_not_check(monkeypatch):

    """Test that non-TEI/LIDO files are not checked."""
    object_dir = Path("/some/path/object789")
    main_resource = Path("/some/path/object789/main.txt")

    mock_format = MagicMock()
    mock_format.subtype = formatinfo.SubType.SVG
    monkeypatch.setattr("gamslib.formatdetect.detect_format", lambda x: mock_format)
    gamslib.objectdir.check_if_object_dir_matches_object_id(object_dir, main_resource)