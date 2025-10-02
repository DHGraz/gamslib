import copy
import csv
from dataclasses import asdict
import pytest
from gamslib.objectcsv.objectcollection import (
    ObjectCollection,
    ALL_OBJECTS_CSV,
    ALL_DATASTREAMS_CSV,
)
from gamslib.objectcsv.objectdata import ObjectData
from gamslib.objectcsv.dsdata import DSData


@pytest.fixture(name="objcollection")
def objcollection_fixture():
    """Fixture for an empty ObjectCollection."""
    return ObjectCollection()


@pytest.fixture(name="populated_objcollection")
def populated_objcollection_fixture(objdata, dsdata):
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
    """Test initialization of an empty ObjectCollection."""
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

    assert (
        objcollection.count_datastreams() == populated_objcollection.count_datastreams()
    )
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
        assert len(rows) == len(["obj1", "obj2"])
        assert rows[0]["recid"] == "obj1"
        assert rows[1]["recid"] == "obj2"

    with ds_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == len(populated_objcollection.datastreams["obj1"]) + len(
            populated_objcollection.datastreams["obj2"]
        )
        dspaths = [row["dspath"] for row in rows]
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
    assert len(objcollection.objects) == len(["obj1", "obj2"])
    assert len(objcollection.datastreams) == len(populated_objcollection.datastreams)
    assert objcollection.count_objects() == populated_objcollection.count_objects()
    assert (
        objcollection.count_datastreams() == populated_objcollection.count_datastreams()
    )


def test_save_to_xlsx(tmp_path, populated_objcollection):
    """Test saving objects and datastreams to a single XLSX file."""
    # objcollection.objects["obj1"] = objdata
    # objcollection.datastreams["obj1"] = [dsdata_fixture]
    populated_objcollection.save_to_xlsx(tmp_path / "all_objects.xlsx")
    assert (tmp_path / "all_objects.xlsx").exists()


def test_load_from_xlsx(tmp_path, populated_objcollection):
    """Test loading objects and datastreams from a single XLSX file."""
    # generate xslx test file
    populated_objcollection.save_to_xlsx(tmp_path / "all_objects.xlsx")

    objcollection = ObjectCollection()
    objcollection.load_from_xlsx(tmp_path / "all_objects.xlsx")
    assert len(objcollection.objects) == len(["obj1", "obj2"])
    assert len(objcollection.datastreams) == len(populated_objcollection.datastreams)
    recids = [obj.recid for obj in objcollection.objects.values()]
    assert set(recids) == set(["obj1", "obj2"])
    dsids = [ds.dsid for ds in objcollection.datastreams["obj1"]] + [
        ds.dsid for ds in objcollection.datastreams["obj2"]
    ]
    assert set(dsids) == set(["DC.xml", "TEI2.xml", "TEI3.xml"])


def test_distribute_to_objects_updates_files(tmp_path, populated_objcollection):
    """Test that distribute_to_objects writes correct object.csv and datastreams.csv files."""
    # Prepare directories for obj1 and obj2
    obj1_dir = tmp_path / "obj1"
    obj2_dir = tmp_path / "obj2"
    obj1_dir.mkdir()
    obj2_dir.mkdir()
    # Place dummy files to simulate object folders
    (obj1_dir / "DC.xml").touch()
    (obj2_dir / "DC.xml").touch()

    # Distribute metadata to these directories
    updated_objects, updated_datastreams = (
        populated_objcollection.distribute_to_objects(tmp_path)
    )
    assert updated_objects == 2
    assert updated_datastreams == 3

    # Check object.csv for obj1
    with (obj1_dir / "object.csv").open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["recid"] == "obj1"

    # Check datastreams.csv for obj1
    with (obj1_dir / "datastreams.csv").open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        dspaths = [row["dspath"] for row in rows]
        assert set(dspaths) == set(["obj1/DC.xml", "obj1/TEI2.xml"])

    # Check object.csv for obj2
    with (obj2_dir / "object.csv").open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["recid"] == "obj2"

    # Check datastreams.csv for obj2
    with (obj2_dir / "datastreams.csv").open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        dspaths = [row["dspath"] for row in rows]
        assert dspaths == ["obj2/TEI3.xml"]


def test_distribute_to_objects_missing_directory(populated_objcollection, tmp_path):
    """Test that distribute_to_objects raises UserWarning if an object directory is missing."""
    # Only create obj1 directory, not obj2
    obj1_dir = tmp_path / "obj1"
    obj1_dir.mkdir()
    (obj1_dir / "DC.xml").touch()

    # Remove obj2 from datastreams to avoid writing to missing dir
    # (simulate only obj1 present)
    populated_objcollection.objects = {
        "obj1": populated_objcollection.objects["obj1"],
        "obj2": populated_objcollection.objects["obj2"],
    }
    populated_objcollection.datastreams = {
        "obj1": populated_objcollection.datastreams["obj1"],
        "obj2": populated_objcollection.datastreams["obj2"],
    }

    # Should raise UserWarning for obj2
    with pytest.raises(UserWarning):
        populated_objcollection.distribute_to_objects(tmp_path)


