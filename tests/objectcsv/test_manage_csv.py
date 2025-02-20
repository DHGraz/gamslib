"Unit tests for the manage_csv module."

import csv

from gamslib.objectcsv import ObjectCSV
from gamslib.objectcsv.manage_csv import (
    collect_csv_data,
    update_csv_files,
)


def test_collect_csv_data(datadir, tmp_path):
    "Collect data from all csv files in all object folders."
    root_dir = datadir / "objects"

    obj_file = tmp_path / "all_objects.csv"
    ds_file = tmp_path / "all_datastreams.csv"

    all_obj_csv = collect_csv_data(root_dir, obj_file, ds_file)

    assert all_obj_csv.object_dir == root_dir
    assert isinstance(all_obj_csv, ObjectCSV)

    assert obj_file.exists()
    assert ds_file.exists()

    with open(obj_file, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        data = sorted(list(reader), key=lambda x: x["recid"])

    assert len(data) == len(["obj1", "obj2"])
    assert data[0]["recid"] == "obj1"
    assert data[1]["recid"] == "obj2"

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


def test_update_csv_files(datadir):
    "Update a single object csv file with data from csv_data."

    collected_dir = datadir / "collected_csvs"
    objects_dir = datadir / "objects"

    num_objects, num_ds = update_csv_files(objects_dir, collected_dir)
    assert num_objects == len(["obj1", "obj2"])
    assert num_ds == len([
        "obj1/foo.xml",
        "obj1/foo.jpg",
        "obj1/DC.xml",
        "obj2/bar.xml",
        "obj2/bar.jpg",
        "obj2/DC.xml",
    ])

    # Check if the object.csv files have been updated
    with open(objects_dir / "obj1" / "object.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        obj_data = list(reader)
        assert obj_data[0]["title"] == "Object 1 new"
    with open(objects_dir / "obj2" / "object.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        obj_data = list(reader)
        assert obj_data[0]["title"] == "Object 2 new"

    # Check if the datastreams.csv files have been updated
    with open(objects_dir / "obj1" / "datastreams.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        ds_data = list(reader)
        assert ds_data[0]["title"] == "DCTitle new"
        assert ds_data[1]["title"] == "FooTitle 2 new"
        assert ds_data[2]["title"] == "FooTitle 1 new"
    with open(objects_dir / "obj2" / "datastreams.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        ds_data = list(reader)
        assert ds_data[0]["title"] == "DCTitle new"
        assert ds_data[1]["title"] == "BarTitle 2 new"
        assert ds_data[2]["title"] == "BarTitle 1 new"


def test_update_csv_files_no_collect_dir(datadir, monkeypatch):
    "What happends if we do not set an explicit input_dir?"

    input_dir = datadir / "collected_csvs"
    objects_dir = datadir / "objects"

    monkeypatch.chdir(input_dir)
    num_objects, num_ds = update_csv_files(objects_dir)
    assert num_objects == len(["obj1", "obj2"])
    assert num_ds == len([
        "obj1/foo.xml",
        "obj1/foo.jpg",
        "obj1/DC.xml",
        "obj2/bar.xml",
        "obj2/bar.jpg",
        "obj2/DC.xml",
    ])
