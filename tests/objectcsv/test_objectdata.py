"Tests for the ObjectData class."
import copy
import csv
from pathlib import Path
import pytest
from gamslib.objectcsv.objectcsvfile import ObjectCSVFile
from gamslib.objectcsv.objectdata import ObjectData
from gamslib.objectcsv.dublincore import DublinCore



def test_objectdata_creation(objdata):
    "Should create an ObjectData object."
    assert objdata.recid == "obj1"
    assert objdata.title == "The title"
    assert objdata.project == "The project"
    assert objdata.description == "The description with ÄÖÜ"
    assert objdata.creator == "The creator"
    assert objdata.rights == "The rights"
    assert objdata.publisher == "The publisher"
    assert objdata.source == "The source"
    assert objdata.objectType == "The objectType"
    assert objdata.mainResource == "TEI.xml"


def test_fix_for_mainresource(tmp_path):
    """mainresource was renamed to mainResource.

    Wee added code which still works with the old name, but uses the new name.
    This test makes sure that it works like expected.
    """
    obj_dict = {
        'recid': "obj1",
        'title': "The title",
        'project': "The project",
        'description': "The description with ÄÖÜ",
        'creator': "The creator",
        'rights': "The rights",
        'publisher': "The publisher",
        'source': "The source",
        'objectType': "The objectType",
        'mainresource': "TEI.xml",
    }
    # write test data to file
    csv_file = tmp_path / "object.csv"
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(obj_dict.keys()))
        writer.writeheader()
        writer.writerow(obj_dict)
    
    data = ObjectCSVFile.from_csv(csv_file)
    assert next(data.get_data()).mainResource == "TEI.xml"

@pytest.mark.skip
def test_objectdata_merge(objdata):
    "Should merge two ObjectData objects."
    objdata2 = copy.deepcopy(objdata)
    #['title', 'project', 'creator', 'rights', 'publisher', 'source', 'objectType', 'funder']
    objdata2.title = "The title 2"
    objdata2.project = "The project 2"
    objdata2.creator = "The creator 2"
    objdata2.rights = "The rights 2"
    objdata2.publisher = "The publisher 2"
    objdata2.source = "The source 2"
    objdata2.objectType = "The objectType 2"
    objdata2.funder = "The funder 2"

    objdata.merge(objdata2)
    assert objdata.title == "The title 2"
    assert objdata.project == "The project 2"
    assert objdata.description == "The description with ÄÖÜ"
    assert objdata.creator == "The creator 2"
    assert objdata.rights == "The rights 2"
    assert objdata.publisher == "The publisher 2"
    assert objdata.source == "The source 2"
    assert objdata.objectType == "The objectType 2"
    assert objdata.mainResource == "TEI.xml"
    assert objdata.funder == "The funder 2"

    
def test_objectdata_validate(objdata):
    "Should raise an exception if required fields are missing."
    objdata.recid = ""
    with pytest.raises(ValueError):
        objdata.validate()
    objdata.recid = "obj1"
    objdata.title = ""
    with pytest.raises(ValueError):
        objdata.validate()
    objdata.title = "The title"
    objdata.rights = ""
    with pytest.raises(ValueError):
        objdata.validate()
    objdata.rights = "The rights"
    objdata.source = ""
    with pytest.raises(ValueError):
        objdata.validate()
    objdata.source = "The source"
    objdata.objectType = ""
    with pytest.raises(ValueError):
        objdata.validate()

