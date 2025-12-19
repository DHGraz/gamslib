""" "This code is part of a test suite for validating the payload oxum of a bag directory structure.
It includes tests for correct and incorrect formats, as well as checks for mismatches in expected and
actual payload sizes and file counts.
"""

import pytest

from gamslib.sip.validation import baginfo
from gamslib.sip import BagValidationError
from gamslib.sip.validation.baginfo import validate_payload_oxum


class DummyUtils:
    @staticmethod
    def count_bytes(path):
        # Simulate payload size
        return 1234

    @staticmethod
    def count_files(path):
        # Simulate file count
        return 5


@pytest.fixture(autouse=True)
def patch_utils(monkeypatch):
    """Patch the utils module to use DummyUtils for testing."""
    monkeypatch.setattr(baginfo, "utils", DummyUtils)


@pytest.fixture
def tmp_bag_dir(tmp_path):
    """Create a temporary bag directory structure for testing."""
    # Create a data directory
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    # Create dummy files
    for i in range(5):
        (data_dir / f"file{i}.txt").write_text("a" * (1234 // 5))
    return tmp_path


def test_valid_payload_oxum(tmp_bag_dir):
    """Test the validate_payload_oxum function with a valid payload oxum."""
    # The expected size is 1234 and file count is 5
    # This matches the dummy implementation of count_bytes and count_files
    # in DummyUtils.
    value = "1234.5"
    # Should not raise
    validate_payload_oxum(value, tmp_bag_dir)


@pytest.mark.parametrize(
    "value",
    [
        "abc.5",  # size not integer
        "1234.xyz",  # file_count not integer
        "1234",  # missing file_count
        "1234.5.6",  # too many parts
        "12a4.5",  # size contains letter
        "1234.5a",  # file_count contains letter
    ],
)
def test_invalid_format(value, tmp_bag_dir):
    """Test the validate_payload_oxum function with invalid formats."""
    with pytest.raises(BagValidationError) as excinfo:
        validate_payload_oxum(value, tmp_bag_dir)
    assert "Value for 'Payload-Oxum' is not valid" in str(excinfo.value)


def test_wrong_size(tmp_bag_dir, monkeypatch):
    """Test the validate_payload_oxum function with a wrong size.
    
    This simulates a mismatch between the expected and actual payload size.
    """
    # Patch count_bytes to return a different value
    monkeypatch.setattr(DummyUtils, "count_bytes", staticmethod(lambda path: 9999))
    value = "1234.5"
    with pytest.raises(BagValidationError) as excinfo:
        validate_payload_oxum(value, tmp_bag_dir)
    assert "does not match the actual payload size" in str(excinfo.value)


def test_wrong_file_count(tmp_bag_dir, monkeypatch):
    """Test the validate_payload_oxum function with a wrong file count.
    
    This simulates a mismatch between the expected and actual file count.
    """
    # Patch count_files to return a different value
    monkeypatch.setattr(DummyUtils, "count_files", staticmethod(lambda path: 99))
    value = "1234.5"
    with pytest.raises(BagValidationError) as excinfo:
        validate_payload_oxum(value, tmp_bag_dir)
    assert "does not match the actual number of files" in str(excinfo.value)
