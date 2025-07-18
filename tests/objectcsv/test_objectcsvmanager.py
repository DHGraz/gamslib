import copy
import csv
import dataclasses
from pathlib import Path

import pytest

from gamslib.objectcsv.dsdata import DSData
from gamslib.objectcsv.objectcsvmanager import (
    DS_CSV_FILENAME,
    OBJ_CSV_FILENAME,
    ObjectCSVManager,
)
from gamslib.objectcsv.objectdata import ObjectData


def test_init_empty_objdir(tmp_path):
    """Test initialization with an empty object directory."""
    manager = ObjectCSVManager(tmp_path)
    assert manager.obj_dir == tmp_path
    assert manager.object_id == tmp_path.name
    # Initially, no object data or datastreams should be set
    assert manager._object_data is None
    assert manager.get_object() is None
    assert manager._datastream_data == []
    assert list(manager.get_datastreamdata()) == []

def test_init_with_nonexistent_objdir(tmp_path):
    """Test initialization with a non-existent object directory."""
    non_existing_dir = tmp_path / "non_existent_directory"
    
    with pytest.raises(FileNotFoundError):
        ObjectCSVManager(non_existing_dir)

def test_init_with_existing_csvs(tmp_path, objdata, dsdata):
    """Test initialization with existing object.csv and datastreams.csv files."""
    obj_csv_file = tmp_path / "object.csv"
    ds_csv_file = tmp_path / "datastreams.csv"

    # Create object.csv
    with open(obj_csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=objdata.fieldnames())
        writer.writeheader()
        writer.writerow(dataclasses.asdict(objdata))

    # Create datastreams.csv
    with open(ds_csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=DSData.fieldnames())
        writer.writeheader()
        writer.writerow(dataclasses.asdict(dsdata))

    manager = ObjectCSVManager(tmp_path)
    assert manager.get_object() == objdata
    assert manager._datastream_data == [dsdata]


def test_set_object(tmp_path, objdata):
    """Test setting the object data."""
    manager = ObjectCSVManager(tmp_path)
    manager.set_object(objdata)
    assert manager.get_object() == objdata

    # objdata can only be set once
    with pytest.raises(ValueError):
        manager.set_object(objdata)


def test_merge_object(tmp_path, objdata):
    """Test merging object data."""
    manager = ObjectCSVManager(tmp_path)
    manager.merge_object(objdata)
    assert manager.get_object() == objdata

    new_obj_data = copy.deepcopy(objdata)
    new_obj_data.title = "New title"
    manager.merge_object(new_obj_data)
    assert manager.get_object() == new_obj_data


def test_get_object(tmp_path, objdata):
    """Test getting the object data."""
    manager = ObjectCSVManager(tmp_path)
    assert manager.get_object() is None


def test_add_datastream(tmp_path, dsdata):
    """Test adding a datastream."""
    manager = ObjectCSVManager(tmp_path)
    manager.add_datastream(dsdata)
    assert len(manager._datastream_data) == 1
    datastreams = list(manager.get_datastreamdata())
    assert len(datastreams) == 1
    assert datastreams[0] == dsdata

    with pytest.raises(ValueError):
        manager.add_datastream(dsdata)


def test_merge_datastream(tmp_path, dsdata):
    """Test merging datastream data."""
    manager = ObjectCSVManager(tmp_path)
    manager.merge_datastream(dsdata)
    assert len(manager._datastream_data) == 1
    assert manager._datastream_data[0] == dsdata

    new_ds_data = copy.deepcopy(dsdata)
    new_ds_data.title = "New title"
    manager.merge_datastream(new_ds_data)
    assert len(manager._datastream_data) == 1
    assert manager._datastream_data[0].dspath == dsdata.dspath
    assert manager._datastream_data[0].title == new_ds_data.title


def test_is_empty_when_empty(tmp_path):
    """Test if the manager is empty with no existing csv files."""
    manager = ObjectCSVManager(tmp_path)
    assert manager.is_empty()


