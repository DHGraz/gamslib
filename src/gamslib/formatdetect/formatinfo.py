"""Describes the format of a file.

FormatInfo objects are returned by format detectors.
"""

from dataclasses import dataclass


@dataclass
class FormatInfo:
    """Object contains basic information about the format of a file.

    FormatInfo objects are returned by format detectors.
    """

    detector: str  # name of the detector that detected the format
    mimetype: str  # text/xml
    subtype: str | None = None  # e.g. tei or json-ld
