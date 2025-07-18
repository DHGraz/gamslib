"Tests for the ObjectData class."

import copy
import csv

import pytest



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





@pytest.mark.parametrize(
    "fieldname, old_value, new_value, expected_value",
    [
        ("title", "Old title", "New title", "New title"),
        ("title", "", "New title", "New title"),
        ("title", "Old title", "", "Old title"),
        ("project", "Old project", "New project", "New project"),
        ("project", "", "New project", "New project"),
        ("project", "Old project", "", "Old project"),
        ("creator", "Old creator", "New creator", "New creator"),
        ("creator", "", "New creator", "New creator"),
        ("creator", "Old creator", "", "Old creator"),
        ("rights", "Old rights", "New rights", "New rights"),
        ("rights", "", "New rights", "New rights"),
        ("rights", "Old rights", "", "Old rights"),
        ("publisher", "Old publisher", "New publisher", "New publisher"),
        ("publisher", "", "New publisher", "New publisher"),
        ("publisher", "Old publisher", "", "Old publisher"),
        ("source", "Old source", "New source", "New source"),
        ("source", "", "New source", "New source"),
        ("source", "Old source", "", "Old source"),
        ("objectType", "Old objectType", "New objectType", "New objectType"),
        ("objectType", "", "New objectType", "New objectType"),
        ("objectType", "Old objectType", "", "Old objectType"),
        ("mainResource", "Old mainResource", "New mainResource", "New mainResource"),
        ("mainResource", "", "New mainResource", "New mainResource"),
        ("mainResource", "Old mainResource", "", "Old mainResource"),
        ("funder", "Old funder", "New funder", "New funder"),
        ("funder", "", "New funder", "New funder"),
        ("funder", "Old funder", "", "Old funder"),
        # description should not be touched
        ("description", "Old description", "New description", "Old description"),
        # changed recid should raise an exception
        ("recid", "obj2", "obj3", "ValueError"),
    ],
)
def test_objectdata_merge(objdata, fieldname, old_value, new_value, expected_value):
    "Should merge two ObjectData objects."
    new_objdata = copy.deepcopy(objdata)

    setattr(objdata, fieldname, old_value)
    setattr(new_objdata, fieldname, new_value)

    if expected_value == "ValueError":
        with pytest.raises(ValueError):
            objdata.merge(new_objdata)
    else:
        objdata.merge(new_objdata)
        assert getattr(objdata, fieldname) == expected_value


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
