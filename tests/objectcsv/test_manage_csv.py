"Unit tests for the manage_csv module."

import csv

import pytest

import gamslib
from gamslib.objectcsv.objectcollection import ObjectCollection
from gamslib.objectcsv.objectcsvmanager import ObjectCSVManager    
from gamslib.objectcsv.manage_csv import (
    collect_csv_data,
    split_from_csv,
    split_from_xlsx
)


@pytest.fixture
def collector(datadir):
    """Fixture to collect data from all csv files in all object folders.
    Provides a collector object with updated object and datastream data.
    This is used to test the split_from_xxx functions.
    """
    collector = ObjectCollection()
    collector.collect_from_objects(datadir / "objects")

    # replace all titles with the suffix " new"
    for obj_id, obj_data in collector.objects.items():
        # update the object data to have some new values
        obj_data.title = f"{obj_data.title} new"
        for dsdata in collector.datastreams.get(obj_id, []):
            dsdata.title = f"{dsdata.title} new"    
    return collector

def test_collect_csv_data(datadir, tmp_path):
    "Collect data from all csv files in all object folders."

    # this is where we put the collected data
    obj_file = tmp_path / "all_objects.csv"
    ds_file = tmp_path / "all_datastreams.csv"

    # this is the root dictory of all object directorie
    root_dir = datadir / "objects"


    collector = collect_csv_data(root_dir, obj_file, ds_file)

    # check if the objectcsv object and the 2 csv files have been created
    # assert collector.object_dir == root_dir
    assert isinstance(collector, ObjectCollection)
    assert obj_file.exists()
    assert ds_file.exists()

    # check if object data has been collected correctly
    with open(obj_file, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        obj_data = sorted(list(reader), key=lambda x: x["recid"])
    assert len(obj_data) == len(["obj1", "obj2"])
    assert obj_data[0]["recid"] == "obj1"
    assert obj_data[1]["recid"] == "obj2"

    # Check if the datastream data has been collected correctly
    with open(ds_file, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        data = list(reader)
    assert len(data) == len([
        "obj1/foo.xml",
        "obj1/foo.jpg",
        "obj1/DC.xml",
        "obj2/bar.xml",
        "obj2/bar.jpg",
        "obj2/DC.xml",
    ])
    dspaths = [row["dspath"] for row in data]
    assert "obj1/foo.xml" in dspaths
    assert "obj1/foo.jpg" in dspaths
    assert "obj1/DC.xml" in dspaths
    assert "obj2/bar.xml" in dspaths
    assert "obj2/bar.jpg" in dspaths
    assert "obj2/DC.xml" in dspaths


def test_split_from_csv(datadir, tmp_path, collector):
    "Update object folder csv metadata from the combined csv data."

    # this is where we put the collected data
    obj_file = tmp_path / "all_objects.csv"
    ds_file = tmp_path / "all_datastreams.csv"
    # this is the data we are starting with
    collector.save_to_csv(obj_file, ds_file)

    # this is the root dictory of all object directories
    root_dir = datadir / "objects"

    # split the collected data back into the object folders
    num_objects, num_ds = split_from_csv(root_dir, obj_file, ds_file)
    assert num_objects == len(["obj1", "obj2"])
    assert num_ds == 6  # noqa: PLR2004

    # check if the object.csv files have been updated
    for dir in ["obj1", "obj2"]:
        obj_csv = root_dir / dir / "object.csv"
        with open(obj_csv, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            obj_data = list(reader)
        assert obj_data[0]["title"].endswith(" new"), f"{obj_data[0]}.title does not end with ' new'" 

        ds_csv = root_dir / dir / "datastreams.csv"
        with open(ds_csv, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            ds_data = list(reader)
        assert ds_data[0]["title"].endswith(" new"), f"{ds_data[0]}.title does not end with ' new'"

def test_split_from_xlsx(datadir, tmp_path, collector):    
    "Update object folder csv metadata from the combined xlsx data."

    # this is where we put the collected data
    xlsx_file = tmp_path / "all_objects.xlsx"

    # this is the root dictory of all object directories
    root_dir = datadir / "objects"

    collector.save_to_xlsx(xlsx_file)

    # this is the root dictory of all object directories
    root_dir = datadir / "objects"

    # split the collected data back into the object folders
    num_objects, num_ds = split_from_xlsx(root_dir, xlsx_file)

    assert num_objects == len(["obj1", "obj2"])
    assert num_ds == 6  # noqa: PLR2004

    # check if the object.csv files have been updated
    for dir in ["obj1", "obj2"]:
        obj_csv = root_dir / dir / "object.csv"
        with open(obj_csv, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            obj_data = list(reader)
        assert obj_data[0]["title"].endswith(" new"), f"{obj_data[0]}.title does not end with ' new'" 

        ds_csv = root_dir / dir / "datastreams.csv"
        with open(ds_csv, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            ds_data = list(reader)
        assert ds_data[0]["title"].endswith(" new"), f"{ds_data[0]}.title does not end with ' new'"



# def test_update_csv_files_no_collect_dir(datadir, monkeypatch):
#     "What happends if we do not set an explicit input_dir?"

#     input_dir = datadir / "collected_csvs"
#     objects_dir = datadir / "objects"

#     monkeypatch.chdir(input_dir)
#     num_objects, num_ds = split_csv_files(objects_dir)
#     assert num_objects == len(["obj1", "obj2"])
#     assert num_ds == len([
#         "obj1/foo.xml",
#         "obj1/foo.jpg",
#         "obj1/DC.xml",
#         "obj2/bar.xml",
#         "obj2/bar.jpg",
#         "obj2/DC.xml",
#     ])
