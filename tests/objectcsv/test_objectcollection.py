import copy
import csv
from dataclasses import asdict
import pytest
from pathlib import Path
from gamslib.objectcsv.objectcollection import ObjectCollection, ALL_OBJECTS_CSV, ALL_DATASTREAMS_CSV
from gamslib.objectcsv.objectdata import ObjectData
from gamslib.objectcsv.dsdata import DSData

@pytest.fixture
def objcollection(tmp_path):
    return ObjectCollection()

@pytest.fixture
def populated_objcollection(objdata, dsdata):
    """Fixture for a populated ObjectCollection. 
    
    Contains two objects (obj1 and obj2).
    obj1 has two datastreams (ds1, ds2)
    obj2 has one datastream (ds3).
    
    """
    objdata2 = copy.deepcopy(objdata) 
    objdata2.recid = "obj2"

    dsdata.dsid = "DC.xml"
    dsdata.dspath = "obj1/DC.xml"
    dsdata2 = copy.deepcopy(dsdata)
    dsdata2.dsid = "TEI2.xml"
    dsdata2.dspath = "obj1/TEI2.xml"
    
    dsdata3 = copy.deepcopy(dsdata)
    dsdata3.dsid = "TEI3.xml"
    dsdata3.dspath = "obj2/TEI3.xml"

    objcollection = ObjectCollection()
    objcollection.objects["obj1"] = objdata
    objcollection.datastreams["obj1"] = [dsdata, dsdata2]
    objcollection.objects["obj2"] = objdata2
    objcollection.datastreams["obj2"] = [dsdata3]
    return objcollection

@pytest.fixture
def populated_dir(tmp_path, populated_objcollection):
    """Fixture for a populated directory with object and datastream csv files.
    
    
    Creates two directories (obj1 and obj2) with object.csv and datastreams.csv files.
    Uses data from populated_objectcollection fixture.
    """
    obj1_dir = tmp_path / "obj1"
    obj1_dir.mkdir(parents=True, exist_ok=True)
    obj2_dir = tmp_path / "obj2"
    obj2_dir.mkdir(parents=True, exist_ok=True)
    (obj1_dir / "DC.xml").touch()  # Create a dummy DC.xml file
    (obj2_dir / "DC.xml").touch()  # Create a dummy DC.xml file

    # Create object.csv for obj1
    obj1_obj_csv = obj1_dir / "object.csv"
    with obj1_obj_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ObjectData.fieldnames())
        writer.writeheader()
        writer.writerow(asdict(populated_objcollection.objects["obj1"]))

    # Create datastreams.csv for obj1
    obj1_ds_csv = obj1_dir / "datastreams.csv"
    with obj1_ds_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=DSData.fieldnames())
        writer.writeheader()
        for dsdata in populated_objcollection.datastreams["obj1"]:
            writer.writerow(asdict(dsdata))

    # Create object.csv for obj2
    obj2_obj_csv = obj2_dir / "object.csv"
    with obj2_obj_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ObjectData.fieldnames())
        writer.writeheader()
        writer.writerow(asdict(populated_objcollection.objects["obj2"]))

    # Create datastreams.csv for obj2
    obj2_ds_csv = obj2_dir / "datastreams.csv"
    with obj2_ds_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=DSData.fieldnames())
        writer.writeheader()
        for dsdata in populated_objcollection.datastreams["obj2"]:
            writer.writerow(asdict(dsdata))

    return tmp_path


def test_init(objcollection):
    assert objcollection.objects == {}
    assert objcollection.datastreams == {}

def test_collect_from_objects_with_missing_csvs(tmp_path, objcollection):
    """Test collecting objects from an empty directory."""
    # create a obj1 directory with only a DC.xml file (no csv files!)
    obj_dir = tmp_path / "obj1"
    obj_dir.mkdir(parents=True, exist_ok=True)
    dc_file = obj_dir / "DC.xml"
    dc_file.touch()

    # If collect_objects finds a object dir without csv files, ist should fail
    with pytest.raises(ValueError):
        objcollection.collect_from_objects(tmp_path)

