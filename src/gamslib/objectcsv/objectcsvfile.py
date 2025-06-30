"""Represents an object.csv file of a single GAMS Object.
"""
import csv
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Generator

from gamslib.objectcsv.exceptions import ValidationError
from gamslib.objectcsv.objectdata import ObjectData


@dataclass
class ObjectCSVFile:
    """Represents csv data for a single object."""

    def __init__(self, object_dir: Path | None = None):
        self._objectdata: list[ObjectData] = []
        self._object_dir: Path|None = object_dir

    def add_objectdata(self, objectdata: ObjectData):
        """Add a ObjectData object."""
        self._objectdata.append(objectdata)

    def get_data(self, recid: str | None = None) -> Generator[ObjectData, None, None]:
        """Return the objectdata objects for a given object pid.

        If pid is None, return all objectdata objects.
        Filtering by pid is only needed if we have data from multiple objects.
        """
        for objdata in self._objectdata:
            if recid is None or objdata.recid == recid:
                yield objdata

    def merge_object(self, other: ObjectData) -> ObjectData:
        """Merge the object data with dara from other.

        Returns the merged ObjectData object.
        """
        old_objectdata = next(self.get_data(other.recid), None)
        if old_objectdata is None:
            self.add_objectdata(other)
            return other

        old_objectdata.merge(other)
        return old_objectdata

    @classmethod
    def from_csv(cls, csv_file: Path) -> "ObjectCSVFile":
        """Load the object data from a csv file."""
        if not csv_file.is_file():
            raise FileNotFoundError(f"Object CSV file {csv_file} does not exist.")
        obj_csv_file = ObjectCSVFile(csv_file.parent)
        with csv_file.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                # mainresource has been renamed to mainResource and mainresource was renamed to mainResource. 
                # Just in case we have existing data we fix this here.
                if "mainresource" in row:
                    row["mainResource"] = row.pop("mainresource")
                obj_csv_file.add_objectdata(ObjectData(**row))
        if len(obj_csv_file._objectdata) == 0:
            raise ValidationError(f"Empty object.csv file {csv_file}.")
        return obj_csv_file

    def to_csv(self, csv_file: Path|None) -> None:
        """Save the object data to a csv file."""
        if csv_file is None:
            csv_file = self._object_dir / "object.csv"
        with csv_file.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=[field.name for field in fields(ObjectData)]
            )
            writer.writeheader()
            for objdata in self._objectdata:
                writer.writerow(asdict(objdata))
        self._object_dir = csv_file.parent

    def sort(self):
        """Sort collected object data by recid value."""
        self._objectdata.sort(key=lambda x: x.recid)

    def set_mainresource(self, recid: str, dsid: str) -> None:
        """Set the main resource for the object data.

        This is used to set the main resource for the object data.
        The main resource is the datastream with the given dsid.
        If the mainResource is already set, it will not be changed.
        """
        for objdata in self._objectdata:
            if objdata.recid == recid and objdata.mainResource == "":
                objdata.mainResource = dsid
                # If the mainResource is set, we don't need to check further
                # as there should be only one object with the same recid.
                return

    def validate(self) -> None:
        """Validate the datastreams data.
        
        Raises ValueError if the object data is invalid."""
        if len(self._objectdata) == 0:
            raise ValidationError(f"Empty object.csv in {self._object_dir}.")
        for objdata in self._objectdata:
            objdata.validate()


    def __len__(self):
        """Return the number of objectdata objects."""
        return len(self._objectdata)
