"""
GAMS Object CSV File

The DSData class represents the datastream metadata for a single object.
"""

import dataclasses
from pathlib import Path

from gamslib import formatdetect
from gamslib.objectcsv import defaultvalues


# pylint: disable=too-many-instance-attributes
@dataclasses.dataclass
class DSData:
    """Represents csv data for a single datastream of a single object."""

    dspath: str
    dsid: str = ""
    title: str = ""
    description: str = ""
    mimetype: str = ""
    creator: str = ""
    rights: str = ""
    lang: str = ""
    tags: str = ""

    @property
    def object_id(self):
        """Return the object id of the object the datastream is part of."""
        return Path(self.dspath).parts[0]

    @classmethod
    def fieldnames(cls) -> list[str]:
        """Return the fields of the object data."""
        return [field.name for field in dataclasses.fields(cls)]

    def merge(self, other_dsdata: "DSData"):
        """Merge the datastream data with another DSData object.

        This is used to update the datastream if it has been created before.
        The datastreams are merged by selectively overwriting the values of the current
        datastream with the values of the other datastream.
        The datastreams must have the same dspath and dsid.
        """
        if self.dspath != other_dsdata.dspath:
            raise ValueError("Cannot merge datastreams with different dspath values")
        if self.dsid != other_dsdata.dsid:
            raise ValueError("Cannot merge datastreams with different dsid values")

        # replace only these fields with new values if the new value is not empty
        # These are the fields that are et automatically. All other fields are
        # set by the user in the csv file.
        fields_to_replace = ["title", "mimetype", "creator", "rights"]
        for field in fields_to_replace:
            if getattr(other_dsdata, field).strip():
                setattr(self, field, getattr(other_dsdata, field))

    def validate(self):
        """Validate the datastream data."""
        if not self.dspath.strip():
            raise ValueError(f"{self.dsid}: dspath must not be empty")
        if not self.dsid.strip():
            raise ValueError(f"{self.dspath}: dsid must not be empty")
        if not self.mimetype.strip():
            raise ValueError(f"{self.dspath}: mimetype must not be empty")
        if not self.rights.strip():
            raise ValueError(f"{self.dspath}: rights must not be empty")

    def guess_missing_values(self, object_path: Path):
        """Guess missing values by analyzing the datastream file."""
        ds_file = object_path / Path(self.dspath).name
        format_info = formatdetect.detect_format(ds_file)
        self._guess_mimetype(format_info)
        self._guess_missing_values(ds_file, format_info)

    def _guess_mimetype(self,  format_info=None):
        """Guess the mimetype if it is empty."""
        if not self.mimetype and format_info is not None:
            self.mimetype = format_info.mimetype

    def _guess_missing_values(self, file_path: Path, format_info=None):
        """Guess missing values."""
        if not self.title and format_info is not None:
            self.title = f"{format_info.description}: {self.dsid}"

        if not self.description and file_path.name in defaultvalues.FILENAME_MAP:
            self.description = defaultvalues.FILENAME_MAP[self.dsid]["description"]
        if not self.rights:
            self.rights = defaultvalues.DEFAULT_RIGHTS
        if not self.creator:
            self.creator = defaultvalues.DEFAULT_CREATOR
