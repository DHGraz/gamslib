"""Tests for the top-level DataCite record facade."""

import json

import pytest

import gamslib.datacite as datacite_package
from gamslib.datacite import DataCite, datacite_record
from gamslib.datacite.access import Access
from gamslib.datacite.files import FilesRecord
from gamslib.datacite.metadata import Metadata


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


def test_datacite_from_json_builds_nested_models():
    """from_json validates nested structures with package models."""
    payload = {
        "$schema": "local://records/record-v2.0.0.json",
        "access": {"record": "public", "files": "restricted"},
        "metadata": {
            "id": "image-photo",
            "title": "Example",
            "publication_date": "2024",
            "creators": [],
        },
        "files": {"enabled": True, "entries": None, "default_preview": None},
    }

    record = DataCite.from_json(json.dumps(payload))

    assert isinstance(record, DataCite)
    assert isinstance(record.access, Access)
    assert isinstance(record.metadata, Metadata)
    assert isinstance(record.files, FilesRecord)
    assert record.files.enabled is True


def test_datacite_from_json_accepts_dict_payload():
    """from_json accepts an already parsed JSON object payload."""
    record = DataCite.from_json(
        {
            "access": {"record": "public", "files": "public"},
            "metadata": {
                "id": "image-photo",
                "title": "Example",
                "publication_date": "2024-05",
                "creators": [],
            },
        }
    )

    assert record.access.files == "public"
    assert record.metadata.publication_date == "2024-05"
    assert isinstance(record.files, FilesRecord)


def test_datacite_from_json_rejects_non_object_json():
    """from_json requires a JSON object payload."""
    with pytest.raises(TypeError, match="must be an object"):
        DataCite.from_json("[]")


def test_datacite_to_json_uses_aliases_and_serializes_nested_models():
    """to_json emits a valid JSON string with aliased top-level fields."""
    record = DataCite(
        access=Access(record="public", files="restricted"),
        metadata=Metadata(
            id="image-photo",
            title="Example",
            publication_date="2024",
            creators=[],
        ),
        files=FilesRecord(enabled=True),
    )

    dumped = json.loads(record.to_json())

    assert dumped["$schema"] == "local://records/record-v2.0.0.json"
    assert dumped["access"]["files"] == "restricted"
    assert dumped["metadata"]["title"] == "Example"
    assert dumped["files"]["enabled"] is True


def test_datacite_json_round_trip_preserves_core_values():
    """to_json output can be read back with from_json."""
    original = DataCite(
        access=Access(record="public", files="public"),
        metadata=Metadata(
            id="image-photo",
            title="Round trip",
            publication_date="2024-05",
            creators=[],
        ),
    )

    restored = DataCite.from_json(original.to_json())

    assert restored.record_schema == original.record_schema
    assert restored.access.record == original.access.record
    assert restored.metadata.title == original.metadata.title


def test_datacite_from_json_real_example(shared_datadir):
    """from_json can parse a real-world example JSON file."""
    example_path = shared_datadir / "record.json"
    with open(example_path, "r", encoding="utf-8") as f:
        record = DataCite.from_json(f.read())

    assert record.metadata.title == "Practice meets Principle: Tracking Software and Data Citations to Zenodo DOIs"
    assert record.metadata.id == "image-photo"
    assert record.access.record == "public"