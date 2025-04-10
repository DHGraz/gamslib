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

def test_objectdata_merge(objdata):
    "Should merge two ObjectData objects."
    new_objdata = copy.deepcopy(objdata)
    original_objdata = copy.deepcopy(objdata)
    #['title', 'project', 'creator', 'rights', 'publisher', 'source', 'objectType', 'funder']

    new_objdata.title = "Updated title"
    new_objdata.project = "Updated project"
    new_objdata.creator = "Updated creator"
    new_objdata.rights = "Updated rights"
    new_objdata.publisher = "Updated publisher"
    new_objdata.source = "Updated source"
    new_objdata.objectType = "Updated objectType"
    new_objdata.mainResource = "Updated mainResource"
    new_objdata.funder = "Updated funder"

    # and now some more changed fields, which should be ignored
    new_objdata.description = "Updated description"
    new_objdata.mainResource = "Updated mainResource"

    objdata.merge(new_objdata)
    assert objdata.title == new_objdata.title
    assert objdata.project == new_objdata.project
    assert objdata.creator == new_objdata.creator
    assert objdata.rights == new_objdata.rights
    assert objdata.publisher == new_objdata.publisher
    assert objdata.source == new_objdata.source
    assert objdata.objectType == new_objdata.objectType
    assert objdata.funder == new_objdata.funder
    assert objdata.mainResource == new_objdata.mainResource

    # check that the other fields are not changed
    assert objdata.recid == original_objdata.recid
    assert objdata.description == original_objdata.description
    
    

def test_objectdata_merge_empty(objdata):
    "Empty fields should not be merged."
    new_objdata = copy.deepcopy(objdata)
    original_objdata = copy.deepcopy(objdata)
    #['title', 'project', 'creator', 'rights', 'publisher', 'source', 'objectType', 'funder']

    new_objdata.title = ""
    new_objdata.project = ""
    new_objdata.creator = ""
    new_objdata.rights = ""
    new_objdata.publisher = ""
    new_objdata.source = ""
    new_objdata.objectType = ""
    new_objdata.mainResource = ""
    new_objdata.funder = ""

    # and now some more changed fields, which should be ignored
    new_objdata.description = ""
    

    objdata.merge(new_objdata)
    assert objdata.title == original_objdata.title
    assert objdata.project == original_objdata.project
    assert objdata.creator == original_objdata.creator
    assert objdata.rights == original_objdata.rights
    assert objdata.publisher == original_objdata.publisher
    assert objdata.source == original_objdata.source
    assert objdata.objectType == original_objdata.objectType
    assert objdata.funder == original_objdata.funder
    assert objdata.mainResource == original_objdata.mainResource
   
    assert objdata.recid == original_objdata.recid
    assert objdata.description == original_objdata.description
    

def test_objectdata_merge_different_recid(objdata):
    "Should raise an exception if recid is different."
    new_objdata = copy.deepcopy(objdata)
    new_objdata.recid = "obj2"
    with pytest.raises(ValueError):
        objdata.merge(new_objdata)
    
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

