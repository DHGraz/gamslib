import csv
from pathlib import Path

from gamslib.objectcsv.datastreamscsvfile import DatastreamsCSVFile
from gamslib.objectcsv.dsdata import DSData


def test_dscsvfile(dscsvfile: Path, dsdata: DSData):
    "Test the DatastreamsCSVFile object."
    dcf = DatastreamsCSVFile.from_csv(dscsvfile)
    result = list(dcf.get_data())
    assert len(result) == len(["obj1/TEI.xml", "obj2/TEI2.xml"])
    assert result[0].dspath == "obj1/TEI.xml"
    assert result[1].dspath == "obj2/TEI2.xml"

    # test the get_data method with pid parameter
    result = list(dcf.get_data("obj1"))
    assert len(result) == 1
    assert result[0] == dsdata

    result = list(dcf.get_data("obj2"))
    assert len(result) == 1

    # test the __len__ method
    assert len(dcf) == len(["obj1/TEI.xml", "obj2/TEI2.xml"])

    # now save the datastream.csv file to a new file and compare the content
    csv_file = dscsvfile.parent / "datastreams2.csv"
    dcf.to_csv(csv_file)
    assert dscsvfile.read_text(encoding="utf-8") == csv_file.read_text(encoding="utf-8")


def test_dccsvfile_get_languages(dscsvfile: Path):
    "Test the get_languages method."
    dcf = DatastreamsCSVFile.from_csv(dscsvfile)
    assert dcf.get_languages() == ["en", "de", "nl", "it"]

    # missing lang field: we set lang of last ds to ""
    with dscsvfile.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        data = list(reader)
        data[-1]["lang"] = ""
    with dscsvfile.open("w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
        writer.writeheader()
        writer.writerows(data)
    dcf = DatastreamsCSVFile.from_csv(dscsvfile)
    assert dcf.get_languages() == ["en", "de"]

