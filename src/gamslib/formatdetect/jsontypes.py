"""Module to inspect and classify JSON files.

Provides utilities to check MIME types, detect JSON lines format, and guess the subtype of 
JSON files.
Maps supported subtypes to MIME types and offers helpers for format detection.
"""

import json
from pathlib import Path

from gamslib.formatdetect.formatinfo import SubType


# These MIME Types (as returned by a detection tool) are handled as JSON files.
# This is an extension to the MIMETYPES dict, as some mime types listed here are not
# yet registered, but might be used by some format detection tools. Feel free to add more.
JSON_MIME_TYPES = [
    "application/json",
    "application/ld+json",
    "application/schema+json",
    "application/jsonl",
]


# Maps SubType enums to MIME types for JSON formats.
MIMETYPES = {
    SubType.JSON: "application/json",
    SubType.JSONLD: "application/ld+json",
    # The suggested mime type is application/schema+json, but it is not registered yet
    # SubType.JSONSCHEMA: "application/schema+json",
    SubType.JSONSCHEMA: "application/json",
    # The suggested mime type is application/jsonl, but it is not registered yet
    # SubType.JSONL: "application/jsonl"
    SubType.JSONL: "application/json",
}


def is_json_type(mime_type: str) -> bool:
    """
    Check if a MIME type is recognized as a JSON type.

    Args:
        mime_type (str): MIME type to check.

    Returns:
        bool: True if the MIME type is a known JSON type, False otherwise.
    """
    return mime_type in JSON_MIME_TYPES or mime_type in MIMETYPES.values()


def is_jsonl(data: str) -> bool:
    """
    Check if a string contains JSON lines (jsonl) format.

    Args:
        data (str): String content of the file.

    Returns:
        bool: True if the content is valid JSON lines, False otherwise.

    Notes:
        - Used primarily by the 'guess_json_format' function.
        - Returns False for empty strings.
    """
    if data.strip() == "":
        return False
    lines = data.splitlines()
    is_jsonl_ = True
    for line in lines:
        try:
            json.loads(line)
        except json.JSONDecodeError:
            is_jsonl_ = False
            break
    return is_jsonl_


def guess_json_format(file_to_validate: Path) -> SubType:
    """
    Guess the subtype of a JSON file.

    Args:
        file_to_validate (Path): Path to the JSON file.

    Returns:
        SubType: Detected subtype (JSON, JSONLD, JSONSCHEMA, or JSONL).

    Notes:
        - Checks file extension and content for schema or linked data context.
        - Falls back to JSONL if content is not valid JSON but is valid JSON lines.
    """
    if file_to_validate.suffix == ".jsonld":
        return SubType.JSONLD

    try:
        with open(file_to_validate, "r", encoding="utf-8", newline="") as f:
            file_content = f.read()
            jsondata = json.loads(file_content)
            if (
                "$schema" in jsondata
                and jsondata["$schema"]
                == "https://json-schema.org/draft/2020-12/schema"
            ):
                return SubType.JSONSCHEMA

            for key in jsondata:
                if key in ["@context", "@id"]:
                    return SubType.JSONLD
    # If file contains JSONL context, parsing will fail
    except json.JSONDecodeError as exp:
        if is_jsonl(file_content):
            return SubType.JSONL
        raise exp from exp  # eg. invalid JSON
    return SubType.JSON


def get_format_info(filepath: Path, mime_type: str) -> tuple[str, SubType | None]:
    """
    Return a tuple with the (possibly fixed) MIME type and detected JSON subtype.

    Args:
        filepath (Path): Path to the JSON file.
        mime_type (str): Initial MIME type.

    Returns:
        tuple[str, SubType | None]: (MIME type, detected subtype) for the file.
    """
    subtype = None
    json_type = guess_json_format(filepath)
    if json_type in MIMETYPES:
        mime_type = MIMETYPES[json_type]
        subtype = json_type
    return (mime_type,subtype)