def test_is_empty_when_not_empty(tmp_path, objdata, dsdata):
    """Test if the manager is not empty with existing csv files."""
    obj_csv_file = tmp_path / "object.csv"
    ds_csv_file = tmp_path / "datastreams.csv"

    # Create object.csv
    with open(obj_csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=objdata.fieldnames())
        writer.writeheader()
        writer.writerow(dataclasses.asdict(objdata))

    # Create datastreams.csv
    with open(ds_csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=DSData.fieldnames())
        writer.writeheader()
        writer.writerow(dataclasses.asdict(dsdata))

    manager = ObjectCSVManager(tmp_path)
    assert manager.is_empty() is False


def test_is_empty_on_empty_obj_csv(tmp_path, dsdata):
    """Test the is_empty method if object.csv only contains the header."""
    obj_csv_file = tmp_path / "object.csv"
    ds_csv_file = tmp_path / "datastreams.csv"

    obj_csv_file = tmp_path / "object.csv"
    ds_csv_file = tmp_path / "datastreams.csv"

    # Create object.csv
    with open(obj_csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ObjectData.fieldnames())
        writer.writeheader()

    # Create datastreams.csv
    with open(ds_csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=DSData.fieldnames())
        writer.writeheader()
        writer.writerow(dataclasses.asdict(dsdata))

    manager = ObjectCSVManager(tmp_path)
    assert manager.is_empty() is True


def test_is_empty_on_empty_ds_csv(tmp_path, objdata):
    """Test the is_empty method if datastreams.csv only contains the header."""
    obj_csv_file = tmp_path / "object.csv"
    ds_csv_file = tmp_path / "datastreams.csv"

    # Create object.csv
    with open(obj_csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=objdata.fieldnames())
        writer.writeheader()
        writer.writerow(dataclasses.asdict(objdata))

    # Create datastreams.csv
    with open(ds_csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=DSData.fieldnames())
        writer.writeheader()

    manager = ObjectCSVManager(tmp_path)
    assert manager.is_empty() is True


