"""Tests for validation of manifest files."""

import pytest

from gamslib.sip import BagValidationError
from gamslib.sip.validation.manifests import (
    validate_manifest_md5,
    validate_manifest_sha512,
)

# These are the manifest file to be tested and the corresponding validation functions
manifests_to_test = [
    ("manifest-md5.txt", validate_manifest_md5),
    ("manifest-sha512.txt", validate_manifest_sha512),
]


@pytest.mark.parametrize("manifest_file, validation_function", manifests_to_test)
def test_validate_valid_manifest(manifest_file, validation_function, valid_bag_dir):
    """Test valid manifest files.

    valid_bag_dir is a fixture that creates a valid Bagit directory, so
    all validations should pass.
    """
    assert validation_function(valid_bag_dir) is None, (
        "Should not raise an exception for valid manifest files"
    )


@pytest.mark.parametrize("manifest_file, validation_function", manifests_to_test)
def test_manifest_empty(manifest_file, validation_function, valid_bag_dir):
    """Test if validation fails if manifest file is empty."""
    (valid_bag_dir / manifest_file).write_text("")
    with pytest.raises(BagValidationError, match="is empty"):
        validation_function(valid_bag_dir)


@pytest.mark.parametrize("manifest_file, validation_function", manifests_to_test)
def test_validate_incomplete_manifest(
    manifest_file, validation_function, valid_bag_dir
):
    """Test if validation fails if a manifest file is incomplete."""

    # remove the first line of mainifest_file
    manifest_path = valid_bag_dir / manifest_file
    data = (manifest_path).read_text()
    lines = data.splitlines()
    lines.pop(0)
    manifest_path.write_text("\n".join(lines))

    with pytest.raises(BagValidationError, match="is not listed"):
        validation_function(valid_bag_dir)


@pytest.mark.parametrize("manifest_file, validation_function", manifests_to_test)
def test_validate_invalid_path(manifest_file, validation_function, valid_bag_dir):
    """Test if validation fails if a manifest file has an invalid path."""
    manifest_path = valid_bag_dir / manifest_file
    content = manifest_path.read_text()
    content = content.replace("data/", "invalid_path/")
    manifest_path.write_text(content)
    with pytest.raises(BagValidationError, match="Invalid path"):
        validation_function(manifest_path.parent)


@pytest.mark.parametrize("manifest_file, validation_function", manifests_to_test)
def test_validate_bad_checksum(manifest_file, validation_function, valid_bag_dir):
    "Check if a bad checksum is detected"
    manifest_path = valid_bag_dir / manifest_file
    lines = []
    for line in manifest_path.read_text().splitlines():
        chksum, file = line.split("  ")
        chksum = chksum.replace("1", "2").replace("2", "1")
        lines.append(f"{chksum}  {file}")
    content = "\n".join(lines)
    content += "\n"
    manifest_path.write_text(content)
    with pytest.raises(BagValidationError, match="Checksum mismatch"):
        validation_function(valid_bag_dir)


@pytest.mark.parametrize("manifest_file, validation_function", manifests_to_test)
def test_validate_bad_checkum_format(manifest_file, validation_function, valid_bag_dir):
    """Check if a bad checksum format is detected
    Each line must contain a checksum, two spaces and a path."
    """
    manifest_path = valid_bag_dir / manifest_file
    content = manifest_path.read_text().replace("  ", "")
    manifest_path.write_text(content)
    with pytest.raises(BagValidationError, match="Invalid line"):
        validation_function(valid_bag_dir)
