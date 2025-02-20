"""Tests for the objectsv.xlsx module."""

import csv
from gamslib.objectcsv.xlsx import csv_to_xlsx, xlsx_to_csv, read_csv


def test_read_csv(datadir):
    "Test the read_csv function."
    result = read_csv(datadir / "simple.csv", skip_header=False)
    assert len(result) == len(["foo", "foo1", "foo2"])
    assert result[0] == ["foo", "bar", "foobar"]
    assert result[1] == ["foo1", "bar1", "foobar1"]
    assert result[2] == ["foo2", "bar2", "foobar2"]

    result = read_csv(datadir / "simple.csv", skip_header=True)
    assert len(result) == len(["foo1", "foo2"])
    assert result[0] == ["foo1", "bar1", "foobar1"]
    assert result[1] == ["foo2", "bar2", "foobar2"]


def test_roundtrip(datadir):
    "If we convert csv files to xsls and back, we should get the same csv files."
    object_csv = datadir / "objects.csv"
    ds_csv = datadir / "datastreams.csv"
    xlsx_file = datadir / "metadata.xlsx"

    csv_to_xlsx(object_csv, ds_csv, xlsx_file)
    assert xlsx_file.exists()

    new_object_csv = datadir / "new_objects.csv"
    new_ds_csv = datadir / "new_datastreams.csv"
    xlsx_to_csv(xlsx_file, new_object_csv, new_ds_csv)

    with open(object_csv, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        old_object_data = list(reader)

    with open(new_object_csv, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        new_object_data = list(reader)

    assert old_object_data == new_object_data

    with open(ds_csv, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        old_ds_data = list(reader)
    with open(new_ds_csv, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        new_ds_data = list(reader)
    assert old_ds_data == new_ds_data
