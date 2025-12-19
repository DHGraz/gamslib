"""Default values and namespaces for datastream metadata in GAMS projects.

This module provides constants for default metadata values and XML namespaces used in
object and datastream CSV generation. It also includes mappings for default titles and
descriptions for specific metadata files.

Contents:
    - NAMESPACES: Common XML namespaces for metadata files.
    - DEFAULT_CREATOR: Default value for the creator field.
    - DEFAULT_MIMETYPE: Default MIME type for datastreams.
    - DEFAULT_OBJECT_TYPE: Default object type for metadata.
    - DEFAULT_RIGHTS: Default rights statement for objects and datastreams.
    - DEFAULT_SOURCE: Default source value for metadata.
    - FILENAME_MAP: Mapping of filenames to default metadata fields (title, description).
"""

NAMESPACES = {
    "tei": "http://www.tei-c.org/ns/1.0",
    "lido": "http://www.lido-schema.org",
}
# NAMESPACES: Dictionary of XML namespaces used for metadata files.

DEFAULT_CREATOR = "Unknown"
# DEFAULT_CREATOR: Default value for the 'creator' metadata field.

DEFAULT_MIMETYPE = "application/octet-stream"
# DEFAULT_MIMETYPE: Default MIME type for datastreams.

DEFAULT_OBJECT_TYPE = "text"
# DEFAULT_OBJECT_TYPE: Default object type for metadata.

DEFAULT_RIGHTS = (
    "Creative Commons Attribution-NonCommercial 4.0 "
    "(http://creativecommons.org/licenses/by-nc/4.0/)"
)
# DEFAULT_RIGHTS: Default rights statement for objects and datastreams.

DEFAULT_SOURCE = "local"
# DEFAULT_SOURCE: Default source value for metadata.

FILENAME_MAP = {
    "DC.xml": {
        "title": "Dublin Core Metadata",
        "description": "Dublin Core meta data in XML format for this object.",
    },
    "RDF.xml": {"title": "RDF Statements", "description": ""},
}
# FILENAME_MAP: Mapping of metadata filenames to default title and description