def test_load_from_csv_missing_obj_file(tmp_path, objcollection):
    """Test that load_from_csv raises FileNotFoundError if object CSV is missing."""
    ds_csv = tmp_path / ALL_DATASTREAMS_CSV
    # Create only datastreams.csv
    with ds_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=DSData.fieldnames())
        writer.writeheader()
    # obj_file does not exist
    with pytest.raises(FileNotFoundError):
        objcollection.load_from_csv(tmp_path / ALL_OBJECTS_CSV, ds_csv)


def test_load_from_csv_missing_ds_file(tmp_path, objcollection):
    """Test that load_from_csv raises FileNotFoundError if datastreams CSV is missing."""
    obj_csv = tmp_path / ALL_OBJECTS_CSV
    # Create only object.csv
    with obj_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ObjectData.fieldnames())
        writer.writeheader()
    # ds_file does not exist
    with pytest.raises(FileNotFoundError):
        objcollection.load_from_csv(obj_csv, tmp_path / ALL_DATASTREAMS_CSV)


def test_load_from_csv_clears_existing_data(populated_objcollection, tmp_path):
    """Test that load_from_csv clears existing objects and datastreams before loading."""
    obj_csv = tmp_path / ALL_OBJECTS_CSV
    ds_csv = tmp_path / ALL_DATASTREAMS_CSV
    # Save current data to CSV
    populated_objcollection.save_to_csv(obj_csv, ds_csv)
    # Add extra data to collection
    populated_objcollection.objects["extra"] = ObjectData(**{k: "" for k in ObjectData.fieldnames()})
    populated_objcollection.datastreams["extra"] = []
    assert "extra" in populated_objcollection.objects
    # Load from CSV, should clear "extra"
    populated_objcollection.load_from_csv(obj_csv, ds_csv)
    assert "extra" not in populated_objcollection.objects
    assert "extra" not in populated_objcollection.datastreams


def test_load_from_csv_populates_objects_and_datastreams(tmp_path, objcollection, populated_objcollection):
    """Test that load_from_csv correctly populates objects and datastreams from CSV files."""
    obj_csv = tmp_path / ALL_OBJECTS_CSV
    ds_csv = tmp_path / ALL_DATASTREAMS_CSV
    # Save reference data to CSV
    populated_objcollection.save_to_csv(obj_csv, ds_csv)
    # Load into empty collection
    objcollection.load_from_csv(obj_csv, ds_csv)
    assert objcollection.count_objects() == populated_objcollection.count_objects()
    assert objcollection.count_datastreams() == populated_objcollection.count_datastreams()
    for obj_id in populated_objcollection.objects:
        assert obj_id in objcollection.objects
    for obj_id in populated_objcollection.datastreams:
        assert obj_id in objcollection.datastreams
        assert len(objcollection.datastreams[obj_id]) == len(populated_objcollection.datastreams[obj_id])
def test_load_from_xlsx_missing_file(objcollection, tmp_path):
    """Test that load_from_xlsx raises FileNotFoundError if XLSX file does not exist."""
    missing_xlsx = tmp_path / "nonexistent.xlsx"
    with pytest.raises(FileNotFoundError):
        objcollection.load_from_xlsx(missing_xlsx)


def test_load_from_xlsx_populates_data(tmp_path, populated_objcollection):
    """Test that load_from_xlsx correctly loads data from XLSX file."""
    # Save reference data to XLSX
    xlsx_file = tmp_path / "all_objects.xlsx"
    populated_objcollection.save_to_xlsx(xlsx_file)
    # Load into a new collection
    objcollection = ObjectCollection()
    objcollection.load_from_xlsx(xlsx_file)
    assert objcollection.count_objects() == populated_objcollection.count_objects()
    assert objcollection.count_datastreams() == populated_objcollection.count_datastreams()
    for obj_id in populated_objcollection.objects:
        assert obj_id in objcollection.objects
    for obj_id in populated_objcollection.datastreams:
        assert obj_id in objcollection.datastreams
        assert len(objcollection.datastreams[obj_id]) == len(populated_objcollection.datastreams[obj_id])


def test_load_from_xlsx_clears_existing_data(tmp_path, populated_objcollection):
    """Test that load_from_xlsx clears existing data before loading new data."""
    xlsx_file = tmp_path / "all_objects.xlsx"
    populated_objcollection.save_to_xlsx(xlsx_file)
    # Add extra data
    populated_objcollection.objects["extra"] = ObjectData(**{k: "" for k in ObjectData.fieldnames()})
    populated_objcollection.datastreams["extra"] = []
    assert "extra" in populated_objcollection.objects
    # Load from XLSX, should clear "extra"
    populated_objcollection.load_from_xlsx(xlsx_file)
    assert "extra" not in populated_objcollection.objects
    assert "extra" not in populated_objcollection.datastreams


