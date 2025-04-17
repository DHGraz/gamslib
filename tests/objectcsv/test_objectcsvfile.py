"""Tests for the ObjectCSVFile class."""

import copy
from pathlib import Path

from gamslib.objectcsv.objectcsvfile import ObjectCSVFile
from gamslib.objectcsv.objectdata import ObjectData


def test_objectcsvfile(objcsvfile: Path, objdata: ObjectData):
    "Should create an ObjectCSVFile object from a csv file."
    ocf = ObjectCSVFile.from_csv(objcsvfile)
    result = list(ocf.get_data())
    assert len(result) == 1
    assert result[0] == objdata

    # test the get_data method with pid parameter, which should return the same result,
    # because we only have one object in the csv file
    result = list(ocf.get_data("obj1"))
    assert len(result) == 1
    assert result[0] == objdata

    # and the __len__method
    assert len(ocf) == 1

    # now save the object to a new csv file and compare the content
    csv_file = objcsvfile.parent / "object2.csv"
    ocf.to_csv(csv_file)
    assert objcsvfile.read_text() == csv_file.read_text()


def test_merge(objcsvfile: Path):
    "Should merge two ObjectCSVFile objects."
    ocf = ObjectCSVFile.from_csv(objcsvfile)
    old_objdata = next(ocf.get_data("obj1"))
    original_objdata = copy.deepcopy(old_objdata)
    new_objdata = ObjectData(
        recid="obj1",
        title="Updated title",
        project="Updated project",
        description="Update description with ÄÖÜ",
        creator="Upodated creator",
        rights="Updated rights",
        publisher="Updated publisher",
        source="Updated source",
        objectType="Updated objectType",
        mainResource="TEI2.xml",
    )
    updated_objdata = ocf.merge_object(new_objdata)

    # make sure we really have updated the old object
    assert updated_objdata is old_objdata

    # Check if merge was applied correctly
    assert updated_objdata.title == new_objdata.title
    assert updated_objdata.project == new_objdata.project

    assert updated_objdata.creator == new_objdata.creator
    assert updated_objdata.rights == new_objdata.rights
    assert updated_objdata.publisher == new_objdata.publisher
    assert updated_objdata.source == new_objdata.source
    assert updated_objdata.objectType == new_objdata.objectType
    assert updated_objdata.mainResource == new_objdata.mainResource

    assert updated_objdata.description == original_objdata.description


def test_merge_non_existent(objcsvfile: Path):
    "Should mergin to a non existing object should not merge but add the new object."
    ocf = ObjectCSVFile.from_csv(objcsvfile)
    # old_objdata = next(ocf.get_data("obj1"))
    # original_objdata = copy.deepcopy(old_objdata)
    new_objdata = ObjectData(
        recid="obj99",
        title="Updated title",
        project="Updated project",
        description="Update description with ÄÖÜ",
        creator="Upodated creator",
        rights="Updated rights",
        publisher="Updated publisher",
        source="Updated source",
        objectType="Updated objectType",
        mainResource="TEI2.xml",
    )
    updated_objdata = ocf.merge_object(new_objdata)

    # make sure we added the new object
    assert updated_objdata is new_objdata

    # Check if merge was applied correctly
    assert updated_objdata.title == new_objdata.title
    assert updated_objdata.project == new_objdata.project

    assert updated_objdata.creator == new_objdata.creator
    assert updated_objdata.rights == new_objdata.rights
    assert updated_objdata.publisher == new_objdata.publisher
    assert updated_objdata.source == new_objdata.source
    assert updated_objdata.objectType == new_objdata.objectType
    assert updated_objdata.mainResource == new_objdata.mainResource

    assert updated_objdata.description == new_objdata.description
