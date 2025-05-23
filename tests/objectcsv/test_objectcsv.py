"""Tests for the ObjectCSV class in the objectcsv.objectcsv module."""

import copy
import csv
from pathlib import Path

import pytest

from gamslib.objectcsv.dsdata import DSData
from gamslib.objectcsv.objectcsv import ObjectCSV
from gamslib.objectcsv.objectdata import ObjectData


def test_object_csv(objcsvfile: Path, dscsvfile: Path, tmp_path: Path):
    "Should create an ObjectCSV object."

    oc = ObjectCSV(objcsvfile.parent)
    assert len(oc.object_data) == 1
    assert len(oc.datastream_data) == len(["obj1/TEI.xml", "obj2/TEI2.xml"])
    assert oc.is_new() is False
    assert oc.object_id == "obj1"

    assert oc.count_objects() == 1
    assert oc.count_datastreams() == len(["obj1/TEI.xml", "obj2/TEI2.xml"])

    # test write
    objcsvfile.unlink()
    dscsvfile.unlink()
    oc.write()
    assert objcsvfile.exists()
    assert dscsvfile.exists()

    # test write with explicit filenames
    obj_csv = tmp_path / "o.csv"
    ds_csv = tmp_path / "d.csv"
    oc.write(obj_csv, ds_csv)
    assert obj_csv.exists()
    assert ds_csv.exists()
    assert obj_csv.read_text(encoding="utf-8") == objcsvfile.read_text(encoding="utf-8")
    assert ds_csv.read_text(encoding="utf-8") == dscsvfile.read_text(encoding="utf-8")

    # test clear()
    oc.clear()
    assert oc.count_objects() == 0
    assert oc.count_datastreams() == 0


def test_objectcsv_get_languages(objcsvfile: Path, dscsvfile: Path):
    "Test the get_languages method."
    oc = ObjectCSV(objcsvfile.parent)
    #oc.datastream_data._datastreams[0].lang = "en; de; nl"
    #oc.datastream_data._datastreams[1].lang = "it;en"
    assert oc.get_languages() == ["en", "de", "nl", "it"]

    # we add a second de, which should move de to first position
    with dscsvfile.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        data = list(reader)
        data[-1]["lang"] += "; de"
    with dscsvfile.open("w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
        writer.writeheader()
        writer.writerows(data)
    oc = ObjectCSV(objcsvfile.parent)
    assert oc.get_languages() == ["de", "en", "nl", "it"]


def test_object_csv_modify_get_set_data(
    objcsvfile: Path, dscsvfile: Path, objdata: ObjectData, dsdata: DSData
):
    "Test if adding and retrieving object and datastream data works."
    # test add_datastream() and get_datastreamdata()
    oc = ObjectCSV(objcsvfile.parent)

    # test adding a datastream
    new_ds = copy.deepcopy(dsdata)
    new_ds.dspath = "obj1/TEI3.xml"
    oc.add_datastream(new_ds)
    assert oc.count_datastreams() == len(
        ["obj1/TEI.xml", "obj2/TEI2.xml", "obj1/TEI3.xml"]
    )
    assert len(list(oc.get_datastreamdata())) == len(
        ["obj1/TEI.xml", "obj2/TEI2.xml", "obj1/TEI3.xml"]
    )
    assert list(oc.get_datastreamdata("obj1"))[-1] == new_ds

    # test add_objectdata() and get_objectdata()
    new_obj = copy.deepcopy(objdata)
    new_obj.recid = "obj2"
    oc.add_objectdata(new_obj)
    assert len(list(oc.get_objectdata())) == len(["obj1", "obj2"])
    assert list(oc.get_objectdata("obj2"))[-1] == new_obj

    # test write() with overwriting the original csv files
    objcsvfile.unlink()
    dscsvfile.unlink()

    oc.write(objcsvfile, dscsvfile)

    assert objcsvfile.exists()
    assert dscsvfile.exists()


def test_objectcsv_empty_dir(tmp_path):
    "The the is_new method with an empty directory."
    empty_oc = ObjectCSV(tmp_path)
    assert empty_oc.is_new()


def test_objectcsv_missing_dir():
    "Should raise an exception if the directory does not exist."
    with pytest.raises(FileNotFoundError):
        ObjectCSV(Path("does_not_exist"))


def test_update_objectdata(objcsvfile: Path, objdata: ObjectData):
    """Test the update_objectdata method."""
    # Create an ObjectCSV instance
    oc = ObjectCSV(objcsvfile.parent)

    # Get the initial object data for modification
    initial_obj = next(oc.get_objectdata())
    modified_obj = copy.deepcopy(initial_obj)

    # Modify some fields in the object data
    modified_obj.title = "Updated Title"
    modified_obj.creator = "Updated Creator"

    # Update the object data
    oc.update_objectdata(modified_obj)

    # Check if the update was successful
    updated_obj = next(oc.get_objectdata())
    assert updated_obj.title == "Updated Title"
    assert updated_obj.creator == "Updated Creator"
    assert updated_obj.recid == initial_obj.recid  # The ID should remain the same

    # Test updating with a different object that has the same ID
    new_obj = copy.deepcopy(objdata)
    new_obj.recid = initial_obj.recid  # Same ID
    new_obj.title = "Another Title"
    new_obj.creator = "Another Creator"

    oc.update_objectdata(new_obj)

    # Verify the object was updated correctly
    result_obj = next(oc.get_objectdata())
    assert result_obj.title == "Another Title"
    assert result_obj.creator == "Another Creator"
    assert result_obj.recid == initial_obj.recid

# pylint: disable=unused-argument
def test_update_datastreams(objcsvfile: Path, dscsvfile: Path):
    """Test the update_datastreams method."""
    # Create an ObjectCSV instance
    oc = ObjectCSV(objcsvfile.parent)

    # Get the initial datastreams
    initial_datastreams = list(oc.get_datastreamdata())
    assert len(initial_datastreams) > 0

    # Make a copy of the first datastream and modify it
    modified_ds = copy.deepcopy(initial_datastreams[0])
    new_ds = copy.deepcopy(initial_datastreams[0])
    modified_ds.title = "Updated Datastream"
    modified_ds.creator = "Updated Creator"
    new_ds.dspath = "obj1/NEW.xml"
    new_ds.dsid = "NEW"
    new_ds.title = "New Datastream"
    new_ds.creator = "Updated Creator"

    # Update with modified and new datastreams
    update_list = [modified_ds, new_ds]
    oc.update_datastreams(update_list)

    # Verify the results
    updated_datastreams = list(oc.get_datastreamdata())

    # Should have exactly 2 datastreams now
    assert len(updated_datastreams) == len(["obj1/TEI.xml", "obj1/NEW.xml"])

    # Check that the modified datastream was updated correctly
    found_modified = False
    found_new = False
    for ds in updated_datastreams:
        if ds.dspath == modified_ds.dspath and ds.dsid == modified_ds.dsid:
            assert ds.title == "Updated Datastream"
            assert ds.creator == "Updated Creator"
            found_modified = True
        elif ds.dspath == new_ds.dspath and ds.dsid == new_ds.dsid:
            assert ds.title == "New Datastream"
            found_new = True
    assert found_modified
    assert found_new

    # Assert that the obj1/TEI2.xml datastream has been removed from the updated datastreams
    assert "obj1/TEI2.xml" not in [ds.dspath for ds in updated_datastreams]
