"""Validation utilities for Bagit and object directories in GAMS projects.

This subpackage provides functions to validate the structure and metadata of Bagit directories,
including checks for required files, manifests, and SIP JSON metadata.

Features:
    - Validates Bagit directory structure and required files.
    - Checks bagit.txt, bag-info.txt, and manifest files (MD5, SHA512).
    - Validates SIP JSON metadata for completeness and correctness.
    - Raises BagValidationError for any validation failures.

Usage:
    Call `validate_bag(bag_dir)` to perform all standard validations on a Bagit directory.
    Individual validation functions are also available for more granular checks.
"""

import re
import urllib
from pathlib import Path
import warnings

from .. import BagValidationError
from .baginfo import validate_baginfo_text
from .bagit import validate_bagit_txt, validate_structure
from .manifests import (
    validate_manifest_md5,
    validate_manifest_sha512,
)
from .sip_json import validate_sip_json


def _split_id(pid: str) -> tuple[str, str, str]:
    """
    Split a given ID into type prefix, project prefix, and object identifier.

    This is a helper function for the is_valid_id function.

    so a pid like "o:abc.def123" will be split into:
        - type_prefix: "o"
        - project_prefix: "abc"
        - object_identifier: "def123"

    Args:
        pid (str): The ID to split.

    Raises:
        ValueError: If the ID is not splitable
    Returns:
        tuple: A tuple containing (type_prefix, project_prefix, object_identifier).
               type_prefix is empty string if not present.
    """
    if not "." in pid:
        raise ValueError(
            "ID must contain a dot (.) separating project prefix and object identifier"
        )
    if (
        pid[0] == "."
    ):  # we have to keep the dot if it is the first char (will fail later)
        return "", "", pid
    prefix, object_id = pid.split(".", 1)
    # Decode percent-encoded colon if present
    cleaned_prefix = prefix.replace("%3A", ":")
    # if prefix starts with colon, it is not a type prefix
    if ":" in cleaned_prefix and cleaned_prefix[0] != ":":
        type_prefix, project_prefix = cleaned_prefix.split(":", 1)
    else:
        type_prefix, project_prefix = "", cleaned_prefix
    return type_prefix, project_prefix, object_id


def _validate_type_prefix(type_prefix: str) -> None:
    """
    Validate the type prefix of an ID.

    The type prefix is the part before the colon (:) in an ID like "o:abc.def123".
    It must contain only lowercase letters or be empty.

    Args:
        type_prefix (str): The type prefix to validate.
    Raises:
        ValueError: If the type prefix is invalid.
    """
    # the commented out prefixes are legacy prefixes which
    # do not make sense in GAMS5+. Keep them
    # here for reference, but currently do not allow them.
    allowed_type_prefixes = [
        "",
        "collection",
        "container",
        "context",
        "corpus",
        "o",
        "podcast",
        "query",
        # "FgsConfig",
        # "cirilo",
        # "cm",
        # "fedora-system",
        # "sdef",
        # "sdep",
    ]
    if type_prefix not in allowed_type_prefixes:
        raise ValueError(
            f"The type prefix ('{type_prefix}') is not allowed. "
            f"Allowed prefixes are: {', '.join(allowed_type_prefixes)}"
            "Note: Using types prefixes is discouraged for new objects."
        )


def validate_project_name(value: str) -> None:
    """
    Validate the project name. Can also be used to validate the project prefix of a PID.

    The value must start with a letter, followed by any number of letters and numbers.
    The project prefix is the part before the dot (.) in an ID like "abc.def123".

    Args:
        value (str): The project prefix to validate.

    Raises:
        ValueError: If the project prefix is invalid.
    """
    if not value:
        raise ValueError("Project prefix (before dot) is empty")

    if not re.match(r"^[a-z][a-z0-9]*$", value):
        raise ValueError(
            "A project name must start with a letter and contain "
            "only lowercase letters and numbers."
        )


