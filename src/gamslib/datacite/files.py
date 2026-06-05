"""Represents the datacite record.files object."""

from pydantic import BaseModel, Field


class FileLinks(BaseModel):
    """Links for a file entry in the datacite record.files object."""

    self_: str = Field(serialization_alias="self")
    content: str
    # iiif of course only applies to image files
    iiif_canvas: str | None = None
    iiif_canvas: str | None = None
    iiif_info: str | None = None
    iiif_api: str | None = None


class DataCiteFile(BaseModel):
    """A file entry in the datacite record.files object."""

    bucket_id: str
    checksum: str  # <algorithm>:<value>
    created: str  # utc datetime
    file_id: str  # The digital file instance identifier (references a file on storage).
    key: str  # The filepath of the file.
    links: FileLinks  # links to the file
    # Dictionary of free key-value pairs with meta information about the file
    # (e.g. description).
    metadata: dict[str, str]
    mimetype: str
    size: int
    status: str  # completed or pending
    storage_class: str  # The backend for the file (e.g. local or external storage).
    updated: str  # utc datetime
    version_id: str  # The logical object identifier.


class FilesRecord(BaseModel):
    """A datacite record.files object."""

    # if enabled is False, the record is a metadata-only record
    enabled: bool = True
    # each entry has the file name as key and a DataCiteFile as value
    entries: dict[str, DataCiteFile] | None = None
    # the name of the 'default' file used for previewing
    default_preview: str | None = None
