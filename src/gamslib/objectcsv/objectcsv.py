"""Provides classes to handle object and datastream data in csv files.

The central class is ObjectCSV, which represents the object and datastream data.

ObjectCSV is directly accessible from the objectcsv package.
"""
# pylint: disable=too-many-instance-attributes
# pylint: disable=invalid-name

import csv
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Generator


@dataclass
class ObjectData:
    "Represents csv data for a single object."

    recid: str
    title: str = ""
    project: str = ""
    description: str = ""
    creator: str = ""
    rights: str = ""
    publisher: str = ""
    source: str = ""
    objectType: str = ""

    def validate(self):
        "Validate the object data."
        # TODO: Needs discussion
        if not self.recid:
            raise ValueError("recid must not be empty")
        if not self.title:
            raise ValueError(f"{self.recid}: title must not be empty")
        if not self.rights:
            raise ValueError(f"{self.recid}: rights must not be empty")
        if not self.source:
            raise ValueError(f"{self.recid}: source must not be empty")
        if not self.objectType:
            raise ValueError(f"{self.recid}: objectType must not be empty")


@dataclass
class DSData:
    "Represents csv data for a single datastream of a single object."

    dspath: str
    dsid: str = ""
    title: str = ""
    description: str = ""
    mimetype: str = ""
    creator: str = ""
    rights: str = ""

    @property
    def object_id(self):
        "Return the object id."
        return Path(self.dspath).parts[0]

    def validate(self):
        "Validate the datastream data."
        if not self.dspath.strip():
            raise ValueError(f"{self.dsid}: dspath must not be empty")
        if not self.dsid.strip():
            raise ValueError(f"{self.dspath}: dsid must not be empty")
        if not self.mimetype.strip():
            raise ValueError(f"{self.dspath}: mimetype must not be empty")
        if not self.rights.strip():
            raise ValueError(f"{self.dspath}: rights must not be empty")


@dataclass
class ObjectCSVFile:
    "Represents csv data for a single object."

    def __init__(self):
        self._objectdata: list[ObjectData] = []

    def add_objectdata(self, objectdata: ObjectData):
        "Add a ObjectData objects."
        self._objectdata.append(objectdata)

    def get_data(self, pid: str | None = None) -> Generator[ObjectData, None, None]:
        """Return the objectdata objects for a given object pid.

        If pid is None, return all objectdata objects.
        Filtering by pid is only needed if we have data from multiple objects.
        """
        for objdata in self._objectdata:
            if pid is None:
                yield objdata
            else:
                if objdata.recid == pid:
                    yield objdata

    @classmethod
    def from_csv(cls, csv_file: Path) -> "ObjectCSVFile":
        "Load the object data from a csv file."
        obj_csv_file = ObjectCSVFile()
        with csv_file.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                obj_csv_file.add_objectdata(ObjectData(**row))
        return obj_csv_file

    def to_csv(self, csv_file: Path) -> None:
        "Save the object data to a csv file."
        with csv_file.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=[field.name for field in fields(ObjectData)]
            )
            writer.writeheader()
            for objdata in self._objectdata:
                writer.writerow(asdict(objdata))

    def __len__(self):
        "Return the number of objectdata objects."
        return len(self._objectdata)


class DatastreamsCSVFile:
    "Represents csv data for all datastreams of a single datastream."

    def __init__(self):
        self._datastreams: list[DSData] = []

    def add_datastream(self, dsdata: DSData):
        "Add a datastream to the datastreams."
        self._datastreams.append(dsdata)

    def get_data(self, pid: str | None = None) -> Generator[DSData, None, None]:
        """Return the datastream objects for a given object pid.

        If pid is None, return all datastream objects.
        Filtering by pid is only needed if we have data from multiple objects.
        """
        for dsdata in self._datastreams:
            if pid is None:
                yield dsdata
            else:  # DOTO: this is not object_id!
                if dsdata.object_id == pid:
                    yield dsdata

    @classmethod
    def from_csv(cls, csv_file: Path) -> "DatastreamsCSVFile":
        "Load the datastream container data from a csv file."
        ds_csv_file = DatastreamsCSVFile()
        with csv_file.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ds_csv_file.add_datastream(DSData(**row))
        return ds_csv_file

    def to_csv(self, csv_file: Path):
        "Save the datastream data to a csv file."
        self._datastreams.sort(key=lambda x: x.dspath)
        with csv_file.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=[field.name for field in fields(DSData)]
            )
            writer.writeheader()
            for dsdata in self._datastreams:
                writer.writerow(asdict(dsdata))

    def __len__(self):
        "Return the number of datastreams."
        return len(self._datastreams)


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

    def __post_init__(self):
        "Check if the object directory exists and load the object and datastream data."
        if not self.object_dir.is_dir():
            raise FileNotFoundError(
                f"Object directory '{self.object_dir}' does not exist."
            )

        self.obj_csv_file = self.object_dir / self.object_file
        self.ds_csv_file = self.object_dir / self.datastream_file

        if self.obj_csv_file.is_file():
            self.object_data = ObjectCSVFile.from_csv(self.obj_csv_file)
        else:
            self.object_data = ObjectCSVFile()

        if self.ds_csv_file.is_file():
            self.datastream_data = DatastreamsCSVFile.from_csv(self.ds_csv_file)
        else:
            self.datastream_data = DatastreamsCSVFile()

    def is_new(self):
        "Return True if at least one of the csv files exist."
        # obj_csv = self.object_dir / self.OBJECT_CSV_FILENAME
        # ds_csv = self.object_dir / self.DATASTREAM_CSV_FILENAME
        return not (self.obj_csv_file.exists() or self.ds_csv_file.exists())

    def add_datastream(self, dsdata: DSData):
        "Add a datastream to the object."
        self.datastream_data.add_datastream(dsdata)

    def add_objectdata(self, objectdata: ObjectData):
        "Add a object to the object."
        self.object_data.add_objectdata(objectdata)

    def get_objectdata(
        self, pid: str | None = None
    ) -> Generator[ObjectData, None, None]:
        """Return the object data for a given object pid.

        If pid is None, return all object data.
        """
        return self.object_data.get_data(pid)

    def get_datastreamdata(
        self, pid: str | None = None
    ) -> Generator[DSData, None, None]:
        """Return the datastream data for a given object pid.

        If pid is None, return all datastream data.
        """
        return self.datastream_data.get_data(pid)

    def write(
        self,
        target_dir: Path | None = None,
        object_filename=None,
        datastream_filename=None,
    ):
        """Save the object and datastream data to csv files.

        If target_dir is not set, the object_dir is used.
        If object_filename is not set, the default object filename (object.csv)
           is used.
        If datastream_filename is not set, the default datastream filename
           (datastreams.csv) is used.
        """
        if target_dir is None:
            target_dir = self.object_dir
        if object_filename is None:
            object_filename = self.OBJECT_CSV_FILENAME
        if datastream_filename is None:
            datastream_filename = self.DATASTREAM_CSV_FILENAME

        self.object_data.to_csv(target_dir / object_filename)
        self.datastream_data.to_csv(target_dir / datastream_filename)

    def count_objects(self) -> int:
        "Return the number of object data objects."
        return len(self.object_data)

    def count_datastreams(self) -> int:
        "Return the number of datastream data objects."
        return len(self.datastream_data)

    def clear(self):
        "Clear the object and datastream data."
        self.object_data = ObjectCSVFile()
        self.datastream_data = DatastreamsCSVFile()

    @property
    def object_id(self):
        "Return the object id."
        return self.object_dir.name
