"""Tests for the top-level DataCite record facade."""

import gamslib.datacite as datacite_package

from gamslib.datacite import DataCite
from gamslib.datacite.access import Access
from gamslib.datacite.metadata import Metadata
from gamslib.datacite import datacite_record


def test_datacite_can_be_created_from_package_exports():
    """The package facade exposes a usable top-level DataCite record model."""
    record = DataCite(
        access=Access(record="public", files="restricted"),
        metadata=Metadata(
            id="image-photo",
            title="Example",
            publication_date="2024-05",
            creators=[],
        ),
    )

    assert record.access.record == "public"
    assert record.metadata.title == "Example"
    assert record.record_schema == "local://records/record-v2.0.0.json"


def test_datacite_serializes_schema_using_alias():
    """The top-level record serializes the JSON schema field as `$schema`."""
    record = DataCite(
        access=Access(record="public", files="public"),
        metadata=Metadata(
            id="image-photo",
            title="Example",
            publication_date="2024",
            creators=[],
        ),
    )

    dumped = record.model_dump(by_alias=True)

    assert dumped["$schema"] == "local://records/record-v2.0.0.json"


def test_datacite_package_facade_exports_datacite_model():
    """The package facade keeps DataCite available from the package root."""
    assert datacite_package.__all__ == ["DataCite"]
    assert DataCite is datacite_record.DataCite