def test_collect_from_objects(objcollection, populated_objcollection, populated_dir):
    """Test collecting objects from a populated directory."""
    # collect objects from the populated directory
    objcollection.collect_from_objects(populated_dir)
    assert objcollection.count_objects() == populated_objcollection.count_objects()
    assert "obj1" in objcollection.objects
    assert "obj2" in objcollection.objects

    assert objcollection.count_datastreams() == populated_objcollection.count_datastreams()
    assert "obj1" in objcollection.datastreams
    objcollection.collect_from_objects(populated_dir)
    assert objcollection.count_objects() == populated_objcollection.count_objects()
    assert "obj1" in objcollection.objects
    assert "obj2" in objcollection.objects


def test_save_to_csv(tmp_path, populated_objcollection):
    """Test saving objects and datastreams to CSV files."""
    obj_csv = tmp_path / ALL_OBJECTS_CSV
    ds_csv = tmp_path / ALL_DATASTREAMS_CSV

    obj_csv.unlink(missing_ok=True)  # Remove if exists
    ds_csv.unlink(missing_ok=True)  # Remove if exists

    populated_objcollection.save_to_csv(obj_csv, ds_csv)
    assert obj_csv.exists()
    assert ds_csv.exists()

    with obj_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == len(['obj1', 'obj2'])  
        assert rows[0]["recid"] == "obj1"
        assert rows[1]["recid"] == "obj2"

    with ds_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == len(populated_objcollection.datastreams["obj1"]) + len(populated_objcollection.datastreams["obj2"])
        dspaths = [row["dspath"] for row in rows        ]
        assert "obj1/DC.xml" in dspaths
        assert "obj1/TEI2.xml" in dspaths
        assert "obj2/TEI3.xml" in dspaths

def test_load_from_csv(populated_objcollection, tmp_path, objcollection):
    """Test loading objects and datastreams from CSV files."""
    # create the csv files to be read
    obj_csv = tmp_path / ALL_OBJECTS_CSV
    ds_csv = tmp_path / ALL_DATASTREAMS_CSV
    populated_objcollection.save_to_csv(obj_csv, ds_csv)

    objcollection.load_from_csv(obj_csv, ds_csv)
    assert len(objcollection.objects) == len(['obj1', 'obj2'])
    assert len(objcollection.datastreams) == len(populated_objcollection.datastreams)
    assert objcollection.count_objects() == populated_objcollection.count_objects()
    assert objcollection.count_datastreams() == populated_objcollection.count_datastreams()

def test_save_to_xlsx(tmp_path, populated_objcollection):
    """Test saving objects and datastreams to a single XLSX file."""
    #objcollection.objects["obj1"] = objdata
    #objcollection.datastreams["obj1"] = [dsdata_fixture]
    populated_objcollection.save_to_xlsx(tmp_path / "all_objects.xlsx") 
    assert (tmp_path / "all_objects.xlsx").exists()

def test_load_from_xlsx(tmp_path, populated_objcollection):
    """Test loading objects and datastreams from a single XLSX file."""
    # generate xslx test file
    populated_objcollection.save_to_xlsx(tmp_path / "all_objects.xlsx")

    objcollection = ObjectCollection()
    objcollection.load_from_xlsx(tmp_path / "all_objects.xlsx")
    assert len(objcollection.objects) == len(['obj1', 'obj2'])
    assert len(objcollection.datastreams) == len(populated_objcollection.datastreams)
    recids = [obj.recid for obj in objcollection.objects.values()]
    assert set(recids) == set(['obj1', 'obj2']) 
    dsids = [ds.dsid for ds in objcollection.datastreams["obj1"]] + [ds.dsid for ds in objcollection.datastreams["obj2"]]
    assert set(dsids) == set(['DC.xml', 'TEI2.xml', 'TEI3.xml'])
    