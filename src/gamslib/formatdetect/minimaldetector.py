"""A detector that uses the mimetypes module to detect file formats.

This detector should be used as a last resort, if no other detector is available,
because results depend highly on file extensions and data provided by the operating system.
"""

import mimetypes
import warnings
from pathlib import Path

from . import jsontypes, xmltypes
from .formatdetector import DEFAULT_TYPE, FormatDetector
from .formatinfo import FormatInfo


class MinimalDetector(FormatDetector):
    """
    Simple format detector using the Python mimetypes module.

    This detector uses file extensions to determine the MIME type.
    It is not very reliable and should only be used if no other detector is available.
    """

    def __init__(self):
        """
        Initialize the MinimalDetector and register additional MIME types.

        Notes:
            - Adds support for .jp2, .webp, .jsonld, .md, .xml, and .csv extensions.
        """
        mimetypes.add_type("image/jp2", ".jp2")
        mimetypes.add_type("image/webp", ".webp")
        mimetypes.add_type("application/ld+json", ".jsonld")
        mimetypes.add_type("text/markdown", ".md")
        mimetypes.add_type("application/xml", ".xml")
        mimetypes.add_type("text/csv", ".csv")
        super().__init__()

    @staticmethod
    def _fix_mimetype(
        file_to_validate: Path, encoding: str, mime_type: str
    ) -> str:
        """
        Fix common misclassifications as far as we can.

        Args:
            file_to_validate (Path): Path to the file being validated.
            encoding (str): Encoding returned by mimetypes. This is the name of the encoder (e.g. gzip) or None.
            mime_type (str): MIME type returned by Magika. Might be None, too

        Returns:
            tuple[str, str]: Corrected (label, mime_type).

        Notes:
            - Changes 'javascript' label to 'json' for .jsonld/.json files.
            - Converts 'text/xml' MIME type to 'application/xml'.
        """
        if encoding == "gzip":
            # mimetypes returns 'gzip' as encoding for .tgz files, we don't want that
            mime_type = "application/gzip"
        elif encoding == "bzip2":
            mime_type = "application/x-bzip2"
        elif encoding == "xz":
            mime_type = "application/x-xz"
        elif str(file_to_validate).endswith('.tar.lzma'):
            mime_type = "application/x-tar"
        return mime_type


    def guess_file_type(self, filepath: Path) -> FormatInfo:
        """
        Detect the format of a file using the mimetypes module.

        Args:
            filepath (Path): Path to the file to analyze.

        Returns:
            FormatInfo: Object containing detected format information.

        Notes:
            - Uses DEFAULT_TYPE if MIME type cannot be determined.
            - Integrates with xmltypes and jsontypes for subtype detection.
        """
        mime_type, encoding = mimetypes.guess_type(filepath)
        mime_type = self._fix_mimetype(filepath, encoding, mime_type)
        detector_name = str(self)
        subtype = None

        if mime_type is None:
            warnings.warn(
                f"Could not determine mimetype for {filepath}. Using default type."
            )
            mime_type = DEFAULT_TYPE
        elif xmltypes.is_xml_type(mime_type):
            mime_type, subtype = xmltypes.get_format_info(filepath, mime_type)
        elif jsontypes.is_json_type(mime_type):
            mime_type, subtype = jsontypes.get_format_info(filepath, mime_type)

        return FormatInfo(detector=detector_name, mimetype=mime_type, subtype=subtype)

    def __str__(self):
        """
        Return a string representation of the MinimalDetector.

        Returns:
            str: "MinimalDetector"
        """
        return "MinimalDetector"
