"Utility functions for the gamspackaging package."

import hashlib
import logging
import os
import re
from pathlib import Path
from typing import Generator

import requests

# from gamslib.objectcsv.datastreamscsvfile import DatastreamsCSVFile
# from gamslib.objectcsv.objectcsvfile import ObjectCSVFile
from gamslib.objectcsv.objectcsvmanager import ObjectCSVManager

from . import BagValidationError, ObjectDirectoryValidationError

logger = logging.getLogger(__name__)


def validate_object_dir(object_path: Path) -> None:
    """Check if everything we need is in the object directory.

    Raise a ObjectDirectoryValidationError if the directory is not valid.
    """
    if not object_path.is_dir():
        raise ObjectDirectoryValidationError(
            f"Object directory '{object_path}' does not exist or is not a directory."
        )

    if not (object_path / "DC.xml").exists():
        raise ObjectDirectoryValidationError(
            f"Object directory '{object_path}' does contain a DC.xml file."
        )

    # TODO: validate the DC.xml file? Do we require some fields?

    # Check the object.csv file
    objfile = object_path / "object.csv"
    if not objfile.exists():
        raise ObjectDirectoryValidationError(
            f"Object directory '{object_path}' does not contain an object.csv file."
        )
    # use the ObjectCSVFile class to validate contents of the object.csv file
    csv_mgr = ObjectCSVManager(object_path)
    csv_mgr.validate()


def find_object_folders(root_folder: Path) -> Generator[Path, None, None]:
    """Find all object folders in the root folder or below."""
    for root, _, files in os.walk(root_folder):
        if "DC.xml" in files:
            yield Path(root)
        elif not files or "project.toml" not in files:
            logger.warning(
                "Skipping folder %s as it does not contain a DC.xml file.", root
            )


def extract_id(path: Path | str, remove_extension=False) -> str:
    """Extract and validate the ID (PID, DSID) from the object or datastream path.

    If remove_extension is True, the file extension is removed from the PID.
    """
    if isinstance(path, str):
        path = Path(path)
    pid = path.name

    if re.match(r"^[a-zA-Z0-9]+[-.%_a-zA-Z0-9]+[a-zA-Z0-9]+$", pid):
        if remove_extension:
            # not everything after the last dot is an extension :-(
            parts = pid.split(".")
            if re.match(r"^[a-zA-Z]+\w?$", parts[-1]):
                pid = ".".join(parts[:-1])
                logger.debug("Removed extension for ID: %s", parts[0])
            else:
                logger.warning(
                    "'%s' does not look like an extension. Keeping it in PID.", pid[-1]
                )
            return pid
        logger.debug(
            "Extracted PID: %s from %s (remove_extension=%s)",
            pid,
            path,
            remove_extension,
        )
        return pid

    raise ValueError(f"Invalid PID: '{pid}'")


def md5hash(file: Path) -> str:
    """Calculate the MD5 hash of a file."""
    return hashlib.md5(file.read_bytes()).hexdigest()


def sha512hash(file: Path) -> str:
    """Calculate the SHA512 hash of a file."""
    return hashlib.sha512(file.read_bytes()).hexdigest()


def sha256hash(file: Path) -> str:
    """Calculate the SHA256 hash of a file."""
    return hashlib.sha256(file.read_bytes()).hexdigest()


def count_bytes(root_dir: Path) -> int:
    """Count the number of bytes of all files below root_dir."""
    total_bytes = 0
    for file in root_dir.rglob("*"):
        if file.is_file():
            total_bytes += file.stat().st_size
    return total_bytes


def count_files(root_dir: Path) -> int:
    """Count the number of all files below root_dir."""
    total_files = 0
    for file in root_dir.rglob("*"):
        if file.is_file():
            total_files += 1
    return total_files


def fetch_json_schema(url: str) -> dict:
    """Fetch a JSON schema from a URL."""
    try:
        response = requests.get(url, timeout=20)
        if not response.ok:
            raise BagValidationError(
                f"Failed to fetch JSON schema from '{url}': HTTP status code {response.status_code}"
            )
    except requests.RequestException as e:
        raise BagValidationError(
            f"Failed to fetch JSON schema from '{url}': {e}"
        ) from e

    try:
        return response.json()
    except requests.JSONDecodeError as e:
        raise BagValidationError(
            f"Schema referenced in 'sip.json' is not valid JSON: {e}"
        ) from e
