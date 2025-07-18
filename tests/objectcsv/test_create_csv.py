"""Test the objectcsv.create_csv module."""

# pylint: disable=W0212 # access to ._data
import csv
from dataclasses import fields
from pathlib import Path
import shutil

import pytest
from pytest import fixture

from gamslib.objectcsv import defaultvalues
from gamslib.objectcsv.create_csv import (
    create_csv,
    create_csv_files,
    detect_languages,
    extract_dsid,
    get_rights,
    is_datastream_file,
    update_csv,
)
from gamslib.objectcsv.dsdata import DSData
from gamslib.objectcsv.dublincore import DublinCore
from gamslib.objectcsv.objectdata import ObjectData
from gamslib.projectconfiguration.configuration import Configuration


@fixture(name="test_config")
def config_fixture(datadir):
    "Return a conguration object."
    return Configuration.from_toml(datadir / "project.toml")


@fixture(name="test_dc")
def dc_fixture(datadir):
    "Return a DublinCore object."
    return DublinCore(datadir / "objects" / "obj1" / "DC.xml")


# utility functions
def read_csv_file(file: Path):
    """Return the contents of a csv file as a list of dicts."""
    with open(file, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def read_csv_file_to_dict(file: Path, key_field: str):
    """Return the contents of a csv file as a dict of dicts."""
    data = {}
    for row in read_csv_file(file):
        data[row[key_field]] = row
    return data


def write_csv_file(file: Path, data: list[dict[str, str]]):
    """Write contents of a list of dicts to a CSV file."""
    fieldnames = list(data[0].keys())
    with open(file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def test_is_datastream_file(datadir, test_config):
    """Test the is_datastream_file function."""
    # Create a test file
    obj_csv = datadir / "objects" / "obj1" / "object.csv"
    ds_csv = datadir / "objects" / "obj1" / "datastreams.csv"
    dc_file = datadir / "objects" / "obj1" / "DC.xml"

    assert not is_datastream_file(obj_csv, test_config)
    assert not is_datastream_file(ds_csv, test_config)
    assert is_datastream_file(dc_file, test_config)

    no_file = datadir / "objects" / "obj1"
    assert not is_datastream_file(no_file, test_config)

    log_file = datadir / "objects" / "obj1" / "ingest.log"
    assert not is_datastream_file(log_file, test_config)


def test_get_rights(test_config, test_dc):
    """Test the get_rights function."""
    # If set in dc file, this value should be returned.
    assert get_rights(test_config, test_dc) == "Rights from DC.xml"

    # if not set in DC, use the value from the project configuration
    test_dc._data["rights"] = {"unspecified": [""]}
    assert get_rights(test_config, test_dc) == "Rights from project.toml"

    # if not set in configuration either, use the default value
    test_config.metadata.rights = ""
    assert get_rights(test_config, test_dc) == defaultvalues.DEFAULT_RIGHTS


def test_create_csv_missing_object(tmp_path, test_config):
    """Test the create_csv function with a missing object directory."""
    obj_dir = tmp_path / "missing"
    assert create_csv(obj_dir, test_config) is None


def test_create_csv(datadir, test_config):
    """Test the create_csv function."""
    object_dir = datadir / "objects" / "obj1"
    test_config.general.format_detector = "base"
    create_csv(object_dir, test_config)

    # check contents of the newly created object.csv file
    obj_csv = object_dir / "object.csv"
    with open(obj_csv, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == [field.name for field in fields(ObjectData)]
        first_object = next(iter(reader))
        assert first_object["project"] == "Test Project"
        assert first_object["creator"] == "GAMS Test Project"
        assert first_object["publisher"] == "GAMS"
        assert first_object["rights"] == "Rights from DC.xml"
        assert first_object["funder"] == "The funder"

    # check contents of the newly datastreams.csv file
    ds_csv = object_dir / "datastreams.csv"
    with open(ds_csv, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == [field.name for field in fields(DSData)]
        data = list(reader)
        assert len(data) == len(["DC.xml", "SOURCE.xml"])
        assert data[0]["dsid"] == "DC.xml"
        assert data[1]["dsid"] == "SOURCE.xml"
        assert data[0]["mimetype"] == "application/xml"


def test_create_csv_force_overwrite(datadir, test_config):
    """Test the create_csv function with force_overwrite=True."""

    def read_csv(file: Path) -> list[dict[str, str]]:
        with file.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)

    object_dir = datadir / "objects" / "obj1"
    obj_csv = object_dir / "object.csv"
    ds_csv = object_dir / "datastreams.csv"

    # create the csv files for the first time
    create_csv(object_dir, test_config)
    assert len(read_csv(obj_csv)) == 1
    assert len(read_csv(ds_csv)) == len(["DC.xml", "SOURCE.xml"])

    # recreate the csv files with force_overwrite=True
    create_csv(object_dir, test_config, force_overwrite=True)
    assert len(read_csv(obj_csv)) == 1
    assert len(read_csv(ds_csv)) == len(["DC.xml", "SOURCE.xml"])


def test_create_csv_files_existing_csvs(datadir, test_config, objcsvfile: Path, dscsvfile: Path):
    """Test the create_csv_files function.

    If the csv files already exist, they should not be overwritten.
    """
    # we create csv files in obj1 and obj2 dirextories to make sure
    # that existing csv files are not overwritten
    root = datadir / "objects"
    for obj in ["obj1", "obj2"]:
        obj_csv_path = root / obj / "object.csv"
        shutil.copy(objcsvfile, obj_csv_path)
        shutil.copy(dscsvfile, root / obj / "datastreams.csv")
    assert len(create_csv_files(root, test_config)) == 0


def test_create_csv_files(datadir, test_config):
    """The create_csv_files function should create the csv files for all objects."""
    objects_root_dir = datadir / "objects"
    processed_objectscsvs = create_csv_files(objects_root_dir, test_config)
    assert len(processed_objectscsvs) == len(["obj1", "obj2"])

    # Check if all csv files have been created
    assert (objects_root_dir / "obj1" / "object.csv").exists()
    assert (objects_root_dir / "obj1" / "datastreams.csv").exists()
    assert (objects_root_dir / "obj2" / "object.csv").exists()
    assert (objects_root_dir / "obj2" / "datastreams.csv").exists()

    obj_data = read_csv_file_to_dict(objects_root_dir / "obj1" / "object.csv", "recid")
    assert obj_data["obj1"]["title"] == "Object 1"
    obj_data = read_csv_file_to_dict(objects_root_dir / "obj2" / "object.csv", "recid")
    assert obj_data["obj2"]["title"] == "Object 2"

    ds_data = read_csv_file_to_dict(
        objects_root_dir / "obj1" / "datastreams.csv", "dsid"
    )
    assert len(ds_data) == len(["DC.xml", "SOURCE.xml"])
    assert ds_data["DC.xml"]["title"] == "XML Dublin Core metadata: DC.xml"
    assert ds_data["SOURCE.xml"]["title"] =="XML TEI document: SOURCE.xml"

    ds_data = read_csv_file_to_dict(
        objects_root_dir / "obj2" / "datastreams.csv", "dsid"
    )
    assert len(ds_data) == 1
    assert ds_data["DC.xml"]["title"] == "XML Dublin Core metadata: DC.xml"


def test_create_csv_files_with_update_flag(datadir, test_config):
    "The create_csv_files function should update the csv files for all objects."
    # create the initial csv files
    objects_root_dir = datadir / "objects"
    processed_objectcsvs = create_csv_files(objects_root_dir, test_config)
    assert len(processed_objectcsvs) == len(["obj1", "obj2"])

    # Check if all csv files have been created
    assert (objects_root_dir / "obj1" / "object.csv").exists()
    assert (objects_root_dir / "obj1" / "datastreams.csv").exists()
    assert (objects_root_dir / "obj2" / "object.csv").exists()
    assert (objects_root_dir / "obj2" / "datastreams.csv").exists()

    # now modify the csv files so we can check if they are updated
    # change title of the object in obj1/object.csv
    obj_data = read_csv_file_to_dict(objects_root_dir / "obj1" / "object.csv", "recid")
    obj_data["obj1"]["title"] = "New title"
    write_csv_file(objects_root_dir / "obj1" / "object.csv", list(obj_data.values()))
    # remove SOURCE.xml from the first ds entry from obj1/datastreams.csv
    ds_data = read_csv_file_to_dict(
        objects_root_dir / "obj1" / "datastreams.csv", "dsid"
    )
    ds_data.pop("SOURCE.xml")
    write_csv_file(
        objects_root_dir / "obj1" / "datastreams.csv", list(ds_data.values())
    )
    #change title of the DC.xml datastream in obj2/datastreams.csv
    ds_data = read_csv_file_to_dict(
        objects_root_dir / "obj2" / "datastreams.csv", "dsid"
    )
    ds_data["DC.xml"]["title"] = "New title"
    write_csv_file(
        objects_root_dir / "obj2" / "datastreams.csv", list(ds_data.values())
    )

    # # re-run create_csv_files with update=True
    processed_objectcsvs = create_csv_files(objects_root_dir, test_config, update=True)
    assert len(processed_objectcsvs) == len(["obj1", "obj2"])

    # The obj1/object.csv file should have the old title
    obj_data = read_csv_file_to_dict(objects_root_dir / "obj1" / "object.csv", "recid")
    assert obj_data["obj1"]["title"] == "Object 1"

    # in obj1/datastreams.csv the SOURCE.xml entry should be back
    ds_data = read_csv_file_to_dict(
        objects_root_dir / "obj1" / "datastreams.csv", "dsid"
    )
    assert "SOURCE.xml" in ds_data

    # in obj2/datastreams.csv the title of the DC.xml entry should be back
    ds_data = read_csv_file_to_dict(
        objects_root_dir / "obj2" / "datastreams.csv", "dsid"
    )
    assert ds_data["DC.xml"]["title"] == "XML Dublin Core metadata: DC.xml"


def test_update_csv(datadir, test_config):
    """Test the update_csv function.

    This function merges two versions of the csv files.
    """
    object_dir = datadir / "objects" / "obj1"
    obj_csv = object_dir / "object.csv"
    ds_csv = object_dir / "datastreams.csv"

    # create the initial version of the csv files
    create_csv(object_dir, test_config)
    assert obj_csv.exists()
    assert ds_csv.exists()

    # change the existing csv files:
    obj_txt = obj_csv.read_text(encoding="utf-8").replace(",Object 1,", ",Object 2,")
    # remove the last line (datastream) from the datastreams.csv file
    ds_lines = ds_csv.read_text(encoding="utf-8").splitlines()
    removed_line = ds_lines.pop()
    obj_csv.write_text(obj_txt, encoding="utf-8")
    ds_csv.write_text("\n".join(ds_lines), encoding="utf-8")

    update_csv(object_dir, test_config)
    obj_txt = obj_csv.read_text(encoding="utf-8")
    assert ",Object 1," in obj_txt
    ds_lines = ds_csv.read_text(encoding="utf-8").splitlines()
    assert removed_line in ds_lines


def test_extract_dsid():
    """Test the extract_dsid function."""
    # normal cases
    assert extract_dsid(Path("test.jpeg"), True) == "test.jpeg"
    assert extract_dsid(Path("test.jpeg"), False) == "test"
    assert extract_dsid(Path("test.jpeg"), True) == "test.jpeg"

    # str instead of Path
    assert extract_dsid("test.jpeg", True) == "test.jpeg"

    # invalid pid
    with pytest.raises(ValueError):
        extract_dsid(Path("täst"))

    # remove extension with suffix unknown to mimetypes
    assert extract_dsid(Path("test.unknown"), False) == "test"

    # if it does not seem to be an extension, keep it
    with pytest.warns(UserWarning, match=r"does not look like "):
        assert extract_dsid(Path("test.1234"), False) == "test.1234"
    with pytest.warns(UserWarning, match=r"does not look like "):
        assert extract_dsid(Path("test.a1234"), False) == "test.a1234"


def test_detect_languages(datadir):
    """We assume that dc does not contain language information.

    So we have to detect the language from the contents of the file.
    This method does nothing for now, but might be implemented in the future.
    """

    dsfile = datadir / "objects" / "obj1" / "SOURCE.xml"
    assert detect_languages(dsfile) == ""


def test_update_csv_missing_directory(tmp_path, test_config):
    """Test the update_csv function with a non-existent directory."""
    missing_dir = tmp_path / "nonexistent"
    assert update_csv(missing_dir, test_config) is None


def test_update_csv_new_directory(datadir, test_config):
    """Test the update_csv function on a directory without CSV files."""
    # Create a new object directory without CSV files
    object_dir = datadir / "objects" / "obj_new"
    object_dir.mkdir(exist_ok=True)

    # Copy DC.xml from an existing object
    dc_file_src = datadir / "objects" / "obj1" / "DC.xml"
    dc_file_dst = object_dir / "DC.xml"
    dc_file_dst.write_bytes(dc_file_src.read_bytes())

    # Update CSV should create new files
    result = update_csv(object_dir, test_config)
    assert result is not None
    assert (object_dir / "object.csv").exists()
    assert (object_dir / "datastreams.csv").exists()


def test_update_csv_add_datastream(datadir, tmp_path, test_config):
    """Test the update_csv function when adding a new datastream."""
    # Setup: Create a copy of an object directory to work with
    object_dir = tmp_path / "test_object"
    object_dir.mkdir()

    # Copy necessary files
    src_object = datadir / "objects" / "obj1"
    (object_dir / "DC.xml").write_bytes((src_object / "DC.xml").read_bytes())

    # Create initial CSV files
    create_csv(object_dir, test_config)

    # Count initial datastreams
    ds_csv = object_dir / "datastreams.csv"
    initial_lines = ds_csv.read_text(encoding="utf-8").splitlines()

    # Add a new datastream
    new_ds = object_dir / "NEW_FILE.txt"
    new_ds.write_text("Test content", encoding="utf-8")

    # Update the CSV files
    update_csv(object_dir, test_config)

    # Check that the new datastream was added
    updated_lines = ds_csv.read_text(encoding="utf-8").splitlines()
    assert len(updated_lines) > len(initial_lines)
    assert "NEW_FILE.txt" in ds_csv.read_text(encoding="utf-8")


def test_update_csv_metadata_changes(datadir, tmp_path, test_config):
    """Test that update_csv preserves manual edits but updates from source."""
    object_dir = tmp_path / "test_object_edit"
    object_dir.mkdir()

    # Copy necessary files
    src_object = datadir / "objects" / "obj1"
    (object_dir / "DC.xml").write_bytes((src_object / "DC.xml").read_bytes())
    (object_dir / "SOURCE.xml").write_bytes((src_object / "SOURCE.xml").read_bytes())

    # Create initial CSV files
    create_csv(object_dir, test_config)

    # Modify object.csv - simulate a manual edit
    obj_csv = object_dir / "object.csv"
    obj_txt = obj_csv.read_text(encoding="utf-8")
    manual_edits = obj_txt.replace("Object 1", "Manual Edit Title")
    obj_csv.write_text(manual_edits, encoding="utf-8")

    # Modify DC.xml - simulate a source change
    dc_file = object_dir / "DC.xml"
    dc_content = dc_file.read_text(encoding="utf-8")
    updated_dc = dc_content.replace("Rights from DC.xml", "Updated Rights")
    dc_file.write_text(updated_dc, encoding="utf-8")

    # Update CSV
    update_csv(object_dir, test_config)

    # Check that manual title edit remains and rights got updated
    updated_obj_txt = obj_csv.read_text(encoding="utf-8")
    assert "Manual Edit Title" not in updated_obj_txt  # Manual edit preserved
    assert "Updated Rights" in updated_obj_txt  # Source change applied


def test_is_datastream_file_with_ignores(datadir, test_config):
    """Test the is_datastream_file function more comprehensively.
    
    Main reason is to test if the function correctly identifies files
    that should be ignored based on the configuration settings.
    This includes regular files, CSV files, directories, and non-existent files.
    Also checks for files that match patterns but are not in the ignore list.
    """
    # Setup test files
    obj_dir = datadir / "objects" / "obj1"
    
    # Test regular files
    dc_file = obj_dir / "DC.xml"
    assert is_datastream_file(dc_file, test_config)
    
    # Test CSV files that should be ignored
    obj_csv = obj_dir / "object.csv"
    ds_csv = obj_dir / "datastreams.csv"
    assert not is_datastream_file(obj_csv, test_config)
    assert not is_datastream_file(ds_csv, test_config)
    
    # Test directories (should be ignored)
    assert not is_datastream_file(obj_dir, test_config)
    
    # Test non-existent files
    non_existent = obj_dir / "non_existent.txt"
    assert not is_datastream_file(non_existent, test_config)
    
    # Test ignored patterns from configuration
    log_file = obj_dir / "ingest.log"
    assert not is_datastream_file(log_file, test_config)
    
    # Test other common files that should be accepted
    text_file = obj_dir / "text.txt"
    if not text_file.exists():
        text_file.touch()
    assert is_datastream_file(text_file, test_config)
    
    # Test with file that matches a pattern but is not in the ignore list
    xml_file = obj_dir / "metadata.xml"
    if not xml_file.exists():
        xml_file.touch()
    assert is_datastream_file(xml_file, test_config)