def test_save_object_csv(tmp_path, objdata, dsdata):
    """Test saving object data to CSV."""
    manager = ObjectCSVManager(tmp_path)
    manager.set_object(objdata)
    manager.add_datastream(dsdata)
    manager.save()

    # Check if the file was created
    assert (tmp_path / OBJ_CSV_FILENAME).is_file()
    assert (tmp_path / DS_CSV_FILENAME).is_file()

    # Read back the data
    with open(tmp_path / OBJ_CSV_FILENAME, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        row = next(reader)
        assert row == dataclasses.asdict(objdata)
    with open(tmp_path / DS_CSV_FILENAME, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        row = next(reader)
        assert row == dataclasses.asdict(dsdata)


def test_validate(tmp_path, objdata, dsdata):
    """Test validation of object and datastream data."""
    manager = ObjectCSVManager(tmp_path)
    manager.set_object(objdata)
    manager.add_datastream(dsdata)

    assert manager.validate() is None  # Should not raise an exception


def test_validate_empty(tmp_path):
    """Test validation of empty object manager."""
    manager = ObjectCSVManager(tmp_path)
    with pytest.raises(ValueError, match="is not set"):
        manager.validate()


def test_validate_invalid_object(tmp_path, objdata, dsdata):
    """Test validation of invalid object data."""
    objdata.recid = ""  # Invalid recid

    manager = ObjectCSVManager(tmp_path)

    with pytest.raises(ValueError, match="Object metadata .* is not set"):
        manager.validate()


def test_validate_invalid_datastream(tmp_path, objdata, dsdata):
    """Test validation of invalid datastream data."""
    dsdata.dsid = ""  # Invalid dsid

    manager = ObjectCSVManager(tmp_path)
    manager.set_object(objdata)
    manager.add_datastream(dsdata)

    with pytest.raises(ValueError, match="must not be empty"):
        manager.validate()
def test_fix_for_mainresource(tmp_path):
    """mainresource was renamed to mainResource.

    Wee added code which still works with the old name, but uses the new name.
    This test makes sure that it works like expected.
    """
    obj_dict = {
        "recid": "obj1",
        "title": "The title",
        "project": "The project",
        "description": "The description with ÄÖÜ",
        "creator": "The creator",
        "rights": "The rights",
        "publisher": "The publisher",
        "source": "The source",
        "objectType": "The objectType",
        "mainresource": "TEI.xml",
    }
    # write test data to file
    csv_file = tmp_path / "object.csv"
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(obj_dict.keys()))
        writer.writeheader()
        writer.writerow(obj_dict)
    mgr = ObjectCSVManager(tmp_path)
    # read the object data
    data = mgr._read_object_csv()
    assert data.mainResource == "TEI.xml"

def test_guess_mainresource_single_xml(objcsvfile: Path, dscsvfile: Path, dsdata: DSData):
    """Test the guess_mainresource method with a single XML file."""
    # Create an ObjectCSV instance
    oc = ObjectCSVManager(objcsvfile.parent)
    
    # Clear existing datastreams and add a single XML file
    oc.clear()
    
    # Add a DC.xml file which should be ignored
    dc_ds = copy.deepcopy(dsdata)
    dc_ds.dspath = "obj1/DC.xml"
    dc_ds.dsid = "DC.xml"
    dc_ds.mimetype = "application/xml"
    oc.add_datastream(dc_ds)
    
    # Add a TEI XML file which should be detected as main resource
    tei_ds = copy.deepcopy(dsdata)
    tei_ds.dspath = "obj1/TEI.xml"
    tei_ds.dsid = "TEI.xml"
    tei_ds.mimetype = "application/tei+xml"
    oc.add_datastream(tei_ds)
    
    # Add object data
    obj = ObjectData(recid=oc.object_id)
    oc.set_object(obj)
    
    # Test guessing the main resource
    oc.guess_mainresource()
       
    # Verify the object data was updated
    assert oc.get_object().mainResource == "TEI.xml"
    
    


def test_guess_mainresource_multiple_xml(objcsvfile: Path, dscsvfile: Path, dsdata: DSData):
    """Test the guess_mainresource method with multiple XML files."""
    # Create an ObjectCSV instance
    oc = ObjectCSVManager(objcsvfile.parent)
    
    # Clear existing datastreams and add multiple XML files
    oc.clear()
    
    # Add an object data record
    obj = ObjectData(recid=oc.object_id)
    oc.set_object(obj)
    
    # Add several XML files
    xml_ds1 = copy.deepcopy(dsdata)
    xml_ds1.dspath = "obj1/file1.xml"
    xml_ds1.dsid = "FILE1"
    xml_ds1.mimetype = "application/xml"
    oc.add_datastream(xml_ds1)
    
    xml_ds2 = copy.deepcopy(dsdata)
    xml_ds2.dspath = "obj1/file2.xml"
    xml_ds2.dsid = "FILE2"
    xml_ds2.mimetype = "text/xml"
    oc.add_datastream(xml_ds2)
    
    # Test guessing the main resource - should return empty string for multiple XML files
    oc.guess_mainresource()
    
    # Verify object data mainResource was not set
    assert not oc.get_object().mainResource  # Should be empty


def test_guess_mainresource_no_xml(objcsvfile: Path, dscsvfile: Path, dsdata: DSData):
    """Test the guess_mainresource method with no XML files."""
    # Create an ObjectCSV instance
    oc = ObjectCSVManager(objcsvfile.parent)
    
    # Clear existing datastreams
    oc.clear()
    
    # Add an object data record
    obj = ObjectData(recid=oc.object_id)
    oc.set_object(obj)
    
    # Add a non-XML file
    non_xml_ds = copy.deepcopy(dsdata)
    non_xml_ds.dspath = "obj1/image.jpg"
    non_xml_ds.dsid = "IMG"
    non_xml_ds.mimetype = "image/jpeg"
    oc.add_datastream(non_xml_ds)
    
    # Test guessing the main resource - should return empty string for no XML files
    oc.guess_mainresource()
    
    # Verify object data mainResource was not set
    assert not oc.get_object().mainResource  # Should be empty

