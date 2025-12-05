"""Tests for the objectdir module."""

import shutil
from pathlib import Path
from typing import Generator
from unittest.mock import patch

# from gamslib.sip import ObjectDirectoryValidationError
import pytest
from lxml import etree as ET

import gamslib
from gamslib.objectcsv import defaultvalues
from gamslib.objectcsv.objectcsvmanager import ObjectCSVManager
from gamslib.objectdir import (
    ObjectDirectoryValidationError,
    find_object_folders,
    validate_csv_files,
    validate_dc_file,
    validate_directory_structure,
    validate_object_dir,
)


def create_test_object_dir(
    tmp_path: Path,
    object_id: str,
    datastreams: list[tuple],
    main_resource: str | None = None,
) -> Path:
    """Create a dummy object directory with csv files and datatream files for testing.#

    Parameters
    ----------
    object_path : Path
        Object directory path relative to tmp_path
    datastreams : list[tuple[str, str, bytes]]
        List of tuples containing the datastream file name, content type, and content
    main_resource : str
        The filename of the main resource of the object

    Returns
    -------
    Path
        The path to the created object directory
    """
    object_path: Path = tmp_path / object_id.replace(":", "%3A")
    object_path.mkdir(parents=True, exist_ok=True)  
    mgr = ObjectCSVManager(object_path)
    obj_dict = {}
    for field in gamslib.objectcsv.objectdata.ObjectData.fieldnames():
        if field == "recid":
            obj_dict[field] = object_id
        elif field == "mainResource" and main_resource is not None:
            obj_dict[field] = main_resource
        else:
            obj_dict[field] = field
    mgr.set_object(gamslib.objectcsv.objectdata.ObjectData(**obj_dict))
    for i, (ds_file_name, content_type, content) in enumerate(datastreams, start=1):
        ds_dict = {}
        for field in gamslib.objectcsv.dsdata.DSData.fieldnames():
            if field == "dspath":
                ds_dict[field] = f"{object_id}/{ds_file_name}"
            elif field == "dsid":
                ds_dict[field] = ds_file_name
            elif field == "mimetype":
                ds_dict[field] = content_type
            else:
                ds_dict[field] = f"{field}_{i}"
            ds_path = object_path / ds_file_name
            ds_path.write_bytes(content)
            # ds_path.write_text(content, encoding="utf-8")
        mgr.add_datastream(gamslib.objectcsv.dsdata.DSData(**ds_dict))
    mgr.save()
    return object_path


@pytest.fixture(name="tei_content")
def tei_content_fixture(request: pytest.FixtureRequest) -> bytes:
    """Return full and valid TEI file as bytestring."""
    tei_path = (
        Path(request.fspath.dirname) / "objectcsv" / "data" / "obj1" / "xml_tei.xml"
    )
    return tei_path.read_text(encoding="utf-8").encode("utf-8")


@pytest.fixture(name="lido_content")
def lido_content_fixture(request: pytest.FixtureRequest) -> bytes:
    """Return full and valid LDIO file as bytestring."""
    lido_path = (
        Path(request.fspath.dirname) / "objectcsv" / "data" / "obj1" / "xml_lido.xml"
    )
    return lido_path.read_text(encoding="utf-8").encode("utf-8")


@pytest.fixture(name="pdf_content")
def pdf_content_fixture() -> bytes:
    """Return dummy PDF content as bytes."""
    return (
        "%PDF-1.4\n%âãÏÓ\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n".encode(
            "utf-8"
        )
    )


@pytest.fixture(name="png_content")
def png_content_fixture() -> bytes:
    """Return dummy PNG content as bytes."""
    return (
        "\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        "\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\nIDATx\xdac\xf8\x0f"
        "\x00\x01\x01\x01\x00\x18\xdd\x03\xe2\x00\x00\x00\x00IEND\xaeB`\x82"
    ).encode("latin1")


