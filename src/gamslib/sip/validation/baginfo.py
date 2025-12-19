"""Validation functions for the bag-info.txt file in GAMS Bagit directories.

This module provides functions to validate the contents of the bag-info.txt file
and ensure that all required entries are present and correctly formatted.

Features:
    - Checks for required fields in bag-info.txt.
    - Validates date, time, payload oxum, email, and description fields.
    - Reads bag-info.txt as a list of (key, value) tuples to support duplicate keys.
    - Raises BagValidationError for any validation failures.

Usage:
    Call `validate_baginfo_text(bag_dir)` to validate the bag-info.txt file in a Bagit directory.
    Individual validation functions are also available for more granular checks.
"""

from datetime import datetime
from pathlib import Path
import re

from .. import utils, BagValidationError


def validate_required_baginfo_entries(entries: list[tuple[str, str]]) -> None:
    """
    Check if all required values are present in the bag-info.txt file.

    Args:
        entries (list[tuple[str, str]]): List of (key, value) tuples from bag-info.txt.

    Raises:
        BagValidationError: If a required entry is missing.
    """
    required_keys = [
        "Bagging-Date",
        "Payload-Oxum",
        "Contact-Email",
        "External-Description",
    ]

    existing_keys = [key for key, _ in entries]
    for key in required_keys:
        if key not in existing_keys:
            raise BagValidationError(f"Missing required entry '{key}' in bag-info.txt")


def validate_bagging_date(value: str) -> None:
    """
    Check if the value for 'Bagging-Date' is a valid date.

    Args:
        value (str): Value to validate.

    Raises:
        BagValidationError: If the value is not a valid date.
    """
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as e:
        raise BagValidationError(
            f"Value for 'Bagging-Date' is not a valid date: {value}"
        ) from e
    return True


def validate_payload_oxum(value: str, bag_dir: Path) -> None:
    """
    Check the value for 'Payload-Oxum'.

    The value must be in the format 'size.file_count'.
    The size must match the actual size of the payload.
    The file_count must match the actual number of files in the payload.

    Args:
        value (str): Value to validate.
        bag_dir (Path): Path to the Bagit directory.

    Raises:
        BagValidationError: If the value is not valid or does not match the payload.
    """
    parts = value.split(".")
    if len(parts) != len(["size", "file_count"]):
        raise BagValidationError(
            f"Value for 'Payload-Oxum' is not valid: {value}. "
            "It must be in the format 'size.file_count'."
        )
    if not all(part.isdigit() for part in parts):
        raise BagValidationError(
            f"Value for 'Payload-Oxum' is not valid: {value}. "
            "Both size and file_count must be integers."
        )
    size, file_count = value.split(".")
    size = int(size)
    real_size = utils.count_bytes(bag_dir / "data")
    if real_size != size:
        raise BagValidationError(
            (
                f"{bag_dir}: "
                f"Value for 'Payload-Oxum' ({size}) does not match "
                f"the actual payload size: {real_size}"
            )
        )
    real_file_count = utils.count_files(bag_dir / "data")
    if real_file_count != int(file_count):
        raise BagValidationError(
            (
                f"{bag_dir}: "
                f"Value for 'Payload-Oxum' ({file_count}) does not match "
                f"the actual number of files: {real_file_count}"
            )
        )


def validate_contact_email(value: str) -> None:
    """
    Check the value for 'Contact-Email'.

    Args:
        value (str): Value to validate.

    Raises:
        BagValidationError: If the value is not a valid email address.
    """
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}$"
    if not re.match(pattern, value):
        raise BagValidationError(
            f"Value for 'Contact-Email' is not a valid email address: {value}"
        )


def validate_external_description(value: str) -> None:
    """
    Check the value for 'External-Description'.

    Args:
        value (str): Value to validate.

    Raises:
        BagValidationError: If the value is empty.
    """
    if not value.strip():
        raise BagValidationError("Value for 'External-Description' must not be empty")


def read_baginfo_txt(baginfo_txt_file: Path) -> list[tuple[str, str]]:
    """
    Read the bag-info.txt file and return a list of tuples (key, value) with its entries.

    Args:
        baginfo_txt_file (Path): Path to the bag-info.txt file.

    Returns:
        list[tuple[str, str]]: List of (key, value) tuples from the file.

    Notes:
        - Uses a list of tuples instead of a dict, because the same key can appear multiple times.
        - Raises BagValidationError if a line is invalid or missing a colon.
    """
    entries = []

    with baginfo_txt_file.open("r", encoding="utf-8", newline="") as f:
        for i, line in enumerate(f, start=1):
            try:
                stripped_line = line.rstrip()
                if line:
                    key, value = [x.strip() for x in stripped_line.split(":", 1)]
                    entries.append((key, value))
            except ValueError as e:  # missing colon
                raise BagValidationError(
                    f"Invalid line {i} in '{baginfo_txt_file}': '{stripped_line}'"
                ) from e
    return entries


def validate_baginfo_text(bag_dir: Path) -> None:
    """
    Validate the bag-info.txt file in a Bagit directory.

    Args:
        bag_dir (Path): Path to the Bagit directory.

    Raises:
        BagValidationError: If the bag-info.txt file is missing or invalid.

    Notes:
        - Checks for required entries and validates their values.
        - Raises an error immediately if any check fails.
    """
    baginfo_txt_file = bag_dir / "bag-info.txt"

    if not baginfo_txt_file.is_file():
        raise BagValidationError("bag-info.txt file does not exist")

    # read the bag-info.txt file
    entries = read_baginfo_txt(baginfo_txt_file)

    # check if all required entries are present
    validate_required_baginfo_entries(entries)

    # check the values of the required entries
    for key, value in entries:
        if key == "Bagging-Date":
            validate_bagging_date(value)
        elif key == "Payload-Oxum":
            validate_payload_oxum(value, bag_dir)
        elif key == "Contact-Email":
            validate_contact_email(value)
        elif key == "External-Description":
            validate_external_description(value)
