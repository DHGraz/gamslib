"""Collect csv info from multiple objects into two csv or a single xlsx file.

This module provides the `ObjectCollection` class to manage and manipulate collections
of GAMS objects and their associated datastreams.
It allows for collecting, saving, and loading data from CSV and XLSX formats.
"""

import csv
from dataclasses import asdict
from pathlib import Path
import tempfile
from gamslib.objectcsv import xlsx
from gamslib.objectcsv.dsdata import DSData
from gamslib.objectcsv.objectdata import ObjectData
from gamslib.objectcsv.objectcsvmanager import ObjectCSVManager
from gamslib.objectcsv.utils import find_object_folders

ALL_OBJECTS_CSV = "all_objects.csv"
ALL_DATASTREAMS_CSV = "all_datastreams.csv"
ALL_OBJECTS_XLSX = "all_objects.xlsx"


class ObjectCollection:
    """Represents a collection of CSV data for any number of GAMS objects.

    This is only used to collect data from multiple objects into a single csv/xslx file.
    """

    def __init__(self):
        self.objects: dict[str, ObjectData] = {}  # keys are recids (pid)
        self.datastreams: dict[str, list[DSData]] = {}  # keys are object ids (recids)

    def collect_from_objects(self, root_dir: Path) -> None:
        """Collect csv data from all object dirs below root_dir.

        Raises a ValueError if the object metadata (csv) is not set for any object directory.
        """
        for obj_dir in find_object_folders(root_dir):
            object_meta = ObjectCSVManager(obj_dir)
            if object_meta.is_empty():
                raise ValueError(
                    f"Object metadata (csv) is not set for {obj_dir}. "
                    "Please check the object directory."
                )
            self.objects[obj_dir.name] = object_meta.get_object()
            for dsdata in object_meta.get_datastreamdata():
                if obj_dir.name not in self.datastreams:
                    self.datastreams[obj_dir.name] = []
                self.datastreams[obj_dir.name].append(dsdata)

    def distribute_to_objects(self, root_dir: Path) -> tuple[int, int]:
        """Distribute the collected data to the individual object directories.

        This will update the object.csv and datastreams.csv files in each object directory.

        It is expected that all object directories are direct subdirectories of root_dir.

        Returns a tuple of ints: number of updated objects and number of updated datastreams.
        Raises a UserWarning if an object directory does not exist.
        """
        updated_objects_counter = 0
        updated_datastreams_counter = 0
        for obj_id, obj_data in self.objects.items():
            obj_dir = root_dir / obj_id
            if obj_dir.is_dir():
                obj_mgr = ObjectCSVManager(obj_dir, ignore_existing_csv_files=True)
                obj_mgr.set_object(obj_data, replace=True)
                updated_objects_counter += 1
                for dsdata in self.datastreams.get(obj_id, []):
                    obj_mgr.add_datastream(dsdata, replace=True)
                    updated_datastreams_counter += 1
                obj_mgr.save()
            else:
                raise UserWarning(
                    f"Object directory {obj_dir} does not exist. Skipping."
                )
        return updated_objects_counter, updated_datastreams_counter

    def count_objects(self) -> int:
        """Return the number of objects in the collection."""
        return len(self.objects)

    def count_datastreams(self) -> int:
        """Return the number of datastreams in the collection."""
        return sum(len(ds) for ds in self.datastreams.values())

    def save_to_csv(
        self, obj_file: Path | None = None, ds_file: Path | None = None
    ) -> None:
        """Save data to two csv file (object.csv and datastreams.csv).

        If obj_file is None, it defaults to object.csv in the current directory.
        If ds_file is None, it defaults to datastreams.csv in the current directory.
        """
        obj_file = obj_file or Path(ALL_OBJECTS_CSV)
        ds_file = ds_file or Path(ALL_DATASTREAMS_CSV)
        with obj_file.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=ObjectData.fieldnames())
            writer.writeheader()
            for obj in self.objects.values():
                writer.writerow(asdict(obj))
        with ds_file.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=DSData.fieldnames())
            writer.writeheader()
            for datastreams in self.datastreams.values():
                # ) in self.datastreams.items():  # dsdata in self.datastreams:
                for dsdata in datastreams:
                    writer.writerow(asdict(dsdata))

    def save_to_xlsx(self, xlsx_file: Path | None = None) -> None:
        """Save data to a single xlsx file with two sheets (objects and datastreams).

        If xlsx_file is None, it defaults to all_objects.xlsx in the current directory.
        """
        xlsx_file = xlsx_file or Path(ALL_OBJECTS_XLSX)
        with tempfile.TemporaryDirectory() as tmpdir:
            obj_file = Path(tmpdir) / ALL_OBJECTS_CSV
            ds_file = Path(tmpdir) / ALL_DATASTREAMS_CSV
            self.save_to_csv(obj_file, ds_file)
            xlsx.csv_to_xlsx(obj_file, ds_file, xlsx_file)

    def load_from_csv(
        self, obj_file: Path | None = None, ds_file: Path | None = None
    ) -> None:
        """Load data from two csv files (object.csv and datastreams.csv).

        If obj_file is None, it defaults to object.csv in the current directory.
        If ds_file is None, it defaults to datastreams.csv in the current directory.
        """
        obj_file = obj_file or Path(ALL_OBJECTS_CSV)
        ds_file = ds_file or Path(ALL_DATASTREAMS_CSV)
        if not obj_file.is_file():
            raise FileNotFoundError(f"Required csv file {obj_file} does not exist.")
        if not ds_file.is_file():
            raise FileNotFoundError(f"Required csv file {ds_file} does not exist.")
        self.objects.clear()
        self.datastreams.clear()

        with obj_file.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                obj_data = ObjectData(**row)
                self.objects[obj_data.recid] = obj_data

        with ds_file.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ds_data = DSData(**row)
                obj_id = ds_data.dspath.split("/")[0]  # Extract object id from dspath
                if obj_id not in self.datastreams:
                    self.datastreams[obj_id] = []
                self.datastreams[obj_id].append(ds_data)

    def load_from_xlsx(self, xlsx_file: Path | None = None) -> None:
        """Load data from a single xlsx file with two sheets (objects and datastreams).

        If xlsx_file is None, it defaults to all_objects.xlsx in the current directory.
        """
        xlsx_file = xlsx_file or Path(ALL_OBJECTS_XLSX)

        if not xlsx_file.is_file():
            raise FileNotFoundError(f"File {xlsx_file} does not exist.")
        with tempfile.TemporaryDirectory() as tmpdir:
            obj_file = Path(tmpdir) / ALL_OBJECTS_CSV
            ds_file = Path(tempfile.tempdir) / ALL_DATASTREAMS_CSV
            xlsx.xlsx_to_csv(xlsx_file, obj_file, ds_file)
            self.load_from_csv(obj_file, ds_file)
