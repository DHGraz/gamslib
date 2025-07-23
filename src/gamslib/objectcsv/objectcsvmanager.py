"""
Manage CSV metadata for GAMS objects and their datastreams.

This module provides the ObjectCSVManager class, which manages the metadata 
of an object and its datastreams.
It reads and writes the metadata to CSV files named `object.csv` and 
`datastreams.csv` respectively.
It also provides methods to validate, merge, and manipulate the object and 
datastream metadata.
"""

from collections import Counter
import csv
import dataclasses
from pathlib import Path
from typing import Generator

from gamslib.objectcsv import utils
from gamslib.objectcsv.dsdata import DSData
from gamslib.objectcsv.objectdata import ObjectData

OBJ_CSV_FILENAME = "object.csv"
DS_CSV_FILENAME = "datastreams.csv"


class ObjectCSVManager:
    """
    This class is used to store object metadata and metadata about its datastreams.
    """

    def __init__(self, obj_dir: Path, ignore_existing_csv_files: bool = False):
        """Initialize the ObjectMeta with the given object directory."""
        self.obj_dir: Path = obj_dir
        self._ignore_existing_csv_files: bool = ignore_existing_csv_files
        if not self.obj_dir.is_dir():
            raise FileNotFoundError(
                f"Object directory '{self.obj_dir}' does not exist."
            )
        self.object_id = self.obj_dir.name
        self._object_data: ObjectData | None = self._read_object_csv()
        self._datastream_data: list[DSData] = self._read_datastreams_csv()

    def set_object(self, object_data: ObjectData, replace: bool = False) -> None:
        """Set the object data.

        This function raises a ValueError if the object data has already been set,
        unless `replace` is True.
        If `replace` is True, it will replace the existing object data with the new one.
        """
        if self._object_data is not None and not replace:
            raise ValueError("Object data has already been set.")
        self._object_data = object_data

    def merge_object(self, object_data: ObjectData) -> None:
        """Merge the object data with another ObjectData object."""
        if self._object_data is None:
            self._object_data = object_data
        else:
            self._object_data.merge(object_data)

    def get_object(self) -> ObjectData:
        """Return the object csv data.
        
        This is always a single ObjectData object, as we only have one 
        object per directory.
        If the object data has not been set, it returns None.
        """
        return self._object_data

    def add_datastream(self, dsdata: DSData, replace: bool = False) -> None:
        """Add a datastream to the object.

        If the datastream with the same dsid already exists, it raises a 
        ValueError unless `replace` is True.
        If `replace` is True, it will replace the existing datastream with 
        the new one.
        """
        if dsdata.dsid in [ds.dsid for ds in self._datastream_data]:
            if replace:
                # Remove the existing datastream
                # This is necessary to avoid duplicates in the list
                self._datastream_data = [
                    ds for ds in self._datastream_data if ds.dsid != dsdata.dsid
                ]
            else:
                # Raise an error if the datastream already exists
                raise ValueError(f"Datastream with id {dsdata.dsid} already exists.")
        self._datastream_data.append(dsdata)

    def merge_datastream(self, dsdata: DSData) -> None:
        """Merge the datastream data with another DSData object."""
        for existing_ds in self._datastream_data:
            if existing_ds.dsid == dsdata.dsid and existing_ds.dspath == dsdata.dspath:
                existing_ds.merge(dsdata)
                return
        # If no existing datastream was found, add the new one
        self.add_datastream(dsdata)

    def get_datastreamdata(self) -> Generator[DSData, None, None]:
        """Return a generator for the datastream data."""
        yield from self._datastream_data

    def count_datastreams(self) -> int:
        """Return the number of datastreams."""
        return len(self._datastream_data)

    def get_languages(self):
        """Return the languages of the datastreams ordered by frequency."""
        languages = []
        for dsdata in self.get_datastreamdata():
            if dsdata.lang:
                dlangs = utils.split_entry(dsdata.lang)
                languages.extend(dlangs)
        langcounter = Counter(languages)
        return [entry[0] for entry in langcounter.most_common()]

    def is_empty(self) -> bool:
        """Return True if the object has no csv metadata."""
        return self._object_data is None or not self._datastream_data

    def save(self) -> None:
        """Save the object metadata and datastreams to their respective CSV files.

        If `overwrite` is True, it will overwrite the existing CSV files.
        If `overwrite` is False and the CSV files already exist, it raises a FileExistsError.
        """
        self._write_object_csv()
        self._write_datastreams_csv()

    def clear(self) -> None:
        """Clear the object metadata and datastreams.

        This removes the object metadata and all datastreams, and deletes the CSV files.
        """
        self._object_data = None
        self._datastream_data = []
        obj_csv_file = self.obj_dir / OBJ_CSV_FILENAME
        ds_csv_file = self.obj_dir / DS_CSV_FILENAME
        if obj_csv_file.is_file():
            obj_csv_file.unlink()
        if ds_csv_file.is_file():
            ds_csv_file.unlink()

    def validate(self) -> None:
        """Validate the object metadata and datastreams.

        Raises ValueError if the metadata is not valid.
        """
        if self.is_empty():
            raise ValueError("Object metadata (csv) is not set.")
        self._object_data.validate()
        for dsdata in self._datastream_data:
            dsdata.validate()

    def guess_mainresource(self) -> None:
        """Guess (and set)the main resource of the object based on the datastreams.

        Heuristics:
          - if there is only one xml datastream beside DC.xml
            use this one as mainResource.
        """
        # TODO: this heuristic is very basic, we should improve this later
        main_resource = ""
        xml_files = []
        for dsdata in self.get_datastreamdata():
            if dsdata.dsid not in ("DC.xml", "DC") and dsdata.mimetype in (
                "application/xml",
                "text/xml",
                "application/tei+xml",
            ):
                xml_files.append(dsdata.dsid)
        if len(xml_files) == 1:
            self._object_data.mainResource = xml_files[0]
        return main_resource

    def _read_object_csv(self) -> ObjectData | None:
        """Read object data from the CSV file."""
        csv_file = self.obj_dir / OBJ_CSV_FILENAME

        if not csv_file.is_file():
            return None
        with csv_file.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                # mainresource has been renamed to mainResource
                # Just in case we have existing data we fix this here.
                if "mainresource" in row:
                    row["mainResource"] = row.pop("mainresource")
                # we only can have one object per object directory
                return ObjectData(**row)

    def _write_object_csv(self):
        """Write the object data to the CSV file."""
        csv_file = self.obj_dir / OBJ_CSV_FILENAME
        if csv_file.is_file() and not self._ignore_existing_csv_files:
            raise FileExistsError(f"Object CSV file '{csv_file}' already exists.")
        with csv_file.open("w", encoding="utf-8", newline="") as f:
            fieldnames = ObjectData.fieldnames()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(dataclasses.asdict(self._object_data))

    def _read_datastreams_csv(self) -> list[DSData]:
        """Read datastream data from the CSV file."""
        datastreams = []
        csv_file = self.obj_dir / DS_CSV_FILENAME
        if not csv_file.is_file():
            return []
        with csv_file.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                dsdata = DSData(**row)
                # self._datastream_data.append(dsdata)
                datastreams.append(dsdata)
        return datastreams

    def _write_datastreams_csv(self):
        """Write the datastream data to the CSV file."""
        csv_file = self.obj_dir / DS_CSV_FILENAME
        with csv_file.open("w", encoding="utf-8", newline="") as f:
            fieldnames = DSData.fieldnames()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for dsdata in self._datastream_data:
                writer.writerow(dataclasses.asdict(dsdata))
