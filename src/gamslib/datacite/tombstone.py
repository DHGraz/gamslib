"Representation of a DataCite tombstone object."

from pydantic import BaseModel


class Tombstone(BaseModel):
    """Representation of a DataCite tombstone object."""

    # Free text, the reason for removal.
    reason: str
    # An identifier for a category of reasons. Used for statistics
    # purposes and for extracting e.g. spam records from the system.
    category: str
    # The user who removed the record, eg. {"user": 1}
    removed_by: dict[str, int | str]
    timestamp: str
