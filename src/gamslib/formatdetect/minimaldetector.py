"""A detector that uses the mimetypes module to detect file formats.

This detector should be used as a last resort, if no other detector is available,
because result depend highly on file extensions and data provided by the operating system.
"""

import mimetypes
import warnings
from pathlib import Path

from . import jsontypes, xmltypes
from .formatdetector import DEFAULT_TYPE, FormatDetector
from .formatinfo import FormatInfo


class MinimalDetector(FormatDetector):
    """The most simple Format Detector using the mimetypes module.

    This detector uses the mimetypes module to determine the file type.
    As this module heavily relies on file extensions, it is not very reliable.
    """

    def __init__(self):
        mimetypes.add_type("image/jp2", ".jp2")
        mimetypes.add_type("image/webp", ".webp")
        mimetypes.add_type("application/ld+json", ".jsonld")
        mimetypes.add_type("text/markdown", ".md")
        mimetypes.add_type("application/xml", ".xml")
        mimetypes.add_type("text/csv", ".csv")
        super().__init__()

    def guess_file_type(self, filepath: Path) -> FormatInfo:
        mime_type, _ = mimetypes.guess_type(filepath)
        detector_name = str(self)  # )#self.__class__.__name__
        subtype = None

        if mime_type is None:
            # if we cannot determine the mime type, we return the DEFAULT_TYPE
            warnings.warn(
                f"Could not determine mimetype for {filepath}. Using default type."
            )
            mime_type = DEFAULT_TYPE
        elif xmltypes.is_xml_type(mime_type):
            mime_type, subtype = xmltypes.get_format_info(filepath, mime_type)
        elif jsontypes.is_json_type(mime_type):
            mime_type, subtype = jsontypes.get_format_info(filepath, mime_type)

        return FormatInfo(detector=detector_name, mimetype=mime_type, subtype=subtype)

    def __repr__(self):
        return "MinimalDetector"
