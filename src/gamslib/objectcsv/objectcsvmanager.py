"""
Manage CSV metadata for GAMS objects and their datastreams.

This module provides the ObjectCSVManager class, which manages the metadata 
of an object and its datastreams. It reads and writes the metadata to CSV files named 
`object.csv` and `datastreams.csv` respectively. It also provides methods to validate, 
merge, and manipulate the object and datastream metadata.
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
    Manage object and datastream metadata for a single GAMS object directory.

    Stores, reads, writes, validates, and merges metadata for the object and its datastreams.
    """

    def __init__(self, obj_dir: Path, ignore_existing_csv_files: bool = False):
        """
        Initialize the ObjectCSVManager with the given object directory.

        Args:
            obj_dir (Path): Path to the object directory.
            ignore_existing_csv_files (bool): If True, ignore existing CSV files when writing.
        
        Raises:
            FileNotFoundError: If the object directory does not exist.
        """
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
        """
        Set the object metadata.

        Args:
            object_data (ObjectData): Object metadata to set.
            replace (bool): If True, replace existing object data.

        Raises:
            ValueError: If object data is already set and replace is False.
        """
        if self._object_data is not None and not replace:
            raise ValueError("Object data has already been set.")
        self._object_data = object_data

    def merge_object(self, object_data: ObjectData) -> None:
        """
        Merge the object metadata with another ObjectData object.

        Args:
            object_data (ObjectData): Object metadata to merge.
        """
        if self._object_data is None:
            self._object_data = object_data
        else:
            self._object_data.merge(object_data)

    def get_object(self) -> ObjectData:
        """
        Return the object metadata.

        Returns:
            ObjectData: The object metadata, or None if not set.
        """
        return self._object_data

    def add_datastream(self, dsdata: DSData, replace: bool = False) -> None:
        """
        Add a datastream to the object.

        Args:
            dsdata (DSData): Datastream metadata to add.
            replace (bool): If True, replace existing datastream with the same dsid.

        Raises:
            ValueError: If datastream with the same dsid exists and replace is False.
        """
        if dsdata.dsid in [ds.dsid for ds in self._datastream_data]:
            if replace:
                self._datastream_data = [
                    ds for ds in self._datastream_data if ds.dsid != dsdata.dsid
                ]
            else:
                raise ValueError(f"Datastream with id {dsdata.dsid} already exists.")
        self._datastream_data.append(dsdata)

    def merge_datastream(self, dsdata: DSData) -> None:
        """
        Merge the datastream metadata with another DSData object.

        Args:
            dsdata (DSData): Datastream metadata to merge.
        """
        for existing_ds in self._datastream_data:
            if existing_ds.dsid == dsdata.dsid and existing_ds.dspath == dsdata.dspath:
                existing_ds.merge(dsdata)
                return
        self.add_datastream(dsdata)

    def get_datastreamdata(self) -> Generator[DSData, None, None]:
        """
        Return a generator for all datastream metadata.

        Returns:
            Generator[DSData, None, None]: Generator of DSData objects.
        """
        yield from self._datastream_data

    def count_datastreams(self) -> int:
        """
        Return the number of datastreams.

        Returns:
            int: Number of datastreams.
        """
        return len(self._datastream_data)

    def get_languages(self):
        """
        Return the languages of the datastreams ordered by frequency.

        Returns:
            list[str]: List of language codes ordered by frequency.
        """
        languages = []
        for dsdata in self.get_datastreamdata():
            if dsdata.lang:
                dlangs = utils.split_entry(dsdata.lang)
                languages.extend(dlangs)
        langcounter = Counter(languages)
        return [entry[0] for entry in langcounter.most_common()]

    def is_empty(self) -> bool:
        """
        Return True if the object has no CSV metadata.

        Returns:
            bool: True if object or datastream metadata is missing, False otherwise.
        """
        return self._object_data is None or not self._datastream_data

    def save(self) -> None:
        """
        Save the object metadata and datastreams to their respective CSV files.

        Raises:
            FileExistsError: If CSV files already exist and ignore_existing_csv_files is False.
        """
        self._write_object_csv()
        self._write_datastreams_csv()

    def clear(self) -> None:
        """
        Clear the object metadata and datastreams, and delete the CSV files.

        Removes all metadata and deletes object.csv and datastreams.csv files if present.
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
        """
        Validate the object metadata and datastreams.

        Raises:
            ValueError: If metadata is missing or invalid.
        """
        if self.is_empty():
            raise ValueError("Object metadata (csv) is not set.")
        self._object_data.validate()
        for dsdata in self._datastream_data:
            dsdata.validate()

    def guess_mainresource(self) -> None:
        """
        Guess and set the main resource of the object based on the datastreams.

        Heuristics:
            - If there is only one XML datastream besides DC.xml, use it as mainResource.

        Returns:
            str: The guessed main resource ID, or empty string if not determined.
        """
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
        """
        Read object metadata from the CSV file.

        Returns:
            ObjectData | None: Object metadata if present, else None.
        """
        csv_file = self.obj_dir / OBJ_CSV_FILENAME

        if not csv_file.is_file():
            return None
        with csv_file.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                if "mainresource" in row:
                    row["mainResource"] = row.pop("mainresource")
                return ObjectData(**row)

    def _write_object_csv(self):
        """
        Write the object metadata to the CSV file.

        Raises:
            FileExistsError: If the CSV file exists and ignore_existing_csv_files is False.
        """
        csv_file = self.obj_dir / OBJ_CSV_FILENAME
        if csv_file.is_file() and not self._ignore_existing_csv_files:
            raise FileExistsError(f"Object CSV file '{csv_file}' already exists.")
        with csv_file.open("w", encoding="utf-8", newline="") as f:
            fieldnames = ObjectData.fieldnames()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(dataclasses.asdict(self._object_data))

    def _read_datastreams_csv(self) -> list[DSData]:
        """
        Read datastream metadata from the CSV file.

        Returns:
            list[DSData]: List of datastream metadata.
        """
        datastreams = []
        csv_file = self.obj_dir / DS_CSV_FILENAME
        if not csv_file.is_file():
            return []
        with csv_file.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                dsdata = DSData(**row)
                datastreams.append(dsdata)
        return datastreams

    def _write_datastreams_csv(self):
        """
        Write the datastream metadata to the CSV file.

        Notes:
            - Datastreams are sorted by dsid before writing.
        """
        csv_file = self.obj_dir / DS_CSV_FILENAME
        self._datastream_data.sort(key=lambda ds: ds.dsid)
        with csv_file.open("w", encoding="utf-8", newline="") as f:
            fieldnames = DSData.fieldnames()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for dsdata in self._datastream_data:
                writer.writerow(dataclasses.asdict(dsdata))
