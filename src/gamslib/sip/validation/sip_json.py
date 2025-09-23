"""Validation of the sip.json file.
This module provides functions to validate the `sip.json` file in a GAMS packaging context.
"""

import json
from pathlib import Path

import jsonschema
import referencing

from .. import BagValidationError, utils


def validate_main_resource(data: dict) -> None:
    """Make sure the object main resource id is listed in the contentFiles.

    Raises a BagValidationError if the mainResource is not listed in contentFiles.
    """
    mainresource = data.get("mainResource", "")
    known_ds_ids = [content_file["dsid"] for content_file in data["contentFiles"]]
    if mainresource and mainresource not in known_ds_ids:
        raise BagValidationError(
            f"mainResource '{data['mainResource']}' is not listed in contentFiles"
        )


def validate_sip_json(bag_dir: Path) -> None:
    """Validate the sip.json file.

    Raises a BagValidationError if the sip.json file is invalid.
    """
    sip_json_file = bag_dir / "data" / "meta" / "sip.json"
    if not sip_json_file.is_file():
        raise BagValidationError(f"{bag_dir}: sip.json file does not exist")
    try:
        data = json.load(sip_json_file.open(encoding="utf-8", newline=""))
    except json.JSONDecodeError as e:
        raise BagValidationError(f"Invalid JSON in sip.json: {e}") from e

    if "$schema" not in data:
        raise BagValidationError(f"{bag_dir}: Missing '$schema' in sip.json")

    schema = utils.fetch_json_schema(data["$schema"])

    # do  the real validation
    try:
        jsonschema.validate(data, schema)
        validate_main_resource(data)
    except jsonschema.ValidationError as e:
        raise BagValidationError(f"Invalid JSON in sip.json: {e}") from e
    except jsonschema.SchemaError as e:
        raise BagValidationError(
            f"{bag_dir}: The JSON Schema referenced in 'sip.json' is not valid: {e}"
        ) from e
    except referencing.exceptions.Unresolvable as e:
        raise BagValidationError(
            f"Failed to resolve a reference in the JSON Schema: {e}"
        ) from e
