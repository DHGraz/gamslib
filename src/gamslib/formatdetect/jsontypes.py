"Module to inspect json files."

import json
from pathlib import Path

from gamslib.formatdetect.formatinfo import SubType


# These MIME Types (als returned be a detection tool are handled as JSON files.)
# This is an extension to the MIMETYPES dict, as some mime types listed here, are not
# yet registered, but might be used by some format detection tools. Feel free to add more.
JSON_MIME_TYPES = [
    "application/json",
    "application/ld+json",
    "application/schema+json",
    "application/jsonl",
]


# I commented out some entries which are not yet registered with IANA.
MIMETYPES = {
    SubType.JSON: "application/json",
    SubType.JSONLD: "application/ld+json",
    # The suggest mime type is application/schema+json, but it is not registered yet
    # SubType.JSONSCHEMA: "application/schema+json",
    SubType.JSONSCHEMA: "application/json",
    # The suggest mime type is application/jsonl, but it is not registered yet
    # SubType.JSONL: "application/jsonl"
    SubType.JSONL: "application/json",
}


def is_json_type(mime_type: str) -> bool:
    """Check if a mime type is a JSON type."""
    return mime_type in JSON_MIME_TYPES or mime_type in MIMETYPES.values()


def is_jsonl(data: str) -> bool:
    """Check if a file is a JSON lines file (jsonl).

    As this function is thought to be used primarily by the 'guess_json_format' function.
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
    """Guess the format of a JSON file.

    Returns:
        One of the formats defined in jsontypes.JSONTypes:
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
    # if file contains jsonl context, parsing will fail
    except json.JSONDecodeError as exp:
        if is_jsonl(file_content):
            return SubType.JSONL
        raise exp from exp  # eg. invalid JSON
    return SubType.JSON


def get_format_info(filepath: Path, mime_type: str) -> tuple[str, SubType | None]:
    """Return a tuple with (possibly fixed) mimetype and subtype."""
    subtype = None
    json_type = guess_json_format(filepath)
    if json_type in MIMETYPES:
        mime_type = MIMETYPES[json_type]
        subtype = json_type
    return mime_type, subtype
