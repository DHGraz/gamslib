"""Tests for DataCite file models."""

from pydantic import ValidationError
import pytest

from gamslib.datacite.files import DataCiteFile, FileLinks, FilesRecord


def test_file_links_serialize_self_with_alias():
    """FileLinks serializes self_ as self when dumping by alias."""
    links = FileLinks(self_="https://example.org/files/self", content="https://example.org/files/content")

    dumped = links.model_dump(by_alias=True)

    assert dumped["self"] == "https://example.org/files/self"
    assert dumped["content"] == "https://example.org/files/content"


def test_datacite_file_accepts_complete_entry():
    """DataCiteFile can be created with the expected file metadata fields."""
    entry = DataCiteFile(
        bucket_id="bucket-1",
        checksum="md5:abcdef123456",
        created="2026-01-01T12:00:00Z",
        file_id="file-1",
        key="images/picture.jpg",
        links=FileLinks(self_="https://example.org/files/1", content="https://example.org/content/1"),
        metadata={"description": "A sample image"},
        mimetype="image/jpeg",
        size=1024,
        status="completed",
        storage_class="local",
        updated="2026-01-01T12:00:01Z",
        version_id="v1",
    )

    assert entry.key == "images/picture.jpg"
    assert entry.size == 1024
    assert entry.links.self_ == "https://example.org/files/1"


def test_files_record_defaults_to_enabled_metadata_only_shape():
    """FilesRecord default values represent a metadata-only record."""
    files = FilesRecord()

    assert files.enabled is True
    assert files.entries is None
    assert files.default_preview is None


@pytest.mark.parametrize("invalid_size", ["not-an-int", 10.5, None])
def test_datacite_file_rejects_invalid_size_type(invalid_size):
    """DataCiteFile requires an integer size field."""
    with pytest.raises(ValidationError, match="size"):
        DataCiteFile(
            bucket_id="bucket-1",
            checksum="md5:abcdef123456",
            created="2026-01-01T12:00:00Z",
            file_id="file-1",
            key="images/picture.jpg",
            links=FileLinks(self_="https://example.org/files/1", content="https://example.org/content/1"),
            metadata={"description": "A sample image"},
            mimetype="image/jpeg",
            size=invalid_size,
            status="completed",
            storage_class="local",
            updated="2026-01-01T12:00:01Z",
            version_id="v1",
        )
