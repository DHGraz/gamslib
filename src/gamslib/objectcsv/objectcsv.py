"""Provides classes to handle object and datastream data in csv files.

The central class is ObjectCSV, which represents the object and datastream data.

ObjectCSV is directly accessible from the objectcsv package.
"""
# pylint: disable=too-many-instance-attributes
# pylint: disable=invalid-name

from collections import Counter
from dataclasses import InitVar, dataclass
from pathlib import Path
from typing import Generator

from gamslib.objectcsv.datastreamscsvfile import DatastreamsCSVFile
from gamslib.objectcsv.dsdata import DSData
from gamslib.objectcsv.objectcsvfile import ObjectCSVFile
from gamslib.objectcsv.objectdata import ObjectData


@dataclass
class ObjectCSV:
    """Represents the object and datastream data for a single object.

    The constructor expects the Path to the object directory.
    If the csv files are not set, we assume the default filenames:
    object.csv and datastreams.csv.
    """

    OBJECT_CSV_FILENAME = "object.csv"
    DATASTREAM_CSV_FILENAME = "datastreams.csv"

    object_dir: Path
    object_file: str = OBJECT_CSV_FILENAME
    datastream_file: str = DATASTREAM_CSV_FILENAME
    # set this to True to ignore existing csv files. This is useful when creating new objects
    # which then should be merged with what is already in the existing csv file
    ignore_existing_csv_files: InitVar[bool] = False

    def __post_init__(self, ignore_existing_csv_files: bool):
        """Check if the object directory exists and load the object and datastream data."""
        if not self.object_dir.is_dir():
            raise FileNotFoundError(
                f"Object directory '{self.object_dir}' does not exist."
            )

        self.obj_csv_file = self.object_dir / self.object_file
        self.ds_csv_file = self.object_dir / self.datastream_file

        if not ignore_existing_csv_files and self.obj_csv_file.is_file():
            self.object_data = ObjectCSVFile.from_csv(self.obj_csv_file)
        else:
            self.object_data = ObjectCSVFile()

        if not ignore_existing_csv_files and self.ds_csv_file.is_file():
            self.datastream_data = DatastreamsCSVFile.from_csv(self.ds_csv_file)
        else:
            self.datastream_data = DatastreamsCSVFile(self.object_dir)

    def is_new(self):
        """Return True if at least one of the csv files exist."""
        return not (self.obj_csv_file.exists() or self.ds_csv_file.exists())

    def add_datastream(self, dsdata: DSData):
        """Add a datastream to the object."""
        self.datastream_data.add_datastream(dsdata)

    def update_datastreams(self, datastreams: list[DSData]):
        """Update the datastream data."""
        # step 1: remove all datastreams, which are no longer in object
        new_datastream_ids = [(ds.dspath, ds.dsid) for ds in datastreams]
        for dsdata in self.get_datastreamdata():
            if (dsdata.dspath, dsdata.dsid) not in new_datastream_ids:
                self.datastream_data.remove_datastream(dsdata.dspath, dsdata.dsid)

        # step 2: merge all existing datastreams
        for datastream in datastreams:
            self.datastream_data.merge_datastream(datastream)

    def add_objectdata(self, objectdata: ObjectData):
        """Add a object to the object."""
        self.object_data.add_objectdata(objectdata)

    def update_objectdata(self, objectdata: ObjectData):
        """Update the object data."""
        self.object_data.merge_object(objectdata)

    def get_objectdata(
        self, pid: str | None = None
    ) -> Generator[ObjectData, None, None]:
        """Return the object data for a given object pid.

        If pid is None, return all object data.
        """
        return self.object_data.get_data(pid)

    def get_datastreamdata(self, pid: str = "all") -> Generator[DSData, None, None]:
        """Return the datastream data for a given object pid.

        If pid is None, return all datastream data (not just for a single object).
        """
        return self.datastream_data.get_datastreams(pid)

    def sort(self):
        """Sort the object and datastream data."""
        self.object_data.sort()
        self.datastream_data.sort()

    def write(
        self,
        object_csv_path: Path | None = None,
        datastream_csv_path: Path | None = None,
    ):
        """Save the object and datastream data to csv files.

        If no explicit output files are set, we use the default filenames and write to object_dir.
        """
        if object_csv_path is None:
            object_csv_path = self.obj_csv_file
        if datastream_csv_path is None:
            datastream_csv_path = self.ds_csv_file
        self.object_data.to_csv(object_csv_path)
        self.datastream_data.to_csv(datastream_csv_path)

    def count_objects(self) -> int:
        """Return the number of object data objects."""
        return len(self.object_data)

    def count_datastreams(self) -> int:
        """Return the number of datastream data objects."""
        return len(self.datastream_data)

    def clear(self):
        """Clear the object and datastream data."""
        self.object_data = ObjectCSVFile()
        self.datastream_data = DatastreamsCSVFile(self.object_dir)

    @property
    def object_id(self):
        """Return the object id."""
        return self.object_dir.name

    def get_languages(self):
        """Return the languages of the datastreams ordered by frequency."""
        langcounter = Counter(self.datastream_data.get_languages())
        return [entry[0] for entry in langcounter.most_common()]
