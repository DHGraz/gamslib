"""A detector that uses the Google Magika library to detect file formats.

This module provides the MagikaDetector class, which uses Magika to identify file formats.
It includes logic to correct common misclassifications and to integrate with GAMSlib's
format detection infrastructure.
"""

import warnings
from pathlib import Path

from magika import Magika, PredictionMode

from . import jsontypes, xmltypes
from .formatdetector import DEFAULT_TYPE, FormatDetector
from .formatinfo import FormatInfo


class MagikaDetector(FormatDetector):
    """
    Detector that uses the Google Magika library to detect file formats.

    Uses Magika's prediction engine to identify file types and MIME types.
    Applies corrections for known misclassifications (e.g., JSON-LD as JavaScript).
    """

    def __init__(self):
        """
        Initialize the MagikaDetector with Magika's BEST_GUESS prediction mode.
        """
        self._magika_object = Magika(prediction_mode=PredictionMode.BEST_GUESS)

    @staticmethod
    def _fix_result(
        file_to_validate: Path, label: str, mime_type: str
    ) -> tuple[str, str]:
        """
        Fix common misclassifications returned by Magika.

        Args:
            file_to_validate (Path): Path to the file being validated.
            label (str): Label returned by Magika.
            mime_type (str): MIME type returned by Magika.

        Returns:
            tuple[str, str]: Corrected (label, mime_type).

        Notes:
            - Changes 'javascript' label to 'json' for .jsonld/.json files.
            - Converts 'text/xml' MIME type to 'application/xml'.
        """
        if label == "javascript" and file_to_validate.suffix in [".jsonld", ".json"]:
            label = "json"
            mime_type = "application/json"
        if mime_type == "text/xml":
            mime_type = "application/xml"
        return label, mime_type

    def guess_file_type(self, filepath: Path) -> FormatInfo:
        """
        Detect the format of a file using Magika and return a FormatInfo object.

        Args:
            filepath (Path): Path to the file to analyze.

        Returns:
            FormatInfo: Object containing detected format information.

        Notes:
            - Applies corrections for known Magika misclassifications.
            - Uses DEFAULT_TYPE if Magika cannot determine the MIME type.
            - Integrates with xmltypes and jsontypes for subtype detection.
        """
        detector_name = self.__class__.__name__
        subtype = None
        try:
            result = self._magika_object.identify_path(filepath)
            _, mime_type = self._fix_result(
                filepath, result.dl.label, result.dl.mime_type
            )
        except ValueError:
            mime_type = None
        if mime_type is None or mime_type == "application/undefined":
            mime_type = DEFAULT_TYPE
            warnings.warn(
                f"Could not determine mimetype for {filepath}. Using default type."
            )
        elif xmltypes.is_xml_type(mime_type):
            mime_type, subtype = xmltypes.get_format_info(filepath, mime_type)
        elif jsontypes.is_json_type(mime_type):
            mime_type, subtype = jsontypes.get_format_info(filepath, mime_type)
        return FormatInfo(detector=detector_name, mimetype=mime_type, subtype=subtype)

    def __repr__(self):
        """
        Return a string representation of the MagikaDetector.

        Returns:
            str: "MagikaDetector"
        """
        return "MagikaDetector"
