"""Validate the manifest files in a bag directory.
"""
import hashlib
from pathlib import Path

from .. import BagValidationError


def validate_manifest_md5(bag_dir: Path) -> None:
    """Validate the manifest-md5.txt file.

    Raises a BagValidationError if the manifest-md5.txt file
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
    """Validate the manifest-sha512.txt file.


    Returns True if the manifest-sha512.txt file is valid.
    Raises a BagValidationError if the manifest-sha512.txt file is invalid.
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

