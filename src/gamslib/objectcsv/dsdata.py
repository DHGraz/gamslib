"""
Datastream metadata model for GAMS object CSV files.

Defines the DSData class, which represents metadata for a single datastream of a GAMS object.
Provides methods for merging, validating, and inferring missing metadata values.
"""

import dataclasses
from pathlib import Path

from gamslib import formatdetect
from gamslib.objectcsv import defaultvalues


# pylint: disable=too-many-instance-attributes
@dataclasses.dataclass
class DSData:
    """
    Represents metadata for a single datastream of a GAMS object.

    Fields:

      - dspath (str): Relative path to the datastream file.
      - dsid (str): Datastream identifier.
      - title (str): Title of the datastream.
      - description (str): Description of the datastream.
      - mimetype (str): MIME type of the datastream.
      - creator (str): Creator of the datastream.
      - rights (str): Rights statement for the datastream.
      - lang (str): Language(s) of the datastream.
      - tags (str): Additional tags for the datastream.
    """

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
        """
        Return the object ID for the datastream.

        The object ID is inferred from the first part of the datastream path.
        """
        return Path(self.dspath).parts[0]

    @classmethod
    def fieldnames(cls) -> list[str]:
        """
        Return the list of field names for DSData.

        Returns:
            list[str]: Names of all fields in the DSData dataclass.
        """
        return [field.name for field in dataclasses.fields(cls)]

    def merge(self, other_dsdata: "DSData"):
        """
        Merge metadata from another DSData instance.

        Selectively overwrites fields ('title', 'mimetype', 'creator', 'rights') with non-empty
        values from the other instance. Both datastreams must have the same dspath and dsid.

        Args:
            other_dsdata (DSData): Another DSData instance to merge from.

        Raises:
            ValueError: If dspath or dsid do not match.
        """
        if self.dspath != other_dsdata.dspath:
            raise ValueError("Cannot merge datastreams with different dspath values")
        if self.dsid != other_dsdata.dsid:
            raise ValueError("Cannot merge datastreams with different dsid values")

        fields_to_replace = ["title", "mimetype", "creator", "rights"]
        for field in fields_to_replace:
            if getattr(other_dsdata, field).strip():
                setattr(self, field, getattr(other_dsdata, field))

    def validate(self):
        """
        Validate required metadata fields.

        Raises:
            ValueError: If any required field (dspath, dsid, mimetype, rights) is empty.
        """
        if not self.dspath.strip():
            raise ValueError(f"{self.dsid}: dspath must not be empty")
        if not self.dsid.strip():
            raise ValueError(f"{self.dspath}: dsid must not be empty")
        if not self.mimetype.strip():
            raise ValueError(f"{self.dspath}: mimetype must not be empty")
        if not self.rights.strip():
            raise ValueError(f"{self.dspath}: rights must not be empty")

    def guess_missing_values(self, object_path: Path):
        """
        Infer missing metadata values by analyzing the datastream file.

        Uses format detection and default values to fill in missing fields.

        Args:
            object_path (Path): Path to the object directory containing the datastream.
        """
        ds_file = object_path / Path(self.dspath).name
        format_info = formatdetect.detect_format(ds_file)
        self._guess_mimetype(format_info)
        self._guess_missing_values(ds_file, format_info)

    def _guess_mimetype(self, format_info=None):
        """
        Guess and set the MIME type if it is missing.

        Args:
            format_info (FormatInfo, optional): Format information for the datastream.
        """
        if not self.mimetype and format_info is not None:
            self.mimetype = format_info.mimetype

    def _guess_missing_values(self, file_path: Path, format_info=None):
        """
        Infer and set missing metadata fields using file and format info.

        Args:
            file_path (Path): Path to the datastream file.
            format_info (FormatInfo, optional): Format information for the datastream.
        """
        if not self.title and format_info is not None:
            self.title = f"{format_info.description}: {self.dsid}"

        if not self.description and file_path.name in defaultvalues.FILENAME_MAP:
            self.description = defaultvalues.FILENAME_MAP[self.dsid]["description"]
        if not self.rights:
            self.rights = defaultvalues.DEFAULT_RIGHTS
        if not self.creator:
            self.creator = defaultvalues.DEFAULT_CREATOR
