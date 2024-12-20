"Unit tests for the manage_csv module."

import csv
import shutil

from gamslib.objectcsv import ObjectCSV
from gamslib.objectcsv.manage_csv import (
    collect_csv_data,
    update_csv_files,
)


def test_collect_csv_data(datadir):
    "Collect data from all csv files in all object folders."
    root_dir = datadir / "objects"
    all_obj_csv = collect_csv_data(root_dir)

    assert all_obj_csv.object_dir == root_dir
    assert isinstance(all_obj_csv, ObjectCSV)

    obj_file = root_dir / "all_objects.csv"
    ds_file = root_dir / "all_datastreams.csv"
    assert obj_file.exists()
    assert ds_file.exists()

    with open(obj_file, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        data = sorted(list(reader), key = lambda x: x["recid"])
    
    assert len(data) == 2  # we have to objects
    assert data[0]["recid"] == "obj1"
    assert data[1]["recid"] == "obj2"

    with open(ds_file, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        data = list(reader)
    assert len(data) == 6  # we have 6 datastreams
    dspaths = [row["dspath"] for row in data]
    assert "obj1/foo.xml" in dspaths
    assert "obj1/foo.jpg" in dspaths
    assert "obj1/DC.xml" in dspaths
    assert "obj2/bar.xml" in dspaths
    assert "obj2/bar.jpg" in dspaths
    assert "obj2/DC.xml" in dspaths


def test_collect_csv_data_different_output_dir(datadir, tmp_path):
    "Write collection data to a different output directory."

    # we set an output directory but do not change filename
    root_dir = datadir / "objects"
    output_dir = tmp_path / "foo"
    output_dir.mkdir()

    collect_csv_data(root_dir, output_dir)
    assert (output_dir / "all_objects.csv").exists()
    assert (output_dir / "all_datastreams.csv").exists()

    # we set both output directory and filenames
    output_dir = tmp_path / "bar"
    output_dir.mkdir()

    collect_csv_data(root_dir, output_dir, "foo.csv", "bar.csv")
    assert (output_dir / "foo.csv").exists()
    assert (output_dir / "bar.csv").exists()


def test_update_csv_files(datadir):
    "Update a single object csv file with data from csv_data."
    collected_dir = datadir / "collected_csvs"
    objects_dir = datadir / "objects"

    num_objects, num_ds = update_csv_files(objects_dir, collected_dir)
    assert num_objects == 2
    assert num_ds == 6

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


def test_update_csv_files_no_collect_dir(datadir):
    "What happends if we do not set an explicit collected_csv dir?"

    # cove the all_xxx csv files over to the objects directory
    collected_dir = datadir / "collected_csvs"
    objects_dir = datadir / "objects"
    shutil.move(collected_dir / "all_objects.csv", objects_dir / "all_objects.csv")
    shutil.move(
        collected_dir / "all_datastreams.csv", objects_dir / "all_datastreams.csv"
    )

    num_objects, num_ds = update_csv_files(objects_dir)
    assert num_objects == 2
    assert num_ds == 6
