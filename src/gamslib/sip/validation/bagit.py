"""Validate the structure and contents of a bagit directory.
This module provides functions to validate the general structure of a bagit directory,
the contents of the bagit.txt file, and the existence of required directories and files.
"""

from pathlib import Path

from .. import BagValidationError


def validate_structure(bag_dir: Path) -> None:
    """Validate the general structure of the bagit directory.

    Existence of the required directories and files are checked.
    Raises BagValidationError if a required directory or file is missing.
    """
    required_dirs = ["data", "data/meta", "data/content"]
    required_files = [
        "bagit.txt",
        "manifest-md5.txt",
        "manifest-sha512.txt",
        "data/meta/sip.json",
        "data/content/DC.xml",
    ]

    for directory in required_dirs:
        if not (bag_dir / directory).is_dir():
            raise BagValidationError(f"Bag directory '{directory}' does not exist")

    for file in required_files:
        if not (bag_dir / file).is_file():
            raise BagValidationError(
                f"Bag file '{file}' does not exist for bag {bag_dir}"
            )


def validate_bagit_txt(bag_dir: Path) -> None:
    """Validate the bagit.txt file.

    Raises BagValidationError if the bagit.txt file is invalid.
    """
    bagit_txt_file = bag_dir / "bagit.txt"
    if not bagit_txt_file.is_file():
        raise BagValidationError(
            "'bagit.txt' file does not exist in the bag directory {bag_dir}"
        )
    line_entries = []
    with bagit_txt_file.open("r", encoding="utf-8", newline="") as f:
        for i, line in enumerate(f, start=1):
            try:
                stripped_line = line.rstrip()
                if stripped_line:
                    key, value = stripped_line.split(":", 1)
                    line_entries.append((key, value.strip()))
            except ValueError as e:
                raise BagValidationError(
                    f"Invalid line {i} in {bag_dir / 'bagit.txt'}: '{stripped_line}'"
                ) from e

    if len(line_entries) != 2:  # noqa: PLR2004
        raise BagValidationError(
            f"{bag_dir / 'bagit.txt'} has invalid number of lines. bagit.txt is incomplete"
        )

    if line_entries[0][0] != "BagIt-Version":
        raise BagValidationError(
            f"{bag_dir / 'bagit.txt'}: Missing line for 'BagIt-Version'"
        )

    if line_entries[0][1] != "1.0":
        raise BagValidationError(
            f"{bag_dir / 'bagit.txt'}: Invalid value for 'BagIt-Version'. Must be '1.0'"
        )

    if line_entries[1][0] != "Tag-File-Character-Encoding":
        raise BagValidationError(
            f"{bag_dir / 'bagit.txt'}: Missing line for 'Tag-File-Character-Encoding'"
        )

    if line_entries[1][1] != "UTF-8":
        raise BagValidationError(
            f"{bag_dir / 'bagit.txt'}: Invalid value for 'Tag-File-Character-Encoding'. "
            "Must be 'UTF-8'"
        )
