"""CSV data for a single object.
"""
from dataclasses import dataclass
import dataclasses

# pylint: disable=too-many-instance-attributes,invalid-name

@dataclass
class ObjectData:
    """Represents csv data for a single object."""

    recid: str
    title: str = ""
    project: str = ""
    description: str = ""
    creator: str = ""
    rights: str = ""
    publisher: str = ""
    source: str = ""
    objectType: str = ""
    mainResource: str = ""  # main datastream
    funder: str = ""

    @classmethod
    def fieldnames(cls) -> list[str]:
        """Return the fields of the object data."""
        return [field.name for field in dataclasses.fields(cls)]


    def merge(self, other: "ObjectData"):
        """Merge the object data with another ObjectData object."""
        if self.recid != other.recid:
            raise ValueError("Cannot merge objects with different recid values")
        # These are the fields which are possibly set automatically set in the new object data
        fields_to_merge = [
            "title",
            "project",
            "creator",
            "rights",
            "publisher",
            "source",
            "objectType",
            "mainResource",
            "funder",
        ]
        for field in fields_to_merge:
            if getattr(other, field).strip():
                setattr(self, field, getattr(other, field))

    def validate(self):
        """Validate the object data."""
        if not self.recid:
            raise ValueError("recid must not be empty")
        if not self.title:
            raise ValueError(f"{self.recid}: title must not be empty")
        if not self.rights:
            raise ValueError(f"{self.recid}: rights must not be empty")
        if not self.source:
            raise ValueError(f"{self.recid}: source must not be empty")
        if not self.objectType:
            raise ValueError(f"{self.recid}: objectType must not be empty")
