"""File format detection utilities for GAMS projects.

This submodule provides functions and classes to detect the format of files and return
a FormatInfo object describing the detected format.

Currently these Detectors are available:

  - MimeDetector: Uses the `mimetypes` library to identify
    file formats based on file extensions. This is a minimal detector
    and should be used as a fallback only.
  - MagikaDetector: Uses the Google Magika library to identify
    file formats based on file content. This is the preferred
    detector and should be used by default.
    
All detectors implement the FormatDetector abstract base class
and return FormatInfo objects with the detected format information.
The FormatInfo object includes the MIME type, detector name, and the
subformat name if applicable. The subformat is determined by heuristics
based on the MIME type and file content. 

Currently supported subformats include:

  - XML subformats
  - JSON subformats

Features:
    - `detect_format`: Main function to detect the format of a file.
    - Detector selection based on configuration ('general.format_detector').
    - Support for multiple detectors (e.g., Magika, MinimalDetector).
    - Extensible for future REST-based detectors (e.g., FITS).

Usage:
    Use `detect_format(filepath)` to get format information for a file.
    Detector is chosen automatically based on configuration, but can be set explicitly for testing.

Configuration:
    - 'general.format_detector': Name of the detector to use (default: 'magika').
    - 'general.format_detector_url': Optional URL for REST-based detectors.

Future:
    Additional detectors and REST-based services may be supported.
"""

import os
from functools import lru_cache
from pathlib import Path

from ..projectconfiguration import MissingConfigurationException, get_configuration
from .formatdetector import FormatDetector
from .formatinfo import FormatInfo
from .magikadetector import MagikaDetector
from .minimaldetector import MinimalDetector

DEFAULT_DETECTOR_NAME = "magika"


@lru_cache
def make_detector(detector_name: str, detector_url: str = "") -> FormatDetector:
    """
    Return a detector object based on the given name and optional URL.

    Args:
        detector_name (str): Name of the detector to use ('base', 'magika', etc.).
        detector_url (str): Optional URL for REST-based detectors.

    Returns:
        FormatDetector: An instance of the selected detector.

    Raises:
        ValueError: If the detector name is unknown.

    Notes:
        - If no detector name is provided, the default detector is used.
        - Future detectors may require checking for software or service availability.
    """
    # TODO: as soon we have detector which depend on installed software or available services,
    #       we must check for availability if no explicit detector is given
    detector = None
    if detector_name == "":
        detector_name = DEFAULT_DETECTOR_NAME
    if detector_name == "base":
        detector = MinimalDetector()
    elif detector_name == "magika":
        detector = MagikaDetector()
    # TODO: add more detectors
    if detector is None:
        raise ValueError(f"Unknown detector '{detector_name}'")
    return detector


def detect_format(filepath: Path) -> FormatInfo:
    """
    Detect the format of a file and return a FormatInfo object describing the format.

    Args:
        filepath (Path): Path to the file to detect format for.

    Returns:
        FormatInfo: Object containing format information for the file.

    Notes:
        - Detector is chosen based on the configuration setting 'general.format_detector'.
        - If no configuration is found, the default detector is used.
        - Explicit detector selection is only needed for testing or special cases.
    """
    try:
        config = get_configuration()
        detector = make_detector(
            config.general.format_detector, config.general.format_detector_url
        )
        return detector.guess_file_type(filepath)
    except MissingConfigurationException:
        # if no configuration is found, we use the default  detector
        detector = make_detector(DEFAULT_DETECTOR_NAME)
        return  make_detector(DEFAULT_DETECTOR_NAME).guess_file_type(filepath)
