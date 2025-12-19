"""Test the validate_bagit_txt function of validate.py.
"""
import pytest

from gamslib.sip.validation.bagit import validate_bagit_txt
from gamslib.sip import BagValidationError


def test_validate_bagit_txt_missing(valid_bag_dir):
    """A missing bagit.txt file should raise an exception."""
    (valid_bag_dir / "bagit.txt").unlink()
    with pytest.raises(BagValidationError, match="'bagit.txt' file does not exist"):
        validate_bagit_txt(valid_bag_dir)


def test_validate_empty_bagit_txt(valid_bag_dir):
    "Ab empty bagit.txt file should raise an exception."
    (valid_bag_dir / "bagit.txt").write_text("")
    with pytest.raises(BagValidationError, match="bagit.txt is incomplete") as excinfo:
        validate_bagit_txt(valid_bag_dir)
    # assert "Invalid number of lines in bagit.txt" in str(excinfo.value)


def test_validate_bagit_txt_invalid_line(valid_bag_dir):
    "Test a bagit.txt file invalid first line."
    bagit_file = valid_bag_dir / "bagit.txt"
    bagit_file.write_text("BagIt-Version = 1.0\nTag-File-Character-Encoding: UTF-8\n")
    with pytest.raises(BagValidationError, match="Invalid line 1"):
        validate_bagit_txt(valid_bag_dir)

    bagit_file.write_text("Bagit-Version: 1.0\nTag-File-Character-Encoding = UTF-8\n")
    with pytest.raises(BagValidationError, match="Invalid line 2"):
        validate_bagit_txt(valid_bag_dir)


def test_validate_bagit_txt_missing_lines(valid_bag_dir):
    "Test a bagit.txt file with missing lines."
    bagit_file = valid_bag_dir / "bagit.txt"
    bagit_file.write_text(
        "Bagit-Version: 1.0\nTag-File-Character-Encoding: UTF-8\nfoo: bar\n"
    )
    with pytest.raises(BagValidationError, match="bagit.txt is incomplete"):
        validate_bagit_txt(valid_bag_dir)


def test_validate_bagit_txt_ignore_empty_lines(valid_bag_dir):
    "Test a bagit.txt file with additional empty lines."
    bagit_file = valid_bag_dir / "bagit.txt"
    bagit_file.write_text(
        "\nBagIt-Version: 1.0\n\nTag-File-Character-Encoding: UTF-8\n\n\n"
    )
    assert validate_bagit_txt(valid_bag_dir) is None, "Should not raise an exception for empty lines"


def test_validate_bagit_txt_wrong_version(valid_bag_dir):
    "Test a bagit.txt file with wrong version line."
    bagit_file = valid_bag_dir / "bagit.txt"
    bagit_file.write_text("Bagit-Version: 1.0\nTag-File-Character-Encoding: UTF-8")
    with pytest.raises(BagValidationError, match="Missing line for 'BagIt-Version'"):
        validate_bagit_txt(valid_bag_dir)
    # assert "Missing line for 'BagIt-Version'" in str(excinfo.value)


def test_validate_bagit_txt_wrong_version_value(valid_bag_dir):
    "Test a bagit.txt file with wrong version line."
    bagit_file = valid_bag_dir / "bagit.txt"
    bagit_file.write_text("BagIt-Version: foo\nTag-File-Character-Encoding: UTF-8")
    with pytest.raises(BagValidationError, match="Invalid value for 'BagIt-Version'"):
        validate_bagit_txt(valid_bag_dir)


def test_validate_bagit_txt_wrong_encoding(valid_bag_dir):
    "Test a bagit.txt file with wrong encoding line."
    bagit_file = valid_bag_dir / "bagit.txt"
    bagit_file.write_text("BagIt-Version: 1.0\nTagFileCharacter-Encoding: UTF-8")
    with pytest.raises(
        BagValidationError, match="Missing line for 'Tag-File-Character-Encoding'"
    ):
        validate_bagit_txt(valid_bag_dir)
    # assert "Missing line for 'Tag-File-Character-Encoding" in str(excinfo.value)


def test_validate_bagit_txt_wrong_encoding_value(valid_bag_dir):
    "Test a bagit.txt file with wrong encoding line."
    bagit_file = valid_bag_dir / "bagit.txt"
    bagit_file.write_text("BagIt-Version: 1.0\nTag-File-Character-Encoding: foo")
    with pytest.raises(
        BagValidationError, match="Invalid value for 'Tag-File-Character-Encoding'"
    ):
        validate_bagit_txt(valid_bag_dir)
