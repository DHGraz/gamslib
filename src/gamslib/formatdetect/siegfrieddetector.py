"""A detector that uses the  pygfried library to detect file formats.

Pygfried is the python wrapper for the Siegfried file format identification tool.

This module provides the SiegrfriedDetector class, which uses Pygfried to identify file formats.
It includes logic to  to integrate with GAMSlib's
format detection infrastructure.
"""

import json
import warnings
from pathlib import Path

import pygfried

from . import jsontypes, xmltypes
from .formatdetector import DEFAULT_TYPE, FormatDetector
from .formatinfo import FormatInfo
from gamslib.formatdetect.formatinfo import SubType
from lxml import etree as ET

PRONOM_IDS = {
    "JSON": "fmt/817",
    "JSONLD": "fmt/880",
    "JSONSCHEMA": "fmt/817",
    "JSONL": "fmt/817",
}


class SiegfriedDetector(FormatDetector):
    """
    Detector that uses the Pygfried library to detect file formats.

    Uses Siegfried's prediction engine to identify file types and MIME types.
    """

    def __init__(self):
        """
        Initialize the SiegfriedDetector.
        """
        self._detector_name = f"{self} (Siegfried {pygfried.version()})"

    def _extract_pronom_info(
        self,
        matches: list[dict[str, str]],
    ) -> dict[str, str] | None:
        "Return the pronom match info from the list of matches."
        for match in matches:
            if match["ns"] == "pronom":
                return match
        return None

    def _fix_json_info(self, filepath):
        """Try to fix JSON files that pygfried misidentifies.

        Returns None if detection failes, else a triple, which can be
        passed to create a FormatInfo object.

        Returns:
            tuple[str, SubType, str]: (mime_type, subtype, pronom_id) or None if detecton failed
        """
        try:
            detected_format = jsontypes.get_format_info(filepath, "application/json")
            if detected_format is not None:
                mime_type, subtype = detected_format
                if "json" in mime_type:
                    if subtype == SubType.JSONLD:
                        return mime_type, SubType.JSONLD, "fmt/880"
                    return mime_type, SubType.JSON, "fmt/817"
            return None
        except Exception:
            return None

    def _looks_like_xml(self, filepath):
        "Return True if the file looks like an XML file."
        try:
            ET.parse(filepath)
            return True
        except Exception:
            return False

    def _fix_xml_info(self, filepath):
        """Try to fix XML files that pygfried misidentifies.

        Returns None if detection failes, else a triple, which can be
        passed to create a FormatInfo object.

        Returns:
            tuple[str, SubType, str]: (mime_type, subtype, pronom_id) or None if detecton failed
        """
        try:
            detected_format = xmltypes.get_format_info(filepath, "application/xml")
            if detected_format is not None:
                mime_type, subtype = detected_format
                puid = xmltypes.subformats.get_puid_for_format_type(subtype)
                return mime_type, subtype, puid
            return None
        except Exception:  # pylint: disable=broad-except
            return None

    def _fix_result(
        self,
        filepath: Path,
        mime_type: str,
        subtype: SubType,
        pronom_id: str = "UNKNOWN",
        pronom_warning: str = "",
    ):
        if subtype == SubType.JSONLD or filepath.suffix == ".jsonld":
            return "application/ld+json", SubType.JSONLD, "fmt/880"
        # siegfried vers. 1.11.2 identifies xz files but sets no mimetype
        if pronom_id == "fmt/1098":
            return "application/x-xz", subtype, pronom_id
        # text/plain seems to be a fallback for unrecognized JSON
        if pronom_id == "x-fmt/111":  # text/plain: check for unrecognized JSON
            result = self._fix_json_info(filepath)
            if result is not None:
                return result
            result = self._fix_xml_info(filepath)
            if result is not None:
                return result

        # xml files without doctype are not recognized by pygfried
        if pronom_id in ("UNKNOWN", "x-fmt/111"):
            if "fmt/101" in pronom_warning:  # we have an xml file without doctype
                mime_type, subtype = xmltypes.get_format_info(filepath, mime_type)
                return mime_type, subtype, "fmt/101"
            if "fmt/817" in pronom_warning:  # we have an unrecognized json file
                mime_type, subtype = jsontypes.get_format_info(filepath, mime_type)
        return mime_type, subtype, pronom_id

    def guess_file_type(self, filepath: Path) -> FormatInfo:
        """
        Detect the format of a file using Pygfried and return a FormatInfo object.

        Args:
            filepath (Path): Path to the file to be analyzed.

        Returns:
            FormatInfo: An object containing the detected format information.
        """
        mime_type = DEFAULT_TYPE
        subtype = None
        pronom_id = None
        pronom_warning = ""
        if (
            not filepath.is_file()
        ):  # pygfried always returns a dict; only indicates missing file in 'errors'
            raise FileNotFoundError(f"File {filepath} does not exist.")
        data = pygfried.identify(str(filepath), detailed=True)
        if data and len(data["files"]) == 1:
            result = data["files"][0]
            pronom_info = self._extract_pronom_info(result.get("matches", []))
            if pronom_info is not None:
                mime_type = pronom_info.get("mime", DEFAULT_TYPE)
                pronom_id = pronom_info.get("id")
                pronom_warning = pronom_info.get("warning", "")
                # Siegfried identifies XML files without xml declaration as plain
                # text. I'll try to fix that here.
                if pronom_id == "x-fmt/111" and self._looks_like_xml(filepath):
                    mime_type = "application/xml"
                    pronom_id = "fmt/101"
        else:
            warnings.warn(
                f"Could not determine mimetype for {filepath}. Using default type."
            )
        if mime_type in {None, "", "application/undefined"}:
            mime_type = DEFAULT_TYPE
            warnings.warn(
                f"Could not determine mimetype for {filepath}. Using default type."
            )
        elif xmltypes.is_xml_type(mime_type):
            mime_type, subtype = xmltypes.get_format_info(filepath, mime_type)
        elif jsontypes.is_json_type(mime_type):
            mime_type, subtype = jsontypes.get_format_info(filepath, mime_type)

        mime_type, subtype, pronom_id = self._fix_result(
            filepath, mime_type, subtype, pronom_id, pronom_warning
        )
        if mime_type in (None, "application/undefined", ""):
            mime_type = DEFAULT_TYPE
            warnings.warn(
                f"Could not determine mimetype for {filepath}. Using default type."
            )
        return FormatInfo(
            detector=self._detector_name,
            mimetype=mime_type,
            subtype=subtype,
            pronom_id=pronom_id,
        )

    def __str__(self):
        return f"SiegfriedDetector (Siegfried {pygfried.version()})"
