""" Tests for validation baginfo.txt 
"""

from pathlib import Path

import pytest
from gamslib.sip.validation.baginfo import (
    validate_baginfo_text,
)
from gamslib.sip.validation.baginfo import (
    read_baginfo_txt,
    validate_bagging_date,
    validate_contact_email,
    validate_external_description,
    validate_payload_oxum,
    validate_required_baginfo_entries,
)
from gamslib.sip import BagValidationError


@pytest.fixture(name="valid_baginfo")
def make_valid_baginfo() -> list[tuple[str, str]]:
    "Return the content of a valid bag-info.txt file."
    return [
        ("Bagging-Date", "2024-08-22"),
        ("Payload-Oxum", "78207.3"),
        ("Contact-Email", "dh@uni-graz.at"),
        ("Contact-Email", "foo@example.com"),
        ("External-Description", "Test SIP"),
    ]


def compute_payload_oxum(bag_dir: Path) -> tuple[int, int]:
    """Compute the payload size and number of files.

    This is a tests specific helper function to get the current payload.
    """
    total_bytes = 0
    num_of_files = 0
    for file in (bag_dir / "data").rglob("*"):
        if file.is_file():
            total_bytes += file.stat().st_size
            num_of_files += 1
    return total_bytes, num_of_files


def test_read_baginfo_txt(valid_bag_dir):
    """Test reading the bag-info.txt file of a valid Bagit directory."""
    total_bytes, num_of_files = compute_payload_oxum(valid_bag_dir)
    baginfo_path = valid_bag_dir / "bag-info.txt"
    data = read_baginfo_txt(baginfo_path)
    assert data[0] == ("Bagging-Date", "2024-08-22")
    assert data[1] == ("Payload-Oxum", f"{total_bytes}.{num_of_files}")
    assert data[2] == ("Contact-Email", "dh@uni-graz.at")
    assert data[3] == ("Contact-Email", "foo@example.com")
    assert data[4] == ("External-Description", "Test SIP")


def test_validate_required_baginfo_entries(valid_baginfo):
    """Test if the validator detects missing required entries in bag-info.txt."""
    # validate valid data
    assert validate_required_baginfo_entries(valid_baginfo) is None

    # validate missing required entries
    valid_baginfo.pop(0)
    with pytest.raises(
        BagValidationError, match="Missing required entry 'Bagging-Date'"
    ):
        validate_required_baginfo_entries(valid_baginfo)


def test_validate_bagging_date():
    """Test if the validator detects invalid Bagging-Date entries."""
    # valid date
    assert validate_bagging_date("2024-08-22")

    # invalid date
    with pytest.raises(
        BagValidationError, match="alue for 'Bagging-Date' is not a valid date:"
    ):
        validate_bagging_date("2024-08-32")

    # invalid date
    with pytest.raises(
        BagValidationError, match="Value for 'Bagging-Date' is not a valid date:"
    ):
        validate_bagging_date("2024-08-22T14:26:35")




def test_validate_payload_oxum(valid_bag_dir):
    """Test if the validator detects invalid Payload-Oxum entries."""

    # valid oxum
    total_bytes, num_of_files = compute_payload_oxum(valid_bag_dir)
    assert validate_payload_oxum(f"{total_bytes}.{num_of_files}", valid_bag_dir) is None

    # invalid oxum format (missing dot)
    with pytest.raises(
        BagValidationError, match="Value for 'Payload-Oxum' is not valid:"
    ):
        validate_payload_oxum(f"{total_bytes}{num_of_files}", valid_bag_dir)

    # invalid oxum: wrong size
    with pytest.raises(
        BagValidationError, match="does not match the actual payload size:"
    ):
        validate_payload_oxum(f"{total_bytes + 1}.{num_of_files}", valid_bag_dir)

    # invalid oxum: wrong file number
    with pytest.raises(
        BagValidationError, match="does not match the actual number of files:"
    ):
        validate_payload_oxum(f"{total_bytes}.{num_of_files + 1}", valid_bag_dir)


def test_validate_contact_email():
    """Test if the validator detects invalid Contact-Email entries."""
    assert validate_contact_email("foo@example.com") is None
    assert validate_contact_email("bar.foo@example.com") is None
    assert validate_contact_email("br-foo.foo_bar@example.rich") is None

    # invalid mail addresses
    with pytest.raises(
        BagValidationError,
        match="Value for 'Contact-Email' is not a valid email address",
    ):
        validate_contact_email("foo")

    with pytest.raises(BagValidationError):
        validate_contact_email("foo@")

    with pytest.raises(BagValidationError) as excinfo:
        validate_contact_email("fo/o@bar.nat")

    with pytest.raises(BagValidationError) as excinfo:
        validate_contact_email("foo@bar.n-e-t")


def test_validate_external_description():
    """Test if the validator detects invalid External-Description entries."""
    assert validate_external_description("Foo Bar") is None

    # empty value
    with pytest.raises(
        BagValidationError, match="Value for 'External-Description' must not be empty"
    ):
        validate_external_description("")

    # only whitespace
    with pytest.raises(BagValidationError):
        validate_external_description(" ")


def test_validate_bag_info_txt(valid_bag_dir):
    """Test the validate_baginfo_text function."""

    assert validate_baginfo_text(valid_bag_dir) is None

    baginfo_file = valid_bag_dir / "bag-info.txt"

    # Test entry with missing colon
    baginfo_file.write_text("Bagging-Date 2024-08-22")
    with pytest.raises(BagValidationError, match="Invalid line") as excinfo:
        validate_baginfo_text(valid_bag_dir)

    # Test missing bag-info.txt file
    baginfo_file.unlink()
    with pytest.raises(
        BagValidationError, match="bag-info.txt file does not exist"
    ) as excinfo:
        validate_baginfo_text(valid_bag_dir)