@pytest.fixture(name="dc_content")
def dc_content_fixture() -> bytes:
    """Return dummy DC XML content as bytes."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/ '
        'http://www.openarchives.org/OAI/2.0/oai_dc.xsd">\n'
        "  <dc:identifier>o:test.object.001</dc:identifier>\n"
        '  <dc:title xml:lang="en">Test Object</dc:title>\n'
        "  <dc:rights>Test Rights</dc:rights>\n"
        "  <dc:creator>Test Creator</dc:creator>\n"
        "  <dc:subject>Test Subject</dc:subject>\n"
        "  <dc:description>This is a test description.</dc:description>\n"
        "</oai_dc:dc>\n"
    ).encode("utf-8")


@pytest.fixture(name="object_dir")
def valid_object_dir_fixture(
    tmp_path: Path, pdf_content, png_content, dc_content
) -> Generator[Path, None, None]:
    """Create a valid object directory for testing."""
    dir_name = "o%3Atest.object.001"  
    datastreams = [
        ("foo.pdf", "application/pdf", pdf_content),
        ("DC.xml", "application/xml", dc_content),
        ("baz.png", "image/png", png_content),
    ]
    yield create_test_object_dir(tmp_path, dir_name, datastreams)


@pytest.fixture(name="tei_object_dir")
def tei_object_dir_fixture(
    tmp_path: Path, tei_content: bytes, dc_content: bytes, png_content: bytes
) -> Generator[Path, None, None]:
    """Create a minimal TEI Object dir and return path to it."""

    dir_name = "o%3Ahsa.letter.12137"  # "o:hsa.letter.12137"
    datastreams = [
        ("DC.xml", "application/xml", dc_content),
        ("tei.xml", "application/xml", tei_content),
        ("baz.png", "image/png", png_content),
    ]
    yield create_test_object_dir(tmp_path, dir_name, datastreams, "tei.xml")


@pytest.fixture(name="lido_object_dir")
def lido_object_dir_fixture(
    tmp_path: Path, lido_content: str, dc_content: bytes, png_content: bytes
) -> Generator[Path, None, None]:
    """Create a minimal TEI Object dir and return path to it."""
    dir_name = "o%3Ages.a-88"  # "o:ges.a-88"
    datastreams = [
        ("DC.xml", "application/xml", dc_content),
        ("lido.xml", "application/xml", lido_content),
        ("baz.png", "image/png", png_content),
    ]
    yield create_test_object_dir(tmp_path, dir_name, datastreams, "lido.xml")


# ------------- basic functionality tests ---------

def test_is_object_folder(tmp_path: Path, dc_content: bytes):
    """Test if the is_object_folder function correctly identifies object folders."""
    object_folder = tmp_path / "object1"
    object_folder.mkdir()
    (object_folder / "DC.xml").write_bytes(dc_content)

    non_object_folder = tmp_path / "not_an_object"
    non_object_folder.mkdir()

    assert gamslib.objectdir.is_object_folder(object_folder) is True
    assert gamslib.objectdir.is_object_folder(non_object_folder) is False

def test_find_object_folders(tmp_path: Path, dc_content: bytes):
    """Test if the find_object_folders function returns all folder containing a DC.xml."""
    object_folder_names = [
        "object1",
        "object2",
        "object3/subobject1",
        "object3/subobject2",
        "object3/objectx/subobject3",
    ]
    object_folders: list[ObjectCSVManager] = []
    for folder_name in object_folder_names:
        object_folders.append(
            create_test_object_dir(
                tmp_path, folder_name, [["DC.xml", "application/xml", dc_content]]
            )
        )

    found_folders = list(find_object_folders(tmp_path))
    assert len(found_folders) == len(object_folder_names)
    assert set(found_folders) == set(object_folders)


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
    """Test that validation fails when a datastream file referenced in
    datastreams.csv is missing."""
    # Remove one of the datastream files
    (object_dir / "foo.pdf").unlink()

    with pytest.raises(
        ObjectDirectoryValidationError,
        match=r"Datastream file 'foo.pdf'.*does not exist",
    ):
        validate_csv_files(object_dir)


def test_validate_csv_files_recid_mismatch(object_dir: Path):
    """Test that validation fails when directory name doesn't match recid
    in object.csv."""
    # rename object directory to mismatch recid
    new_dirname = object_dir.parent / "wrong_name"
    shutil.move(str(object_dir), str(new_dirname))

    with pytest.raises(
        ObjectDirectoryValidationError, match=r"Directory name.*does not match.*recid"
    ):
        validate_csv_files(new_dirname)


def test_validate_csv_files_csv_manager_validation_error(object_dir: Path):
    """Test that validation fails when ObjectCSVManager.validate() raises ValueError."""

    with patch.object(  # noqa: SIM117
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
    """Test that validation fails when datastreams.csv is missing a required field."""
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
    new_lines = [f"{line},unexpected" for line in lines]
    # Add an unexpected field to the header
    #lines[0] += ",unexpected_field"
    #for i, line in enumerate(lines[1:]):
    #    lines[i] = line + ",unexpected_value"
    ds_csv_path.write_text("\n".join(new_lines))
    content = ds_csv_path.read_text()
    with pytest.raises(
        ObjectDirectoryValidationError,
        match=r"datastreams.csv contains an unexpected field",
    ):
        validate_csv_files(object_dir)

# o%3Atest.object.001/DC.xml,DC.xml,title_2,description_2,application/xml,creator_2,rights_2,lang_2,tags_2,unexpected_value
# o%3Atest.object.001/baz.png,baz.png,title_3,description_3,image/png,creator_3,rights_3,lang_3,tags_3,unexpected_value
# o%3Atest.object.001/foo.pdf,foo.pdf,title_1,description_1,application/pdf,creator_1,rights_1,lang_1,tags_1,unexpected_value
# o%3Atest.object.001/foo.pdf,foo.pdf,title_1,description_1,application/pdf,creator_1,rights_1,lang_1,tags_1




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
    tei_path = tei_object_dir / "tei.xml"
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
        "tei:teiHeader/tei:fileDesc/tei:publicationStmt",
        namespaces=defaultvalues.NAMESPACES,
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
    root = ET.parse(lido_file).getroot()  # pylint: disable=c-extension-no-member
    id_node = root.find(
        'lido:lidoRecID[@lido:type="PID"]',
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
    assert result is None


def test_validate_main_resource_id_tei_file_no_raises(tei_object_dir):
    """Mke sure TEI file with matching object ID does not raise."""
    gamslib.objectdir.validate_main_resource_id(tei_object_dir)


# def test_check_if_object_dir_non_matching_object_id_tei_file_raises(tei_object_dir):
def test_validate_main_resource_id_tei_file_raises(tei_object_dir):
    """Test TEI file with non-matching object ID raises."""
    # change id in TEI file
    main_resource = tei_object_dir / "tei.xml"
    xml = main_resource.read_text(encoding="utf-8")
    xml = xml.replace("o:hsa.letter.12137", "o:hsa.letter.12138")
    main_resource.write_text(xml, encoding="utf-8")

    with pytest.raises(ValueError, match="does not match"):
        gamslib.objectdir.validate_main_resource_id(tei_object_dir)


def test_validate_main_resource_id_lido_file_no_raises(lido_object_dir):
    """Test LIDO file with matching object ID does not raise."""
    # if ids match should not raise
    gamslib.objectdir.validate_main_resource_id(lido_object_dir)


def test_validate_main_resource_id_lidofile_raises(lido_object_dir):
    """Asure LIDO file with non matching object ID raises."""
    main_resource = lido_object_dir / "lido.xml"
    xml = main_resource.read_text(encoding="utf-8")
    xml = xml.replace("o:ges.a-88", "o:ges.a-89")
    main_resource.write_text(xml, encoding="utf-8")

    with pytest.raises(ValueError, match="does not match"):
        gamslib.objectdir.validate_main_resource_id(lido_object_dir)


def test_validate_main_resource_id_non_tei_non_lido_file_does_not_check(object_dir):
    """Make sure that non-TEI/LIDO files are not checked."""

    object_csv = object_dir / "object.csv"
    lines = object_csv.read_text().splitlines()

    # change main resource to foo.pdf
    header = lines[0].split(",")
    main_res_index = header.index("mainResource")
    line1 = lines[1].split(",")
    line1[main_res_index] = "foo.pdf"
    lines = [",".join(header)]
    lines.append(",".join(line1))
    object_csv.write_text("\n".join(lines))
    # should not raise
    gamslib.objectdir.validate_main_resource_id(object_dir)


def test_validate_dc_file_valid(object_dir: Path):
    """Test that validate_dc_file does not raise for a valid DC.xml file."""
    # Should not raise
    validate_dc_file(object_dir)


def test_validate_dc_file_invalid(object_dir: Path):
    """Test that validate_dc_file raises ObjectDirectoryValidationError if DC.xml is invalid."""
    dc_file = object_dir / "DC.xml"
    # Corrupt the DC.xml file by remocing the identifier element
    xml = dc_file.read_text(encoding="utf-8")
    xml = xml.replace("<dc:identifier>o:test.object.001</dc:identifier>", "")
    dc_file.write_text("<invalid<xml>>")

    with pytest.raises(ObjectDirectoryValidationError, match=r"DC.xml file is invalid"):
        validate_dc_file(object_dir)


def test_validate_dc_file_identifier_with_colon(tmp_path: Path, dc_content: bytes):
    """Test validate_dc_file passes when directory name contains %3A and identifier uses colon."""
    dir_name = "o%3Atest.object.001"
    obj_dir = tmp_path / dir_name
    obj_dir.mkdir()
    (obj_dir / "DC.xml").write_bytes(dc_content)
    (obj_dir / "object.csv").write_text(
        "recid,mainResource\n" + dir_name.replace("%3A", ":") + ",foo.pdf"
    )
    (obj_dir / "datastreams.csv").write_text(
        "dspath,dsid,mimetype\nfoo.pdf,foo.pdf,application/pdf"
    )
    # Should not raise
    validate_dc_file(obj_dir)


def test_validate_dc_file_identifier_mismatch(object_dir: Path):
    """Test validate_dc_file raises if DC.xml identifier does not match directory name."""
    dc_file = object_dir / "DC.xml"
    # Change identifier in DC.xml to something else
    xml = dc_file.read_text(encoding="utf-8")
    xml = xml.replace(
        "<dc:identifier>o:test.object.001</dc:identifier>",
        "<dc:identifier>some.other.id</dc:identifier>",
    )
    dc_file.write_text(xml, encoding="utf-8")

    with pytest.raises(
        ObjectDirectoryValidationError, match=r"DC.xml identifier value does not match"
    ):
        validate_dc_file(object_dir)
