"""CSV data model for a single GAMS object.

Defines the ObjectData class, representing metadata for a single object as stored in object.csv.
Provides methods for merging, validating, and listing field names.
"""

from dataclasses import dataclass
import dataclasses

# pylint: disable=too-many-instance-attributes,invalid-name


@dataclass
class ObjectData:
    """
    Represents CSV metadata for a single GAMS object.

    Fields:

      - recid (str): Object identifier.
      - title (str): Title of the object.
      - project (str): Project name or identifier.
      - description (str): Description of the object.
      - creator (str): Creator of the object.
      - rights (str): Rights statement for the object.
      - publisher (str): Publisher of the object.
      - source (str): Source of the object.
      - objectType (str): Type of the object.
      - mainResource (str): Main datastream identifier.
      - funder (str): Funder information.
      - tags (str): Additional tags for the object.
    """

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
    tags: str = ""

    @classmethod
    def fieldnames(cls) -> list[str]:
        """
        Return the list of field names for ObjectData.

        Returns:
            list[str]: Names of all fields in the ObjectData dataclass.
        """
        return [field.name for field in dataclasses.fields(cls)]

    def merge(self, other: "ObjectData"):
        """
        Merge the object data with another ObjectData instance.

        Both objects must have the same recid.

        Some field are always replacd by the new value if the new value is non-empty
        ('title', 'project', 'creator', 'rights', 'publisher', 'source', 'objectType',
        'mainResource', 'funder').

        Other fields are only updated if they are empty in the current instance and
        non-empty in the other instance.

        Args:
            other (ObjectData): Another ObjectData instance to merge from.

        Raises:
            ValueError: If recid values do not match.
        """
        if self.recid != other.recid:
            raise ValueError("Cannot merge objects with different recid values")

        # These fields might have been set automatically from eg. the
        # configuration file. So a changed value should overwrite the old one.
        fields_to_replace = [
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
        # for field in fields_to_replace:
        #     if getattr(other, field).strip():
        #         setattr(self, field, getattr(other, field))
        for field in self.fieldnames():
            new_value = getattr(other, field).strip()
            if field in fields_to_replace and new_value:
                if new_value:
                    setattr(self, field, new_value)
            # only update if the current value is empty
            elif not getattr(self, field).strip() and new_value:
                setattr(self, field, new_value)

    def validate(self):
        """
        Validate required metadata fields.

        Raises:
            ValueError: If any required field is empty.
        """
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
