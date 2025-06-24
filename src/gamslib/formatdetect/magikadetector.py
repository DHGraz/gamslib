"""A detector that uses the Googles Magika library to detect file formats.

This detector uses the magika library to detect file formats.
"""

import warnings
from pathlib import Path

from magika import Magika, PredictionMode

from . import jsontypes, xmltypes
from .formatdetector import DEFAULT_TYPE, FormatDetector
from .formatinfo import FormatInfo


class MagikaDetector(FormatDetector):
    """A detector that uses the Googles Magika library to detect file formats."""

    def __init__(self):
        self._magika_object = Magika(prediction_mode=PredictionMode.BEST_GUESS)

    @staticmethod
    def _fix_result(
        file_to_validate: Path, label: str, mime_type: str
    ) -> tuple[str, str]:
        """Sometimes magika identifies json-ld as javascript.

        This function fixes that issue.
        """
        # If magika identifies a file as "javascript", check if it has a json-ld or json extension.
        # If yes, change the label to "json" and the mime type to application/json
        if label == "javascript" and file_to_validate.suffix in [".jsonld", ".json"]:
            label = "json"
            mime_type = "application/json"
        if (
            mime_type == "text/xml"
        ):  # magika uses xml as text/xml, others a application/xml
            mime_type = "application/xml"
        return label, mime_type

    def guess_file_type(self, filepath: Path) -> FormatInfo:
        detector_name = self.__class__.__name__
        subtype = None
        try:
            result = self._magika_object.identify_path(filepath)
            _, mime_type = self._fix_result(
                filepath, result.dl.label, result.dl.mime_type
            )
        # for some reason magika 0.6 sometimes raises a ValueError
        except ValueError:
            mime_type = None
        # magika 0.6 changed this from None to application/unknown
        if mime_type is None or mime_type == "application/undefined":
            # if we cannot determine the mime type, we return the DEFAULT_TYPE
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
        return "MagikaDetector"
