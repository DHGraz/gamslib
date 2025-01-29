"""Abstract base class for format detectors.

The idea of having multiple format detectors is to be able 
to choose the best available detector, depending on confguration
or installed software/available services.
"""

import abc
from pathlib import Path

from .formatinfo import FormatInfo

import logging

logger = logging.getLogger(__name__)

DEFAULT_TYPE = "application/octet-stream"


class FormatDetector(abc.ABC):
    """An abstract format detection class."""

    @abc.abstractmethod
    def guess_file_type(self, filepath: Path, with_details=True) -> FormatInfo:
        """Abstract method: Detect the format of a file and return a FormatInfo object describing the format."""
        



