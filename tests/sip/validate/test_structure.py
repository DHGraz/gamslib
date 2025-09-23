"""Test validation of bagit directory stucture.

Eg. missing files or directories.
"""

import shutil

import pytest
from gamslib.sip.validation.bagit import validate_structure
from gamslib.sip import BagValidationError


def test_validate_structure(valid_bag_dir):
    """Test validating the structure of a valid Bagit directory."""
    assert validate_structure(valid_bag_dir) is None, (
        "Should not raise an exception for a valid Bagit directory"
    )


# --- missing directory tests ---


def test_validate_structure_missing_data_dir(valid_bag_dir):
    """Test validating the structure of a Bagit directory with a missing data directory."""
    shutil.rmtree(valid_bag_dir / "data")
    with pytest.raises(BagValidationError, match="Bag directory 'data' does not exist"):
        validate_structure(valid_bag_dir)


def test_validate_structure_missing_data_content_dir(valid_bag_dir):
    """Test validating the structure of a Bagit directory with a missing data/content directory."""
    shutil.rmtree(valid_bag_dir / "data" / "content")
    with pytest.raises(
        BagValidationError, match="Bag directory 'data/content' does not exist"
    ):
        validate_structure(valid_bag_dir)


def test_validate_structure_missing_data_meta_dir(valid_bag_dir):
    """Test validating the structure of a Bagit directory with a missing data/content directory."""
    shutil.rmtree(valid_bag_dir / "data" / "meta")
    with pytest.raises(
        BagValidationError, match="Bag directory 'data/meta' does not exist"
    ):
        validate_structure(valid_bag_dir)


# --- missing file tests ---


def test_validate_structure_missing_bagit_txt(valid_bag_dir):
    """Test validating the structure of a Bagit directory with a missing bagit.txt file."""
    (valid_bag_dir / "bagit.txt").unlink()
    with pytest.raises(BagValidationError, match="Bag file 'bagit.txt' does not exist"):
        validate_structure(valid_bag_dir)


def test_validate_structure_missing_manifest_md5(valid_bag_dir):
    """Test validating the structure of a Bagit directory with a missing manifest-md5.txt file."""
    (valid_bag_dir / "manifest-md5.txt").unlink()
    with pytest.raises(
        BagValidationError, match="Bag file 'manifest-md5.txt' does not exist"
    ):
        validate_structure(valid_bag_dir)


def test_validate_structure_missing_manifest_sha512(valid_bag_dir):
    "Check if missing manifest-sha512.txt file is detected."
    (valid_bag_dir / "manifest-sha512.txt").unlink()
    with pytest.raises(
        BagValidationError, match="Bag file 'manifest-sha512.txt' does not exist"
    ):
        validate_structure(valid_bag_dir)


def test_validate_structure_missing_manifest_sha256(valid_bag_dir):
    "Check if missing manifest-sha256.txt file is detected."
    (valid_bag_dir / "manifest-sha512.txt").unlink()
    with pytest.raises(
        BagValidationError, match="Bag file 'manifest-sha512.txt' does not exist"
    ):
        validate_structure(valid_bag_dir)


def test_validate_structure_missing_sip_json(valid_bag_dir):
    "Check if missing sip.json is detected."
    (valid_bag_dir / "data" / "meta" / "sip.json").unlink()
    with pytest.raises(
        BagValidationError, match="Bag file 'data/meta/sip.json' does not exist"
    ) as excinfo:
        validate_structure(valid_bag_dir)


def test_validate_structure_missing_dc_xml(valid_bag_dir):
    "Check if missing DC.xml is detected"
    (valid_bag_dir / "data" / "content" / "DC.xml").unlink()
    with pytest.raises(
        BagValidationError, match="Bag file 'data/content/DC.xml' does not exist"
    ) as excinfo:
        validate_structure(valid_bag_dir)