def _validate_object_id(object_id: str) -> None:
    """
    Validate the object identifier of an ID.

    The object identifier is the part after the first dot (.) in an ID like "abc.def123".
    It must start with a letter or a number, followed by any number of letters, numbers,
    dots, dashes, or underscores.
    Consecutive dots, underscores, or dashes are not allowed.

    Args:
        object_id (str): The object identifier to validate.
        allow_uppercase (bool, optional): If True, allow uppercase letters in object identifier. Defaults to False.
            Object identifiers should normally be lowercase only.

    Raises:
        ValueError: If the object identifier is invalid.
    """
    if not object_id:
        raise ValueError("Object identifier (after dot) is empty")
    if ".." in object_id:
        raise ValueError(
            "Object identifier (after dot) must not contain consecutive dots"
        )
    if "--" in object_id:
        raise ValueError(
            "Object identifier (after dot) must not contain consecutive dashes"
        )

    if not re.match(r"^[a-z0-9][a-z0-9.-]*$", object_id):
        raise ValueError(
            "Object identifier (after dot) must start with a letter or number and "
            "contain only lowercase letters, numbers, dots or dashes"
        )


def validate_pid(pid: str) -> None:
    """Validate a given PID (Project Identifier).

    A valid id follows the rules of xml:id, with some modifications:

     - All letters must be lowercase ASCII letters.
     - Every id must have the project sigle as prefix, followed by a dot.
       The prefix must start with a letter, followed by any number
       of letters and numbers.
     - The part after the dot must start with a letter or a number, followed by any
       number of ASCII letters, numbers, dots, and dashes.
     - For legacy reasons, the project prefix can be proceeded by a type prefix like 'o:'
       but we discourage the use of this prefix for new objects. Only lowercase letters are allowed as
       type prefix.

    Invalid ids are for example:

        - .abcdef  (starts with a dot)
        - 1abcdef (starts with a number)
        - abc/def (contains invalid character '/')
        - abc@def (contains invalid character '@')
        - abcdef  (no dot)
        - abc..def (double dot)

    Args:
        pid (str): The ID to validate.
        allow_uppercase (bool, optional): If True, allow uppercase letters in pid. Defaults to False.
            Object IDs (PIDs) should normally be lowercase only, but datastream id can be uppercase too.

    Raises:
        ValueError: If the ID is invalid. The error message will indicate the reason.
    """
    max_id_length = 64
    # Check if the PID is a valid URI
    if len(pid) > max_id_length:
        raise ValueError(f"ID must not be longer than {max_id_length} characters")
    type_prefix, project_prefix, object_id = _split_id(pid)
    _validate_type_prefix(type_prefix)
    validate_project_name(project_prefix)
    _validate_object_id(object_id)
    if type_prefix:
        warnings.warn(
            "Using type prefixes in PIDs is discouraged for new objects.", UserWarning
        )


def validate_datastream_id(datastream_id: str) -> None:
    """Validate a given datastream ID.

    A valid datastream is must start with a letter or a number, followed by any
    number of ASCII letters, numbers, dots, and dashes. 

    Args:
        datastream_id (str): The datastream ID to validate.

    Raises:
        ValueError: If the datastream ID is invalid. The error message will indicate the reason.
    """
    if not datastream_id:
        raise ValueError("Object identifier (after dot) is empty")
    if ".." in datastream_id:
        raise ValueError(
            "Datastream identifier (after dot) must not contain consecutive dots"
        )
    if "--" in datastream_id:
        raise ValueError(
            "Datastream identifier (after dot) must not contain consecutive dashes"
        )

    if not re.match(r"^[a-z0-9][a-z0-9.-]*$", datastream_id, re.IGNORECASE):
        raise ValueError(
            "Datastream identifier must start with a letter or number and "
            "contain only letters, numbers, dots or dashes"
        )




def validate_bag(bag_dir: Path) -> None:
    """
    Validate the structure and metadata of a Bagit directory.

    Args:
        bag_dir (Path): Path to the Bagit directory to validate.

    Raises:
        BagValidationError: If the bag directory does not exist or any validation check fails.

    Notes:
        - Runs all standard validation checks: structure, bagit.txt, manifests, SIP JSON, and bag-info.txt.
        - Raises an error immediately if any check fails.
    """
    if not bag_dir.is_dir():
        raise BagValidationError(f"Bag directory {bag_dir} does not exist")
    validate_structure(bag_dir)
    validate_bagit_txt(bag_dir)
    validate_manifest_md5(bag_dir)
    validate_manifest_sha512(bag_dir)
    validate_sip_json(bag_dir)
    validate_baginfo_text(bag_dir)
