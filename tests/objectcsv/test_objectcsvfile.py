"""Tests for the ObjectCSVFile class."""

import copy
import csv
from pathlib import Path

import pytest

from gamslib.objectcsv.exceptions import ValidationError
from gamslib.objectcsv.objectcsvfile import ObjectCSVFile
from gamslib.objectcsv.objectdata import ObjectData


def test_objectcsvfile(objcsvfile: Path, objdata: ObjectData):
    "Should create an ObjectCSVFile object from a csv file."
    ocf = ObjectCSVFile.from_csv(objcsvfile)
    result = list(ocf.get_data())
    assert len(result) == 1
    assert result[0] == objdata

    # test the get_data method with pid parameter, which should return the same result,
    # because we only have one object in the csv file
    result = list(ocf.get_data("obj1"))
    assert len(result) == 1
    assert result[0] == objdata

    # and the __len__method
    assert len(ocf) == 1

    # now save the object to a new csv file and compare the content
    csv_file = objcsvfile.parent / "object2.csv"
    ocf.to_csv(csv_file)
    assert objcsvfile.read_text() == csv_file.read_text()


def test_from_csv_file_no_file(tmp_path: Path):
    """Test that from_csv raises FileNotFoundError if the csv file does not exist."""
    with pytest.raises(FileNotFoundError, match="Object CSV file .* does not exist"):
        ObjectCSVFile.from_csv(tmp_path / "object.csv") 


def test_from_csv_file_empty(tmp_path: Path):
    """Test that from_csv raises ValidationError if the csv file is empty."""
    # totaly empty file
    csv_file = tmp_path / "object.csv"
    csv_file.touch()
    with pytest.raises(ValidationError, match="Empty object.csv file"):
        ObjectCSVFile.from_csv(csv_file)    


    # only header line
    with csv_file.open("w", encoding="utf-8", newline="") as f:
        # write only the header line
        writer = csv.DictWriter(f, fieldnames=ObjectData.__dataclass_fields__.keys())
        writer.writeheader()

    with pytest.raises(ValidationError, match="Empty object.csv file"):
        ObjectCSVFile.from_csv(csv_file)    

def test_merge(objcsvfile: Path):
    "Should merge two ObjectCSVFile objects."
    ocf = ObjectCSVFile.from_csv(objcsvfile)
    old_objdata = next(ocf.get_data("obj1"))
    original_objdata = copy.deepcopy(old_objdata)
    new_objdata = ObjectData(
        recid="obj1",
        title="Updated title",
        project="Updated project",
        description="Update description with ÄÖÜ",
        creator="Upodated creator",
        rights="Updated rights",
        publisher="Updated publisher",
        source="Updated source",
        objectType="Updated objectType",
        mainResource="TEI2.xml",
    )
    updated_objdata = ocf.merge_object(new_objdata)

    # make sure we really have updated the old object
    assert updated_objdata is old_objdata

    # Check if merge was applied correctly
    assert updated_objdata.title == new_objdata.title
    assert updated_objdata.project == new_objdata.project

    assert updated_objdata.creator == new_objdata.creator
    assert updated_objdata.rights == new_objdata.rights
    assert updated_objdata.publisher == new_objdata.publisher
    assert updated_objdata.source == new_objdata.source
    assert updated_objdata.objectType == new_objdata.objectType
    assert updated_objdata.mainResource == new_objdata.mainResource

    assert updated_objdata.description == original_objdata.description


def test_merge_non_existent(objcsvfile: Path):
    "Should mergin to a non existing object should not merge but add the new object."
    ocf = ObjectCSVFile.from_csv(objcsvfile)
    # old_objdata = next(ocf.get_data("obj1"))
    # original_objdata = copy.deepcopy(old_objdata)
    new_objdata = ObjectData(
        recid="obj99",
        title="Updated title",
        project="Updated project",
        description="Update description with ÄÖÜ",
        creator="Upodated creator",
        rights="Updated rights",
        publisher="Updated publisher",
        source="Updated source",
        objectType="Updated objectType",
        mainResource="TEI2.xml",
    )
    updated_objdata = ocf.merge_object(new_objdata)

    # make sure we added the new object
    assert updated_objdata is new_objdata

    # Check if merge was applied correctly
    assert updated_objdata.title == new_objdata.title
    assert updated_objdata.project == new_objdata.project

    assert updated_objdata.creator == new_objdata.creator
    assert updated_objdata.rights == new_objdata.rights
    assert updated_objdata.publisher == new_objdata.publisher
    assert updated_objdata.source == new_objdata.source
    assert updated_objdata.objectType == new_objdata.objectType
    assert updated_objdata.mainResource == new_objdata.mainResource

    assert updated_objdata.description == new_objdata.description


