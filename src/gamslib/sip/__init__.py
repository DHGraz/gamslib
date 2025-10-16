"""Tools for dealing with GAMS Submission Information Packages (SIPs).

The `gamslib.sip` subpackage provides tools for creating, validating, and managing
Submission Information Packages (SIPs) in accordance with GAMS and DSA standards.

The `utility` module provides a few helper functions for common tasks such as
counting files and bytes in a directory.

The `validation` submodule offers functions to validate the structure and metadata
of Bagit directories, including checks for required files, manifests, and SIP JSON metadata.
"""


class BagValidationError(Exception):
    """Exception raised when a bag is invalid."""


class ObjectDirectoryValidationError(Exception):
    """Exception raised when an object directory is invalid."""
