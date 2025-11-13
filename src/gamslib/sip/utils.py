"""Utility functions for the GAMS SIP package creation and validation.

Provides helpers for validating object directories, extracting IDs, calculating hashes,
counting files and bytes, and fetching JSON schemas for validation.

Features:
    - Validates object directory structure and required files.
    - Extracts and validates object and datastream IDs.
    - Calculates MD5, SHA512 hashes for files.
    - Counts files and bytes in a directory tree.
    - Fetches and parses JSON schemas from URLs, with error handling.

Usage:
    Use `validate_object_dir(object_path)` to check an object directory.
    Use `extract_id(path)` to extract and validate an object or datastream ID.
    Use `md5hash(file)`, `sha512hash(file)`, or `sha256hash(file)` for file checksums.
    Use `count_bytes(root_dir)` or `count_files(root_dir)` for directory statistics.
    Use `fetch_json_schema(url)` to retrieve a JSON schema from a remote URL.
"""

import hashlib
import json
import logging
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Generator
import warnings
import zipfile

import requests

from gamslib.objectcsv.objectcsvmanager import ObjectCSVManager

from . import BagValidationError, ObjectDirectoryValidationError
from .validation import validate_pid

logger = logging.getLogger(__name__)

GAMS_SIP_SCHEMA_URL = "https://gams.uni-graz.at/OAIS/sip-schema-d1.json"

# This is the path were the schema is stored in the package
SCHEMA_PATH = Path(__file__).parent / "resources" / "sip-schema-d1.json"


def validate_object_dir(object_path: Path) -> None:
    """
    Check if everything needed is present in the object directory.

    Args:
        object_path (Path): Path to the object directory.

    Raises:
        ObjectDirectoryValidationError: If the directory or required files are missing,
            or if object.csv is invalid.
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
    """
    Find all object folders in the root folder or below.

    Args:
        root_folder (Path): Root directory to search for object folders.

    Yields:
        Path: Path to each object folder containing a DC.xml file.

    Notes:
        - Skips folders that do not contain a DC.xml file and logs a warning.
    """
    for root, _, files in os.walk(root_folder):
        if "DC.xml" in files:
            yield Path(root)
        elif not files or "project.toml" not in files:
            logger.warning(
                "Skipping folder %s as it does not contain a DC.xml file.", root
            )


# def extract_object_id_from_path(path: Path | str) -> str:
#     """
#     Extract the object ID (PID) from a path (pointing to the object directory).

#     Args:
#         path (Path | str): Path or filename of the object.

#     Returns:
#         str: The extracted ID.
#     """
#     if isinstance(path, str):
#         path = Path(path)
#     pid = path.name

#     if remove_extension:
#         # not everything after the last dot is an extension :-(
#         parts = pid.split(".")
#         if re.match(r"^[a-zA-Z]+\w?$", parts[-1]):
#             pid = ".".join(parts[:-1])
#             logger.debug("Removed extension for ID: %s", parts[0])
#         else:
#             logger.warning(
#                 "'%s' does not look like an extension. Keeping it in PID.", pid[-1]
#             )
#     logger.debug(
#         "Extracted PID: %s from %s (remove_extension=%s)",
#         pid,
#         path,
#         remove_extension,
#     )
#     # TODO: is this the right place to validate the ID?
#     try:
#         validate_pid(pid)
#         return pid
#     except ValueError as exp:
#         raise ValueError(f"Invalid PID: '{pid}: {exp}'") from exp


def md5hash(file: Path) -> str:
    """
    Calculate the MD5 hash of a file.

    Args:
        file (Path): Path to the file.

    Returns:
        str: MD5 hash as a hexadecimal string.
    """
    return hashlib.md5(file.read_bytes()).hexdigest()


def sha512hash(file: Path) -> str:
    """
    Calculate the SHA512 hash of a file.

    Args:
        file (Path): Path to the file.

    Returns:
        str: SHA512 hash as a hexadecimal string.
    """
    return hashlib.sha512(file.read_bytes()).hexdigest()


def count_bytes(root_dir: Path) -> int:
    """
    Count the number of bytes of all files below root_dir.

    Args:
        root_dir (Path): Directory to count bytes in.

    Returns:
        int: Total number of bytes in all files.
    """
    total_bytes = 0
    for file in root_dir.rglob("*"):
        if file.is_file():
            total_bytes += file.stat().st_size
    return total_bytes


def count_files(root_dir: Path) -> int:
    """
    Count the number of all files below root_dir.

    Args:
        root_dir (Path): Directory to count files in.

    Returns:
        int: Total number of files.
    """
    total_files = 0
    for file in root_dir.rglob("*"):
        if file.is_file():
            total_files += 1
    return total_files


def read_sip_schema_from_package():
    """
    Read the SIP JSON schema from the package data.

    The schema file is located in the sip subpackage under the resources directory.

    Returns:
        dict: Parsed JSON schema.
    """
    with SCHEMA_PATH.open() as f:
        return json.load(f)


@lru_cache()
def fetch_json_schema(url: str) -> dict:
    """
    Fetch a JSON schema from a URL.

    Args:
        url (str): URL to fetch the JSON schema from.

    Returns:
        dict: Parsed JSON schema.

    Raises:
        BagValidationError: If the schema cannot be fetched or is not valid JSON.
    """
    if url == GAMS_SIP_SCHEMA_URL:
        logger.debug("Using embedded GAMS SIP schema")
        return read_sip_schema_from_package()
    try:
        logger.debug("Fetching JSON schema from %s", url)
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
    except (
        requests.JSONDecodeError,
        requests.exceptions.InvalidJSONError,
        TypeError,
    ) as e:
        raise BagValidationError(
            f"Schema referenced in 'sip.json' is not valid JSON: {e}"
        ) from e


def is_bag(bag_path: Path) -> bool:
    """Check if the given path points to a Bag.

    It does not check the validity of the Bag, only if the structure indicates
    that it looks like a Bag.

    To check the validity of the Bag, unpack it using the unpack function
    and use the validate_object_dir function.

    pag_path can be either a directory or a file (zip).

    Args:
        bag_path (Path): The path to the directory to check.

    Returns:
        bool: True if the path points to a Bag, False otherwise.
    """
    expected_files = {
        "bagit.txt",
        "manifest-md5.txt",
        "manifest-sha512.txt",
        "data/meta/sip.json",
    }
    looks_like_a_bag = False
    all_files = set()
    if bag_path.is_dir():
        all_files = {
            file_path.relative_to(bag_path).as_posix()
            for file_path in bag_path.rglob("*")
        }
    elif bag_path.is_file() and bag_path.suffix == ".zip":
        with zipfile.ZipFile(bag_path, "r") as zip_ref:
            all_files = set(zip_ref.namelist())
    if expected_files.issubset(all_files):
        looks_like_a_bag = True
    else:
        missing_files = expected_files - all_files
        warnings.warn(
            f"Path {bag_path} is missing expected Bag files: "
            f"{', '.join(sorted(missing_files))}"
        )
        looks_like_a_bag = False
    return looks_like_a_bag
