"""Describes the format of a file.

FormatInfo objects are returned by format detectors.

It also defines the SubType enum, which contains all supported subtypes
of formats.

The subtype data is fetched from CSV files located in the resources directory
of the formatdetect package.
"""

import csv
from dataclasses import dataclass
from enum import StrEnum
from importlib import resources as impresources
from pathlib import Path


def find_subtype_csv_files() -> list[Path]:
    """Find all CSV files in the resources directory that contain subtype definitions.

    Returns:
        A list of Path objects pointing to the CSV files.
    """
    resource_dir = impresources.files("gamslib") / "formatdetect" / "resources"
    return list(resource_dir.glob("*.csv"))


def load_subtypes_from_csv() -> list[dict[str, str]]:
    """Load subtypes from all CSV files in the resources directory.

    Returns:
        A list of dictionaries, each containing all of the following keys:
        'subformat', 'full name', 'ds name', 'mimetype', and 'maintype'.
    """
    subtypes = []
    for csvfile in find_subtype_csv_files():
        maintype = csvfile.stem.split("_", 1)[
            0
        ]  # Extract the main type from the filename
        with csvfile.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row["maintype"] = maintype  # Add the main type to each row
                # strip whitespace from keys and values
                stripped_row = {k.strip(): v.strip() for k, v in row.items()}
                subtypes.append(stripped_row)
    return subtypes


def extract_subtype_info_from_csv() -> dict[str, str]:
    """Extract data needed for the SubType enum.

    The original data is loaded from all CSV files in the resources directory.
    """
    return {item["subformat"]: item["full name"] for item in load_subtypes_from_csv()}


# `SubType` is an enum for all supported subtypes of formats.
# The values of this are extracted from entries of all csv files in
# the src/gamslib/formatdetect/resources directory.
# It is used to provide a consistent way to refer to these subtypes in the code.
# To add new subtypes, edit one of the csv files.

# Extract a new dict {'subformat' 'full name'} from the loaded subtypes
SubType = StrEnum("SubType", extract_subtype_info_from_csv())


@dataclass
class FormatInfo:
    """Object contains basic information about the format of a file.

    FormatInfo objects are returned by format detectors.
    """

    detector: str  # name of the detector that detected the format
    mimetype: str  # eg. text/xml
    subtype: SubType | None = None  # type: ignore

    def is_xml_type(self) -> bool:  # type: ignore
        """Check if the subtype is an XML type."""
        subtype_info = self._get_subtype_info()
        if subtype_info is not None:
            return (
                subtype_info["subformat"] == self.subtype.name
                and subtype_info["maintype"] == "xml"
            )
        return False

    def is_json_type(self) -> bool:  # type: ignore
        """Check if the subtype is a JSON type."""
        subtype_info = self._get_subtype_info()
        if subtype_info is not None:
            return (
                subtype_info["subformat"] == self.subtype.name
                and subtype_info["maintype"] == "json"
            )
        return False

    @property
    def description(self) -> str:
        """Return a human-friendly description of the format."""
        mime_prefix_map = {
            "text/": "Text document",
            "image/": "Image document",
            "audio/": "Audio document",
            "video/": "Video document",
            "application/": "Application document",
        }
        desc = ""
        subtype_info = self._get_subtype_info()
        if subtype_info is not None:
            desc = subtype_info["ds name"]
        elif self.mimetype == "application/octet-stream":
            desc = "Binary document"
        else:
            for prefix, description in mime_prefix_map.items():
                if self.mimetype.startswith(prefix):
                    desc = description
                    break
        return desc

    def _get_subtype_info(self) -> dict[str, str] | None:
        """Get the full subtype information from the CSV files for this format."""
        subtype_info = None
        if self.subtype is not None:
            for subtype in load_subtypes_from_csv():
                if subtype["subformat"] == self.subtype.name:
                    subtype_info = subtype
        return subtype_info
