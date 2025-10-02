"""Validation functions for manifest files in Bagit directories for GAMS projects.

This module provides functions to validate the manifest-md5.txt and manifest-sha512.txt files
in a Bagit directory, ensuring that all payload files are listed and checksums are correct.

Features:
    - Validates manifest-md5.txt and manifest-sha512.txt files.
    - Checks that all files in the data directory are listed in the manifests.
    - Verifies that checksums match the actual file contents.
    - Raises BagValidationError for any validation failures.

Usage:
    Call `validate_manifest_md5(bag_dir)` to validate the MD5 manifest.
    Call `validate_manifest_sha512(bag_dir)` to validate the SHA512 manifest.
"""

import hashlib
from pathlib import Path

from .. import BagValidationError


def validate_manifest_md5(bag_dir: Path) -> None:
    """
    Validate the manifest-md5.txt file in a Bagit directory.

    Args:
        bag_dir (Path): Path to the Bagit directory.

    Raises:
        BagValidationError: If the manifest-md5.txt file is missing, empty, contains invalid lines,
            has checksum mismatches, or does not list all payload files.

    Notes:
        - Checks that all files in the data directory are listed in the manifest.
        - Verifies that each listed file's MD5 checksum matches the manifest entry.
    """
    manifest_md5_file = bag_dir / "manifest-md5.txt"

    with open(manifest_md5_file, "r", encoding="utf-8", newline="") as f:
        lines = [line for line in f if line.strip()]
        if not lines:
            raise BagValidationError(f"{bag_dir}: manifest-md5.txt is empty")
        for i, line in enumerate(lines, start=1):
            try:
                checksum, file_path = line.split(" ", 1)
                file_path = file_path.strip()
                if not file_path.startswith("data/"):
                    raise BagValidationError(
                        f"Invalid path in line {i} of manifest-md5.txt: '{file_path}'"
                    )
                md5sum = hashlib.md5((bag_dir / file_path).read_bytes()).hexdigest()
                if checksum != md5sum:
                    raise BagValidationError(
                        f"Checksum mismatch in line {i} of manifest-md5.txt: '{file_path}'"
                    )
            except ValueError as e:
                raise BagValidationError(
                    f"Invalid line {i} in manifest-md5.txt: '{line.rstrip()}'"
                ) from e
    payload_files = [Path(line.split(" ", 1)[1].strip()) for line in lines]
    for file in (bag_dir / "data").rglob("*"):
        if file.is_file():
            file_path = file.relative_to(bag_dir)
            if file_path not in payload_files:
                raise BagValidationError(
                    f"File '{file_path}' is not listed in manifest-md5.txt"
                )


def validate_manifest_sha512(bag_dir: Path) -> None:
    """
    Validate the manifest-sha512.txt file in a Bagit directory.

    Args:
        bag_dir (Path): Path to the Bagit directory.

    Raises:
        BagValidationError: If the manifest-sha512.txt file is missing, empty, contains invalid lines,
            has checksum mismatches, or does not list all payload files.

    Notes:
        - Checks that all files in the data directory are listed in the manifest.
        - Verifies that each listed file's SHA512 checksum matches the manifest entry.
    """
    manifest_sha512_file = bag_dir / "manifest-sha512.txt"
    with open(manifest_sha512_file, "r", encoding="utf-8", newline="") as f:
        lines = [line for line in f if line.strip()]
        if not lines:
            raise BagValidationError(f"{bag_dir}: manifest-sha512.txt is empty")
        for i, line in enumerate(lines, start=1):
            try:
                checksum, file_path = line.split(" ", 1)
                file_path = file_path.strip()
                if not file_path.startswith("data/"):
                    raise BagValidationError(
                        f"{bag_dir}: Invalid path in line {i} of manifest-sha512.txt: '{file_path}'"
                    )
                sha512sum = hashlib.sha512(
                    (bag_dir / file_path).read_bytes()
                ).hexdigest()
                if checksum != sha512sum:
                    raise BagValidationError(
                        f"Checksum mismatch in line {i} of manifest-sha512.txt: '{file_path}'"
                    )
            except ValueError as e:
                raise BagValidationError(
                    f"{bag_dir}:Invalid line {i} in manifest-sha512.txt: '{line.rstrip()}'"
                ) from e

    payload_files = [Path(line.split(" ", 1)[1].strip()) for line in lines]
    for file in (bag_dir / "data").rglob("*"):
        if file.is_file():
            file_path = file.relative_to(bag_dir)
            if file_path not in payload_files:
                raise BagValidationError(
                    f"File '{file_path}' is not listed in manifest-sha512.txt"
                )