# ----------------- test the validate method of ObjectCSVFile ----------------


def test_validate_empty_objectcsvfile(tmp_path: Path):
    """Test that validate raises ValidationError when ObjectCSVFile is empty."""
    # a fresh ObjectCSVFile should raise ValidationError
    obj_csv_file = ObjectCSVFile()
    with pytest.raises(ValidationError) as excinfo:
        obj_csv_file.validate()
    assert "Empty object.csv" in str(excinfo.value)


def test_validate_empty_objectcsvfile_with_empty_csv(tmp_path: Path):
    csv_file = tmp_path / "object.csv"

    # create a csv file which only contains the header
    obj_csv_file = ObjectCSVFile()
    obj_csv_file.to_csv(csv_file)
    assert csv_file.exists()
    assert len(csv_file.read_text().splitlines()) == 1  # only header line

    # validation shlould fail if there is no data in the csv file
    with pytest.raises(ValidationError) as excinfo:
        obj_csv_file.validate()
    assert "Empty object.csv" in str(excinfo.value)


def test_validate_valid_objectdata():
    """Test that validate does not raise an error when ObjectData is valid."""
    obj_csv_file = ObjectCSVFile()
    obj_data = ObjectData(
        recid="obj1", title="Title", rights="Rights", source="Source", objectType="Type"
    )
    obj_csv_file.add_objectdata(obj_data)
    obj_csv_file.validate()  # should not raise an error


def test_validate_invalid_objectdata():
    """Test that validate raises ValueError when ObjectData is invalid."""
    obj_csv_file = ObjectCSVFile()
    obj_data = ObjectData(
        recid="", title="Title", rights="Rights", source="Source", objectType="Type"
    )
    obj_csv_file.add_objectdata(obj_data)
    with pytest.raises(ValueError) as excinfo:
        obj_csv_file.validate()
    assert "recid must not be empty" in str(excinfo.value)


def test_validate_multiple_objectdata():
    """Test that validate checks all ObjectData objects."""
    obj_csv_file = ObjectCSVFile()
    obj_data1 = ObjectData(
        recid="obj1", title="Title", rights="Rights", source="Source", objectType="Type"
    )
    obj_data2 = ObjectData(
        recid="", title="Title", rights="Rights", source="Source", objectType="Type"
    )
    obj_csv_file.add_objectdata(obj_data1)
    obj_csv_file.add_objectdata(obj_data2)
    with pytest.raises(ValueError) as excinfo:
        obj_csv_file.validate()
    assert "recid must not be empty" in str(excinfo.value)


def test_validate_objectcsvfile_with_empty_object_dir():
    """Test that validate raises ValidationError when ObjectCSVFile has empty object_dir."""
    obj_csv_file = ObjectCSVFile()
    obj_csv_file._object_dir = Path("")
    with pytest.raises(ValidationError) as excinfo:
        obj_csv_file.validate()
    assert "Empty object.csv in " in str(excinfo.value)


def test_to_csv_with_path(tmp_path: Path):
    """Test to_csv with a provided path."""
    obj_csv_file = ObjectCSVFile()
    obj_data = ObjectData(
        recid="obj1", title="Title", rights="Rights", source="Source", objectType="Type"
    )
    obj_csv_file.add_objectdata(obj_data)

    csv_file = tmp_path / "custom_object.csv"
    obj_csv_file.to_csv(csv_file)

    # Check if file exists and has correct content
    assert csv_file.exists()
    content = csv_file.read_text()
    assert "recid,title,project,description" in content

    # Check if object_dir was updated
    assert obj_csv_file._object_dir == tmp_path


def test_to_csv_without_path(tmp_path: Path):
    """Test to_csv using the default path from object_dir."""
    obj_csv_file = ObjectCSVFile(tmp_path)
    obj_data = ObjectData(
        recid="obj1", title="Title", rights="Rights", source="Source", objectType="Type"
    )
    obj_csv_file.add_objectdata(obj_data)

    obj_csv_file.to_csv(None)

    # Check if file exists at the default location
    csv_file = tmp_path / "object.csv"
    assert csv_file.exists()
    content = csv_file.read_text()
    assert "recid,title,project,description" in content
