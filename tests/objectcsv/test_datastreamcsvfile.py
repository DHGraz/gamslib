"""
Test the DSData class."""

import copy
import csv
from pathlib import Path

from gamslib.objectcsv.datastreamscsvfile import DatastreamsCSVFile
from gamslib.objectcsv.dsdata import DSData


def test_dscsvfile(dscsvfile: Path, dsdata: DSData):
    "Test the DatastreamsCSVFile object."
    dcf = DatastreamsCSVFile.from_csv(dscsvfile)
    result = list(dcf.get_datastreams())
    assert len(result) == len(["obj1/TEI.xml", "obj1/TEI2.xml"])
    assert result[0].dspath == "obj1/TEI.xml"
    assert result[1].dspath == "obj1/TEI2.xml"

    # test the get_data method with pid parameter
    result = list(dcf.get_datastreams("obj1"))
    assert len(result) == len(["obj1/TEI.xml", "obj1/TEI2.xml"])
    assert result[0] == dsdata

    result = list(dcf.get_datastreams("obj2"))
    assert len(result) == 0

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


def test_merge_existingdatastream(dscsvfile: Path):
    "Test the merge_datastream method."
    dcf = DatastreamsCSVFile.from_csv(dscsvfile)

    new_dsdata = DSData(
        dspath="obj1/TEI.xml",
        dsid="TEI.xml",
        title="Updated TEI file with üßÄ",
        description="Updated TEI",
        mimetype="application/json",
        creator="Updated Foo Bar",
        rights="Updated GPLv3",
    )
    dsdata_to_be_merged = dcf.get_datastream(new_dsdata.dspath)
    orig_dsdata = copy.deepcopy(dsdata_to_be_merged)

    merged_dsdata = dcf.merge_datastream(new_dsdata)

    assert merged_dsdata is dsdata_to_be_merged
    # check if the datastream has been updated
    assert merged_dsdata == dcf.get_datastream(new_dsdata.dspath)
    assert merged_dsdata.title == new_dsdata.title
    assert merged_dsdata.mimetype == new_dsdata.mimetype
    assert merged_dsdata.creator == new_dsdata.creator
    assert merged_dsdata.rights == new_dsdata.rights

    assert merged_dsdata.description == orig_dsdata.description
    assert merged_dsdata.lang == orig_dsdata.lang
    assert merged_dsdata.tags == orig_dsdata.tags


def test_merge_newdatastream(dscsvfile: Path):
    """ "Test the merge_datastream method is a ds did not exist."

    Testing this totally makes sense, because adding new datastreams is a required functionality.
    """
    dcf = DatastreamsCSVFile.from_csv(dscsvfile)
    new_dsdata = DSData(
        dspath="obj1/TEIx.xml",
        dsid="TEIx.xml",
        title="Updated TEI file with üßÄ",
        description="Updated TEI",
        mimetype="application/json",
        creator="Updated Foo Bar",
        rights="Updated GPLv3",
        lang="en de",
        tags="tag1 tag2",
    )

    merged_dsdata = dcf.merge_datastream(new_dsdata)

    assert merged_dsdata is new_dsdata
    # check if the datastream has been updated
    assert merged_dsdata == dcf.get_datastream(new_dsdata.dspath)
    assert merged_dsdata.title == new_dsdata.title
    assert merged_dsdata.mimetype == new_dsdata.mimetype
    assert merged_dsdata.creator == new_dsdata.creator
    assert merged_dsdata.rights == new_dsdata.rights

    assert merged_dsdata.description == new_dsdata.description
    assert merged_dsdata.lang == new_dsdata.lang
    assert merged_dsdata.tags == new_dsdata.tags
