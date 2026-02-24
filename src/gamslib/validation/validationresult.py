"""This module defines the ValidationResult and ValidationSubResult classes.

All Validator objects return a ValidationResult object when validating a file. 

The ValidationResult class contains a list of ValidationSubResult objects and
methods/properties to access accumulated results. Each ValidationSubResult represents 
the result of a single validation step of a file validation. This is important, because
a file can be validated against multiple schemata and/or with multiple validators, 
which can all produce their own result.

The most important property of a ValidationResult is `is_valid`, which is True if all subresults 
are valid and False if at least one subresult is invalid.

To access the individual subresults, the `get_subresults()` method can be used, which 
yields all subresult objects.

For convenience, the ValidationResult class also provides methods to get all messages, 
errors and warnings collected during validation.

  * get_messages() returns a list of all messages as strings collected during validation. 
    Each message is a short text indicating the result of a validation step, 
    e.g. "Validated against schema X" or "Validation failed because of Y". 
  * get_errors() returns a list of all errors occurred during validation as strings. 
    If result.is_valid is True, this method should return an empty list, otherwise it 
    should return a list of error messages indicating the reasons for the validation 
    failure (retrieved from the validator).
  * get_warnings() returns a list of all validation warnings as list of Strings. 
    Warnings are not critical for the validation result, but they can indicate 
    potential issues or problems with the file, e.g. 
    "This file type has no validator registered." or 
    "The schema used for validation is deprecated.".
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator


@dataclass
class ValidationSubResult:
    """The result of a single validation step of a file validation.

    All sub-results for a single File are collected in a ValidationResult object.
    """

    is_valid: bool
    validator_name: str
    schema_uri: str = ""
    message: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def has_warnings(self):
        "Return True if there are any warnings."
        return len(self.warnings) > 0

@dataclass
class ValidationResult:
    """This is what a Validator object returns when validating a file.

    It contains a list of ValidationSubResult objects and methods/properties to
    access accumulated results.
    """

    file_path: Path

    _subresults: list[ValidationSubResult] = field(default_factory=list, init=False)

    def add_subresult(self, subresult: ValidationSubResult):
        """Add a subresult to the list of subresults."""
        self._subresults.append(subresult)

    @property
    def is_valid(self):
        "Return True if all subresults are valid."
        return all(subresult.is_valid for subresult in self._subresults)
    
    @property
    def has_warnings(self):
        "Return True if there are any warnings."
        return any(subresult.has_warnings for subresult in self._subresults)

    def get_subresults(self) -> Generator[list[ValidationSubResult], None, None]:
        "Yield all subresult objects."
        yield from self._subresults

    def get_messages(self) -> list[str]:
        "Return a list of messages collected during validation."
        return [subresult.message for subresult in self._subresults]

    def get_errors(self) -> list[str]:
        "Return a list of errors collected during validation."
        return [error for subresult in self._subresults for error in subresult.errors]

    def get_warnings(self) -> list[str]:
        "Return a list of warnings collected during validation."
        return [
            warning for subresult in self._subresults for warning in subresult.warnings
        ]

    def __str__(self):
        "Return a string representation of the ValidationResult object."
        validation_status = "valid" if self.is_valid else "invalid"
        return f"ValidationResult for file '{self.file_path}': {validation_status}."
