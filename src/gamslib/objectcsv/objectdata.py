from dataclasses import dataclass


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


    def merge(self, other_objectdata: "ObjectData"):
        """Merge the object data with another ObjectData object."""
        fields_to_merge = ['title', 'project', 'creator', 'rights', 'publisher', 'source', 'objectType', 'funder']
        for field in fields_to_merge:
            if getattr(self, field) == "":
                setattr(self, field, getattr(other_objectdata, field))

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