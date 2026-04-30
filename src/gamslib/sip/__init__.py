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


SIP_JSON_SCHEMA_URL: Final = "https://gams.uni-graz.at/OAIS/sip-schema-gams-v1.0.json"
# This is the path were the schema is stored in the package
RESOURCE_PATH = Path(__file__).parent / "resources"


# TODO: Remove this after all tests pass again
# It was moved to .sipjson.SCHEMA
#GAMS_SIP_SCHEMA_URL = "https://gams.uni-graz.at/OAIS/sip-schema-gams-v1.0.json"
