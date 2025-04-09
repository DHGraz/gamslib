from gamslib.objectcsv.dsdata import DSData


import csv
from dataclasses import asdict, fields
from pathlib import Path
from typing import Generator


class DatastreamsCSVFile:
    """Represents csv data for all datastreams of a single object."""

    def __init__(self, object_dir: Path):
        self._datastreams: list[DSData] = []
        self._object_dir = object_dir

    def add_datastream(self, dsdata: DSData):
        """Add a datastream to the datastreams."""
        dsdata.guess_missing_values(self._object_dir)
        self._datastreams.append(dsdata)

    def remove_datastream(self, dspath: str, dsid: str):
        """Remove a datastream from the datastreams."""
        for dsdata in self._datastreams:
            if dsdata.dspath == dspath and dsdata.dsid == dsid:
                self._datastreams.remove(dsdata)
                break

    def merge_datastream(self, dsdata: DSData):
        """Merge a datastream with an existing datastream."""
        old_ds = self.get_data(dsdata.ds_id)
        if old_ds is None:
            return None
        for ds in self._datastreams:
            if ds.dspath == dsdata.dspath and ds.dsid == dsdata.dsid:
                # merge the datastream
                #ds.__dict__.update(dsdata.__dict__)
                ds.merge(dsdata)
                return
        # if not found, add the new datastream
        self.add_datastream(dsdata)

    def get_data(self, pid: str | None = None) -> Generator[DSData, None, None]:
        """Return the datastream objects for a given object pid.

        If pid is None, yield all datastream objects.
        Filtering by pid is only needed if we have data from multiple objects.
        """
        for dsdata in self._datastreams:
            if pid is None or dsdata.object_id == pid:
                yield dsdata

    @classmethod
    def from_csv(cls, csv_file: Path) -> "DatastreamsCSVFile":
        """Load the datastream container data from a csv file."""
        ds_csv_file = DatastreamsCSVFile(csv_file.parent)
        with csv_file.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ds_csv_file.add_datastream(DSData(**row))
        return ds_csv_file

    def to_csv(self, csv_file: Path):
        """Save the datastream data to a csv file."""
        self._datastreams.sort(key=lambda x: x.dspath)
        with csv_file.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=[field.name for field in fields(DSData)]
            )
            writer.writeheader()
            for dsdata in self._datastreams:
                writer.writerow(asdict(dsdata))

    def sort(self):
        """Sort collected datastream data by dspath value."""
        self._datastreams.sort(key=lambda x: x.dspath)

    def get_languages(self) -> list[str]:
        """Return the languages of all datastreams.

        Extract and combine all entries from the 'lang' field of all datastreams.
        Returns list of all language codes as strings. The list can contain duplicates,
        which allows us to rank languaes by their frequency.
        """
        languages = []
        for ds in self._datastreams:
            languages.extend(ds.lang.split())
        return languages

    def __len__(self):
        """Return the number of datastreams."""
        return len(self._datastreams)