"""Represents an object.csv file of a single GAMS Object.
"""
import csv
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Generator

from gamslib.objectcsv.objectdata import ObjectData


@dataclass
class ObjectCSVFile:
    """Represents csv data for a single object."""

    def __init__(self):
        self._objectdata: list[ObjectData] = []

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
        obj_csv_file = ObjectCSVFile()
        with csv_file.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # mainresource was renamed to mainResource. Just in case we have existing data
                if "mainresource" in row:
                    row["mainResource"] = row.pop("mainresource")
                obj_csv_file.add_objectdata(ObjectData(**row))
        return obj_csv_file

    def to_csv(self, csv_file: Path) -> None:
        """Save the object data to a csv file."""
        with csv_file.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=[field.name for field in fields(ObjectData)]
            )
            writer.writeheader()
            for objdata in self._objectdata:
                writer.writerow(asdict(objdata))

    def sort(self):
        """Sort collected object data by recid value."""
        self._objectdata.sort(key=lambda x: x.recid)

    def __len__(self):
        """Return the number of objectdata objects."""
        return len(self._objectdata)
