"""A submodule for file format detection.

The package provides a single important function `detect_format` that
can be used to detect the format of a file and returns
a FormatInfo object.

Format detection is done by one of the available detectors, based on the configuration
setting 'gernal.format_detector'. The default detector is the BaseDetector.

In future we plan to provide REST based detectors like FITS. This is the reason
for the 'format_detector_url' setting in the configuration.
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
    """Return a detector object based on the configuration."""
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
    """Detect the format of a file and return a FormatInfo object describing the format.

    Normally the detector is chosen based on the configuration setting 'general.format_detector'.
    Setting a detector explicitely is only needed for testing or special cases.
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
