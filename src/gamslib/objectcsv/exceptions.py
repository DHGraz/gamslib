"""Custom exceptions for the GAMSlib object CSV module.

Defines exception classes for error handling related to object and datastream CSV operations.
"""


class ValidationError(ValueError):
    """
    Exception raised for validation errors in object or datastream metadata.

    Args:
        message (str): Description of the error.
    """
