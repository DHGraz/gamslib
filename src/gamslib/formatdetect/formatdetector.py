"""Abstract base class for format detectors.

Defines the FormatDetector abstract base class for file format detection in GAMS projects.
Supports multiple detector implementations, allowing selection based on configuration,
installed software, or available services.

Features:
    - Abstract FormatDetector class for extensible format detection.
    - Standard interface for returning FormatInfo objects.
    - Default MIME type constant for unknown formats.
"""

import abc
from pathlib import Path

from lxml import etree as ET

from .formatinfo import FormatInfo

# Default MIME type for unknown or undetectable formats.
DEFAULT_TYPE = "application/octet-stream"
# DEFAULT_TYPE: Default MIME type for unknown or undetectable formats.


class FormatDetector(abc.ABC):  # pylint: disable=too-few-public-methods
    """
    Abstract base class for file format detectors.

    Subclasses must implement the guess_file_type method to analyze a file and
    return a FormatInfo object describing its format.
    """

    @abc.abstractmethod
    def guess_file_type(self, filepath: Path) -> FormatInfo:
        """
        Analyze the file and return a FormatInfo object describing its format.

        Args:
            filepath (Path): Path to the file to analyze.

        Returns:
            FormatInfo: Object containing detected format information.

        Raises:
            NotImplementedError: If not implemented in subclass.
        """

    @staticmethod
    def looks_like_xml(filepath: Path) -> bool:
        "Return True if the file looks like an XML file."
        try:
            ET.parse(filepath) # pylint: disable=c-extension-no-member
            return True
        except Exception:  # pylint: disable=broad-except
            return False

    @staticmethod
    def has_xml_declaration(filepath: Path) -> bool:
        "Return True if filepath contains an xml declaration."
        with filepath.open("rb") as f:
            header = f.read(500)
        return b"<?xml " in header
