"""Fixtures for testing objectcsv module."""

import copy
import csv
from dataclasses import asdict
from pathlib import Path

import pytest

from gamslib.objectcsv.dsdata import DSData
from gamslib.objectcsv.objectdata import ObjectData


@pytest.fixture(name="objdata")
def objdata_fixture() -> ObjectData:
    "Return a ObjectData object."
    return ObjectData(
        recid="obj1",
        title="The title",
        project="The project",
        description="The description with ÄÖÜ",
        creator="The creator",
        rights="The rights",
        publisher="The publisher",
        source="The source",
        objectType="The objectType",
        mainResource="TEI.xml",
    )


@pytest.fixture(name="dsdata")
def dsdata_fixture() -> DSData:
    "Return a DSData object."
    return DSData(
        dspath="obj1/TEI.xml",
        dsid="TEI.xml",
        title="The TEI file with üßÄ",
        description="A TEI",
        mimetype="application/xml",
        creator="Foo Bar",
        rights="GPLv3",
        lang="en; de",
        tags="tag 1, tag 2, tag 3",
    )


@pytest.fixture(name="objcsvfile")
def objcsvfile_fixture(objdata: ObjectData, tmp_path: Path) -> Path:
    "Return path to an object.csv file from objdata"
    data = asdict(objdata)
    col_names = list(data.keys())
    csv_file = tmp_path / "obj1" / "object.csv"
    csv_file.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=col_names)
        writer.writeheader()
        writer.writerow(data)
    return csv_file


@pytest.fixture(name="dscsvfile")
def dscsvfile_fixture(dsdata: DSData, tmp_path: Path) -> Path:
    """Return path to a datastreams.csv file.

    Contains data from dsdata as first element and a copy of dsdata,
    where object id, dspath and dsid are different.
    """
    ds1 = asdict(dsdata)
    ds2 = copy.deepcopy(ds1)
    ds2["dspath"] = "obj1/TEI2.xml"
    ds2["dsid"] = "TEI2.xml"
    ds2["lang"] = "nl; it"
    ds2["tags"] = ["tag 8", "tag 9"]

    col_names = list(ds1.keys())

    csv_file = tmp_path / "obj1" / "datastreams.csv"
    csv_file.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=col_names)
        writer.writeheader()
        writer.writerow(ds1)
        writer.writerow(ds2)
    return csv_file
