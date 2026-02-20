"""Provides a None Validator class.

The AlwaysValidValidator is a subclass of the abstract Validator class
and does not perform any validation.
It is used for all files which have no validator registered.
"""

from pathlib import Path
from typing import Optional

from gamslib.validation.schemainfo import SchemaInfo
from gamslib.validation.validationresult import ValidationResult, ValidationSubResult
from gamslib.validation.validator import Validator, ValidatorFactory


@ValidatorFactory.register("*")
class AlwaysValidValidator(Validator):
    "A validator that always returns a valid result (but with a warning)."

    def validate(
        self, file_path: Path, schemata: Optional[list[SchemaInfo]] = None
    ) -> ValidationResult:
        "Return a ValidationResult which indicates, that the file is valid but sets a warning."
        subresult = ValidationSubResult(
            is_valid=True,
            validator_name="AlwaysValidValidator",
            errors=[],
            warnings=["This file type has no validator registered."],
            message=f"Did not validate file '{file_path}', because I do not know how.",
        )
        result = ValidationResult(file_path)
        result.add_subresult(subresult)
        return result

    def add_subresult(self, subresult: ValidationSubResult):
        "This method is disabled fpr the AlwaysValidValidator."
        raise NotImplementedError
