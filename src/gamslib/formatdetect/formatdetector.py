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

from .formatinfo import FormatInfo

DEFAULT_TYPE = "application/octet-stream"
# DEFAULT_TYPE: Default MIME type for unknown or undetectable formats.


class FormatDetector(abc.ABC):   # pylint: disable=too-few-public-methods
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
