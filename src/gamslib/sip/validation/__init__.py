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

from pathlib import Path
import re
import urllib
from .. import BagValidationError
from .baginfo import validate_baginfo_text
from .bagit import validate_bagit_txt, validate_structure
from .manifests import (
    validate_manifest_md5,
    validate_manifest_sha512,
)
from .sip_json import validate_sip_json

def is_valid_id(pid: str, allow_uppercase: bool = False) -> bool:
    """
    Check if the given ID (PID, DSID) is valid.

    This follows the rules of xml:id, with some modifications:

     - Every id must have the project sigle as prefix, followed by a dot. 
       The prefix must start with a letter, followed by any number of letters and numbers.
     - The part after the dot must start with a letter or a number, followed by any 
       number of ASCII letters, numbers, dots, dashes and underscores.
     - For legacy reasons, the project prefix can be proceeded by a type prefix like 'o:'
       but we discourage the use of this prefix for new objects.

    So a valid ids are for example:

        - abc.def123
        - abc.123-def
        - abc.123_456

    An id like "o:abc.123" is also valid, but we discourage the use of the "o:" prefix.

    Invalid ids are for example:

        - .abcdef  (starts with a dot)
        - 1abcdef (starts with a number)
        - abc/def (contains invalid character '/')
        - abc@def (contains invalid character '@')
        - abcdef  (no dot)
        - abc..def (double dot)    

    Args:
        pid (str): The ID to validate.

    Returns:
        bool: True if the ID is valid, False otherwise.
    """
    # If we store a pid to a file name, we replace : with %3A
    # We transform it back before validating because we use 
    # this function also for validating file names
    # in the object directory.
    decoded_pid = pid.replace("%3A", ":")
    #              o:foo1.bar-123_baz
    if '..' in decoded_pid or '--' in decoded_pid or '__' in decoded_pid:
        return False
    # Regex explanation:
    # ^([a-z]+:)?      - optional type prefix (e.g., 'o:') with lowercase letters only
    # [a-z][a-z0-9_.-]* - project prefix starting with a letter, followed by letters, numbers, underscores, dots, or dashes
    # \.               - literal dot separator
    # [a-z0-9][a-z0-9_.-]*$ - object identifier starting with a letter or number, followed by letters, numbers, underscores, dots, or
    pattern = r'^([a-z]+:)?[a-z][a-z0-9_.-]*\.[a-z0-9][a-z0-9_.-]*$'
    if allow_uppercase:
        m = re.match(pattern, decoded_pid, re.IGNORECASE)
    else:
        m = re.match(pattern, decoded_pid)
    return m is not None


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
