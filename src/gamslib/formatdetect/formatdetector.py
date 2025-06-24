"""Abstract base class for format detectors.

The idea of having multiple format detectors is to be able
to choose the best available detector, depending on confguration
or installed software/available services.
"""

import abc
from pathlib import Path

from .formatinfo import FormatInfo

DEFAULT_TYPE = "application/octet-stream"


class FormatDetector(abc.ABC):   # pylint: disable=too-few-public-methods
    """An abstract format detection class."""

    @abc.abstractmethod
    def guess_file_type(self, filepath: Path) -> FormatInfo:
        """Return a FormatInfo object describing the file format."""
