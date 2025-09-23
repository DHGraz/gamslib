"""Validation for bagit and object directories."""

from pathlib import Path
#from gamspackaging import utils
from .. import BagValidationError
from .baginfo import validate_baginfo_text
from .bagit import validate_bagit_txt, validate_structure
from .manifests import (
    validate_manifest_md5,
    validate_manifest_sha512,
)
from .sip_json import validate_sip_json


def validate_bag(bag_dir: Path) -> None:
    """Validate the Bagit directory.

    Raises a BagValidationError if the bag is invalid.
    """
    if not bag_dir.is_dir():
        raise BagValidationError(f"Bag directory {bag_dir} does not exist")
    validate_structure(bag_dir)
    validate_bagit_txt(bag_dir)
    validate_manifest_md5(bag_dir)
    validate_manifest_sha512(bag_dir)
    validate_sip_json(bag_dir)
    validate_baginfo_text(bag_dir)
