"""Tools for dealing with GAMS Submission Information Packages (SIPs).

The `gamslib.sip` subpackage provides tools for creating, validating, and managing
Submission Information Packages (SIPs) in accordance with GAMS and DSA standards.

The `utility` module provides a few helper functions for common tasks such as
counting files and bytes in a directory.

The `validation` submodule offers functions to validate the structure and metadata
of Bagit directories, including checks for required files, manifests, and SIP JSON metadata.
"""

from pathlib import Path
from typing import Final


class BagValidationError(Exception):
    """Exception raised when a bag is invalid."""


# this is the current (latest) version of the SIP JSON schema
CURRENT_SIP_JSON_SCHEMA_URL: Final = (
    "https://gams.uni-graz.at/pub/gams/static/schemas/sip-schema-gams-v1.0.json"
)

# These deprected versions of the GAMS SIP JSON schema are still supported for validation,
# but should not be used for new SIPs.
DEPRECATED_SIP_JSON_SCHEMA_URLS: Final = []

RESOURCE_PATH = Path(__file__).parent / "resources"
