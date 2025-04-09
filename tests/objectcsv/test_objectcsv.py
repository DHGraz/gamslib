"""Tests for the ObjectCSV class in the objectcsv.objectcsv module."""

import copy
import csv
from pathlib import Path

import pytest

from gamslib.objectcsv.dsdata import DSData
from gamslib.objectcsv.objectdata import ObjectData
from gamslib.objectcsv.objectcsv import ObjectCSV


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
    assert oc.get_languages() == ["en", "de", "nl", "it"]

    # we add a second de, which should move de to first position
    with dscsvfile.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        data = list(reader)
        data[-1]["lang"] = "de fr"
    with dscsvfile.open("w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
        writer.writeheader()
        writer.writerows(data)
    oc = ObjectCSV(objcsvfile.parent)
    assert oc.get_languages() == ["de", "en", "fr"]


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
    assert len(list(oc.get_datastreamdata())) == len([
        "obj1/TEI.xml", "obj2/TEI2.xml", "obj1/TEI3.xml"
    ])
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
