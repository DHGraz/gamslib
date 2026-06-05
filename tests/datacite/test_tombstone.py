"""Tests for the DataCite tombstone model."""

import pytest
from pydantic import ValidationError

from gamslib.datacite.tombstone import Tombstone


def test_tombstone_accepts_expected_payload():
    """Tombstone accepts the documented removal payload shape."""
    tombstone = Tombstone(
        reason="Record withdrawn by request",
        category="withdrawn",
        removed_by={"user": 42, "username": "curator"},
        timestamp="2026-06-05T10:15:00Z",
    )

    assert tombstone.reason == "Record withdrawn by request"
    assert tombstone.category == "withdrawn"
    assert tombstone.removed_by == {"user": 42, "username": "curator"}


@pytest.mark.parametrize(
    "removed_by",
    [
        {"user": [1]},
        {"user": {"id": 1}},
        {"user": None},
    ],
)
def test_tombstone_rejects_invalid_removed_by_value_types(removed_by):
    """removed_by only allows integer or string values per key."""
    with pytest.raises(ValidationError, match="removed_by"):
        Tombstone(
            reason="Record withdrawn",
            category="withdrawn",
            removed_by=removed_by,
            timestamp="2026-06-05T10:15:00Z",
        )
