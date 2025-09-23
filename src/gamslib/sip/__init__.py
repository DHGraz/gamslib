"Validtion exceptions for SIP validation."


class BagValidationError(Exception):
    """Exception raised when a bag is invalid."""


class ObjectDirectoryValidationError(Exception):
    """Exception raised when an object directory is invalid."""
