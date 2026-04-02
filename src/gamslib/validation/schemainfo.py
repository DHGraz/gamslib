"""Provides the SchemaInfo class.

This class is a dataclass, which encapsulates information about a detected schema,
including its URI, mimetype, schematypens, charset, and type. The class also includes
methods for detecting the schema type based on the provided information.
"""

import enum
import re
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar


# map extensions to schema types
class SchemaType(enum.StrEnum):
    """Enumeration of the different types of XML schema."""

    XSD = "XML Schema Definition"
    RNG = "Relax NG"
    RNC = "Relax NG Compact"
    SCH = "Schematron"
    DTD = "Document Type Definition"

    # TODO: add a type for each supported schem type (json etc.)

    UNKNOWN = "Unknown Schema Type"


@dataclass
class SchemaInfo:
    """Keeps data about a detected schema.

    The only required member is schema_uri
    """

    schema_uri: str  # uri
    mimetype: str = ""
    schematypens: str = ""
    charset: str = "utf-8"
    schema_type: SchemaType = None

    extension_map: ClassVar[dict[str, SchemaType]] = {
        ".xsd": SchemaType.XSD,
        ".rng": SchemaType.RNG,
        ".rnc": SchemaType.RNC,
        ".sch": SchemaType.SCH,
        ".dtd": SchemaType.DTD,
    }

    def __post_init__(self):
        # make sure schema_location is always a URI
        if not re.match(r"^(https?|file)://.*", self.schema_uri):
            schema_path = Path(self.schema_uri)
            self.schema_uri = schema_path.resolve().as_uri()

        # Only in rare cases is the schema type already known from object creation
        if not self.schema_type:
            self._detect_schema_type()

    def _detect_schema_type(self):
        """Detect the schema type based on the given data."""
        # this is the order of method calls in which we try to detect the schema type
        detection_sequence = [
            self._detect_by_schematypens,
            self._detect_by_mimetype,
            self._detect_by_extension,
        ]
        for method in detection_sequence:
            self.schema_type = method()
            if self.schema_type is not None:
                break
        if self.schema_type is None:
            raise ValueError(
                f"Unknown schema type or schema type not supported: {self.schema_uri}"
            )

    def _detect_by_schematypens(self) -> None:
        """Set self.schema_type based on the schematypens attribute."""
        schematype = None
        if self.schematypens == "http://relaxng.org/ns/structure/1.0":
            schematype = SchemaType.RNG
        elif self.schematypens == "http://www.w3.org/2001/XMLSchema":
            schematype = SchemaType.XSD
        elif self.schematypens == "http://purl.oclc.org/dsdl/schematron":
            schematype = SchemaType.SCH
        return schematype

    def _detect_by_mimetype(self) -> bool:
        """Detect the schema type by the mimetype.

        This only checks for schema-specific types, not for generic XML types.
        """
        schema_type = None
        if self.mimetype == "application/xml-dtd":
            schema_type = SchemaType.DTD
        elif self.mimetype == "application/relax-ng-compact-syntax":
            schema_type = SchemaType.RNC
        return schema_type

    def _detect_by_extension(self) -> bool:
        """Detect the schema type by the file extension.

        This is some sort of last ressortî
        """
        extension = "." + self.schema_uri.split(".")[-1]
        return SchemaInfo.extension_map.get(extension)
