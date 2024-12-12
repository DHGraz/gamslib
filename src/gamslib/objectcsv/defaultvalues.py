"""Default values for the datastream meatadata."""

DEFAULT_CREATOR = "Unknown"
DEFAULT_MIMETYPE = "application/octet-stream"
DEFAULT_OBJECT_TYPE = "text"
DEFAULT_RIGHTS = "Creative Commons Attribution-NonCommercial 4.0 (https://creativecommons.org/licenses/by-nc/4.0/)"
DEFAULT_SOURCE = "local"

# This is a mapping of filenames to default metadata values.
# Add new entries here if you want to add new metadata fields.
FILENAME_MAP = {
    "DC.xml": {
        "title": "Dublin Core Metadata",
        "description": "Dublin Core Metadata in XML format for this content file.",
    }
}