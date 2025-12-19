"""Tests for the objectsv.xlsx module."""

import csv
import zipfile
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


def test_encoding_roundtrip(datadir, tmp_path):
    "Test if converting csv to xslx and back works with special characters."
    object_csv = datadir / "objects_encoding_problem.csv"
    ds_csv = datadir / "datastreams_encoding_problem.csv"
    xlsx_file = datadir / "metadata.xlsx"

    csv_to_xlsx(object_csv, ds_csv, xlsx_file)
    assert xlsx_file.exists()

    # converting back to csv should work anyhow
    new_object_csv = tmp_path / "new_objects.csv"
    new_ds_csv = tmp_path / "new_datastreams.csv"
    xlsx_to_csv(xlsx_file, new_object_csv, new_ds_csv)

    with new_object_csv.open("r", encoding="utf-8", newline="") as f:
        text = f.read()
        assert "الوصف" in text  
    with ds_csv.open("r", encoding="utf-8", newline="") as f:
        text = f.read()
        assert "الوصف" in text


def test_encoding_in_xslx(datadir):
    "Test if special characters are correctly written to xlsx we circumvent openpyxl when reading."
    object_csv = datadir / "objects_encoding_problem.csv"
    ds_csv = datadir / "datastreams_encoding_problem.csv"
    xlsx_file = datadir / "metadata.xlsx"
    # I'd expect this to fail if special characters are not correctly written to xlsx,
    # but it seems to work even under windows with cp1252 as default encoding?!?
    csv_to_xlsx(object_csv, ds_csv, xlsx_file)
    assert xlsx_file.exists()

    # now read the xlsx file and check if special characters are present
    with zipfile.ZipFile(xlsx_file, "r") as zip_:
        xml = zip_.read("xl/sharedStrings.xml").decode("utf-8")
    assert 'الوصف' in xml


