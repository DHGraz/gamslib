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
from .. import BagValidationError
from .baginfo import validate_baginfo_text
from .bagit import validate_bagit_txt, validate_structure
from .manifests import (
    validate_manifest_md5,
    validate_manifest_sha512,
)
from .sip_json import validate_sip_json


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
