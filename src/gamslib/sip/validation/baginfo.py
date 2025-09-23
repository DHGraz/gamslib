"""Validate the bag-info.txt file in a GAMS bag."

This module provides functions to validate the contents of the bag-info.txt file
and ensure that all required entries are present and correctly formatted.
"""

from datetime import datetime
from pathlib import Path
import re

from .. import utils, BagValidationError


def validate_required_baginfo_entries(entries: list[tuple[str, str]]) -> None:
    """Check if all required values are present in the bag-info.txt file.

    Raises a BagValidationError if a required entry is missing.
    """
    required_keys = [
        "Bagging-Date",
        "Bagging-Time",
        "Payload-Oxum",
        "Contact-Email",
        "External-Description",
    ]

    existing_keys = [key for key, _ in entries]
    for key in required_keys:
        if key not in existing_keys:
            raise BagValidationError(f"Missing required entry '{key}' in bag-info.txt")


def validate_bagging_date(value: str) -> None:
    """Check if the value for 'Bagging-Date' is a valid date.

    Raises a BagValidationError if the value is not a valid date.
    """
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as e:
        raise BagValidationError(
            f"Value for 'Bagging-Date' is not a valid date: {value}"
        ) from e
    return True


def validate_bagging_time(value: str) -> None:
    """Check if the value for 'Bagging-Time' is a valid time.

    Raises a BagValidationError if the value is not a valid time.
    """
    try:
        datetime.strptime(value, "%H:%M:%S %Z")
    except ValueError:
        # On some systems, the %Z directive is not supported. We can check the timezone separately.
        try:
            parts = value.split()
            datetime.strptime(parts[0], "%H:%M:%S")
            return
        except ValueError as exp:
            raise BagValidationError(
                f"Value for 'Bagging-Time' is not a valid time: {value}"
            ) from exp


def validate_payload_oxum(value: str, bag_dir: Path) -> None:
    """Check the value for 'Payload-Oxum'.

    The value must be in the format 'size.file_count'.
    The size must match the actual size of the payload.
    The file_count must match the actual number of files in the payload.

    Raises a BagValidationError if the value is not valid.
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
    """Check the value for 'Contact-Email'.

    Raises a BagValidationError if the value is not a valid email address.
    """
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}$"
    if not re.match(pattern, value):
        raise BagValidationError(
            f"Value for 'Contact-Email' is not a valid email address: {value}"
        )


def validate_external_description(value: str) -> None:
    """Check the value for 'External-Description'.

    Raises a BagValidationError if the value is empty.
    """
    if not value.strip():
        raise BagValidationError("Value for 'External-Description' must not be empty")


def read_baginfo_txt(baginfo_txt_file: Path) -> list[tuple[str, str]]:
    """Read the bag-info.txt file and return a list of tuples (key, value) with its entries.
    We us a List of tuples and not a dict, because the same key can appear multiple times.

    This is a helper function for validate_baginfo_text.
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
    """Validate the bag-info.txt file.

    Returns True if the bag-info.txt file is valid.
    Raises a BagValidationError if the bag-info.txt file is invalid.
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
        elif key == "Bagging-Time":
            validate_bagging_time(value)
        elif key == "Payload-Oxum":
            validate_payload_oxum(value, bag_dir)
        elif key == "Contact-Email":
            validate_contact_email(value)
        elif key == "External-Description":
            validate_external_description(value)
