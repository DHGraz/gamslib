"""
Test the DSData class."""

import copy
import csv
from pathlib import Path

import pytest

from gamslib.objectcsv.datastreamscsvfile import DatastreamsCSVFile
from gamslib.objectcsv.dsdata import DSData
from gamslib.objectcsv.exceptions import ValidationError

@pytest.fixture
def sample_dsdata() -> DSData:
    """Fixture to provide DSData object for testing."""
    ds = DSData(
        dspath="obj1/TEI.xml",
        dsid="TEI.xml",
        mimetype="application/xml",
        rights="Rights",
        title="TEI file",
        description="TEI description",
        creator="Creator Name",
        lang="en",
        tags="tag1 tag2"
    )
    return ds
    
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


def test_from_csv_file_no_file(tmp_path: Path):
    """Test that from_csv raises FileNotFoundError if the csv file does not exist."""
    with pytest.raises(FileNotFoundError, match="Datastreams CSV file .* does not exist"):
        DatastreamsCSVFile.from_csv(tmp_path / "datastreams.csv")

def test_from_csv_files_empty(tmp_path: Path):
    """Test that from_csv raises ValidationError if the csv file is empty."""
    # file is totally empty
    dsfile = tmp_path / "datastreams.csv"
    dsfile.touch()  # create an empty file
    with pytest.raises(ValidationError, match="Empty datastreams.csv file .*"):
        DatastreamsCSVFile.from_csv(dsfile)        

        # file has only the header
    dsfile = tmp_path / "datastreams.csv"
    with dsfile.open("w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DSData.__dataclass_fields__.keys())
        writer.writeheader()
    with pytest.raises(ValidationError, match="Empty datastreams.csv file .*"):
        DatastreamsCSVFile.from_csv(dsfile)

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



def test_validate_empty_datastreamscsvfile(tmp_path: Path, dscsvfile: Path):
    """Test that validate raises ValidationError when DatastreamsCSVFile is empty."""
    dsfile = tmp_path / "datastreams.csv"

    # only header
    ds_csv_file = DatastreamsCSVFile(tmp_path)
    ds_csv_file.to_csv(dsfile)  # create an empty datastreams.csv file

    with pytest.raises(ValidationError) as excinfo:
        ds_csv_file.validate()
    assert "Empty datastreams.csv" in str(excinfo.value)

def test_validate_valid_datastream(tmp_path, sample_dsdata):
    """Test that validate does not raise an error when DSData is valid."""
    ds_csv_file = DatastreamsCSVFile(tmp_path)
    ds_csv_file.add_datastream(sample_dsdata)
    ds_csv_file.validate()  # should not raise an error

def test_validate_multiple_datastreams(tmp_path, sample_dsdata):    
    """Test that validate does not raise an error when multiple DSData are valid."""
    #dsfile = tmp_path / "datastreams.csv"
    ds_csv_file = DatastreamsCSVFile(tmp_path)
    ds_csv_file.add_datastream(sample_dsdata)
    ds2 = copy.deepcopy(sample_dsdata)
    ds2.dsid = "TEI2.xml"
    ds_csv_file.add_datastream(ds2)
    ds_csv_file.validate()

def test_validate_invalid_datastream(tmp_path, sample_dsdata):
    """Test that validate raises ValueError when DSData is invalid."""
    dsfile = tmp_path / "datastreams.csv"
    ds_csv_file = DatastreamsCSVFile(tmp_path)
    ds_csv_file.add_datastream(sample_dsdata)
    ds2 = copy.deepcopy(sample_dsdata)
    ds2.dsid = "foo"  
    ds_csv_file.add_datastream(ds2)
    ds_csv_file.validate()  # should not raise an error

def test_validate_datastreamscsvfile_with_empty_object_dir(tmp_path):
    """Test that validate raises ValidationError when DatastreamsCSVFile has empty object_dir."""
    ds_csv_file = DatastreamsCSVFile(tmp_path)
    ds_csv_file._object_dir = Path("")
    with pytest.raises(ValidationError) as excinfo:
        ds_csv_file.validate()
    assert "Empty datastreams.csv in " in str(excinfo.value)