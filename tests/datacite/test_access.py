"""Tests for the datacite access models."""

import pytest
from pydantic import ValidationError

from gamslib.datacite.access import Access, Embargo


def test_embargo_accepts_none_until():
    """Embargo.until may be omitted or set to None."""
    embargo = Embargo(active=True, until=None, reason="temporary embargo")

    assert embargo.active is True
    assert embargo.until is None
    assert embargo.reason == "temporary embargo"


def test_embargo_accepts_valid_date_string():
    """Embargo.until accepts an ISO date string in YYYY-MM-DD format."""
    embargo = Embargo(active=False, until="2026-05-15", reason="release soon")

    assert embargo.until == "2026-05-15"


def test_embargo_rejects_invalid_date_string():
    """Embargo.until rejects strings that are not valid dates."""
    with pytest.raises(ValidationError, match="until must be in YYYY-MM-DD format"):
        Embargo(active=True, until="2026-02-30", reason="invalid date")


@pytest.mark.parametrize("record_value", ["private", "open", "", None])
def test_access_rejects_invalid_record_values(record_value):
    """Access.record only accepts the configured public/restricted values."""
    with pytest.raises(ValidationError):
        Access(record=record_value, files="public")


@pytest.mark.parametrize("files_value", ["private", "open", "", None])
def test_access_rejects_invalid_files_values(files_value):
    """Access.files only accepts the configured public/restricted values."""
    with pytest.raises(ValidationError):
        Access(record="public", files=files_value)


def test_access_accepts_valid_values():
    """Access can be created with valid record and file values."""
    access = Access(
        record="public",
        files="restricted",
        embargo=Embargo(active=True, until="2026-05-15", reason="embargoed"),
    )

    assert access.record == "public"
    assert access.files == "restricted"
    assert access.embargo is not None
    assert access.embargo.until == "2026-05-15"