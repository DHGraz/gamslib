"""Top-level DataCite record models.

The module name follows the owning model so the record-level classes are easy to find,
while `datacite.py` remains a compatibility facade.
"""

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from gamslib.datacite.access import Access
from gamslib.datacite.files import FilesRecord
from gamslib.datacite.metadata import Metadata
from gamslib.datacite.tombstone import Tombstone


class DataCite(BaseModel):
    """Representation of a top-level DataCite/Invenio record."""

    record_schema: str = Field(
        default="local://records/record-v2.0.0.json",
        alias="$schema",
        serialization_alias="$schema",
    )
    id: str | None = None
    pid: dict[str, Any] | None = None
    pids: dict[str, Any] = Field(default_factory=dict)
    parent: dict[str, Any] | None = None
    access: Access
    metadata: Metadata
    #Currently we do not support the (optional) custom_fields
    #custom_fields: = Field(default_factory=dict)
    files: FilesRecord = Field(default_factory=FilesRecord)
    tombstone: Tombstone | None = None
    created: datetime | None = None
    updated: datetime | None = None

    @staticmethod
    def _normalize_creator_entry(creator: Any) -> Any:
        """Normalize one creator entry from Invenio JSON to local model shape."""
        if not isinstance(creator, dict):
            return creator

        creator_copy = creator.copy()
        person_or_org = creator_copy.get("person_or_org")
        if isinstance(person_or_org, dict):
            person_copy = person_or_org.copy()
            identifiers = person_copy.get("identifiers")
            if isinstance(identifiers, list):
                person_copy["identifiers"] = identifiers[0] if identifiers else None
            creator_copy["person_or_org"] = person_copy

        affiliations = creator_copy.get("affiliations")
        if isinstance(affiliations, list):
            creator_copy["affiliations"] = [
                DataCite._normalize_affiliation_entry(affiliation)
                for affiliation in affiliations
            ]

        return creator_copy

    @staticmethod
    def _normalize_affiliation_entry(affiliation: Any) -> Any:
        """Normalize one affiliation entry for strict local vocabulary checks."""
        if not isinstance(affiliation, dict):
            return affiliation

        affiliation_copy = affiliation.copy()
        if affiliation_copy.get("id") not in {"isni", "ror"}:
            affiliation_copy.pop("id", None)
        return affiliation_copy

    @staticmethod
    def _normalize_rights_payload(rights_payload: Any) -> Any:
        """Normalize rights payload from Invenio list/object forms."""
        if isinstance(rights_payload, list):
            rights_payload = rights_payload[0] if rights_payload else None

        if not isinstance(rights_payload, dict):
            return rights_payload

        rights_copy = rights_payload.copy()
        title = rights_copy.get("title")
        if isinstance(title, dict):
            title_values = [v for v in title.values() if isinstance(v, str)]
            rights_copy["title"] = title_values[0] if title_values else None
        return rights_copy

    @staticmethod
    def _normalize_metadata_payload(metadata_payload: dict[str, Any]) -> dict[str, Any]:
        """Normalize known Invenio JSON variants to the internal Metadata shape."""
        normalized = metadata_payload.copy()

        if not normalized.get("id"):
            normalized["id"] = "image-photo"

        creators = normalized.get("creators")
        if isinstance(creators, list):
            normalized["creators"] = [
                DataCite._normalize_creator_entry(creator) for creator in creators
            ]

        normalized["rights"] = DataCite._normalize_rights_payload(
            normalized.get("rights")
        )

        return normalized

    @classmethod
    def from_json(cls, data: str | bytes | bytearray | dict[str, Any]) -> "DataCite":
        """Create a DataCite record from a JSON object/string.

        Nested payloads are validated via the package models (Access, Metadata,
        FilesRecord, Tombstone) before constructing the top-level record.
        """
        payload: Any
        if isinstance(data, (bytes, bytearray)):
            payload = json.loads(data.decode("utf-8"))
        elif isinstance(data, str):
            payload = json.loads(data)
        elif isinstance(data, dict):
            payload = data.copy()
        else:
            raise TypeError("data must be a JSON string/bytes or a dict payload")

        if not isinstance(payload, dict):
            raise TypeError("DataCite JSON payload must be an object")

        if "access" in payload:
            payload["access"] = Access.model_validate(payload["access"])
        if "metadata" in payload:
            metadata_payload = payload["metadata"]
            if isinstance(metadata_payload, dict):
                metadata_payload = cls._normalize_metadata_payload(metadata_payload)
            payload["metadata"] = Metadata.model_validate(metadata_payload)
        if "files" in payload:
            payload["files"] = FilesRecord.model_validate(payload["files"])
        if "tombstone" in payload and payload["tombstone"] is not None:
            payload["tombstone"] = Tombstone.model_validate(payload["tombstone"])

        return cls.model_validate(payload)

    def to_json(self) -> str:
        """Serialize the DataCite record to a JSON string using public aliases."""
        return self.model_dump_json(by_alias=True)


__all__ = ["DataCite"]
