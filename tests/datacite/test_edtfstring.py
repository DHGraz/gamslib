"""Tests for shared EDTF validation helpers used in datacite metadata."""

import pytest

from gamslib.datacite.common import _validate_edtf


@pytest.mark.parametrize(
    "value",
    [
        "2026",
        "2026-05",
        "2026-05-15",
        "2026/2027",
        "2026-05/2027-01",
        "2026-05-15/2027-01-31",
    ],
)
def test_validate_edtf_accepts_supported_formats(value):
    """The shared EDTF validator accepts supported single-date and range formats."""
    parsed = _validate_edtf(value)

    assert parsed == value


@pytest.mark.parametrize(
    "value",
    [
        "2026-13",  # invalid month
        "2026-00",  # invalid month
        "2026-02-30",  # invalid day
        "26",  # invalid year format
        "2026/",  # missing range end
        "/2026",  # missing range start
        "2026/2027/2028",  # too many range parts
        "2026-05-15T00:00:00",  # timestamp not allowed
    ],
)
def test_validate_edtf_rejects_invalid_formats(value):
    """The shared EDTF validator rejects unsupported or malformed values."""
    with pytest.raises(ValueError):
        _validate_edtf(value)


def test_validate_edtf_rejects_non_string_values():
    """The shared EDTF validator requires a plain string input."""
    with pytest.raises(TypeError):
        _validate_edtf(2026)