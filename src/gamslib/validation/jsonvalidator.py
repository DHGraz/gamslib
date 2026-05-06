"""Provides a JSON validator for validating JSON files against JSON schemas."""

from pathlib import Path
from typing import Optional

from gamslib.validation.schemainfo import SchemaInfo
from gamslib.validation.validationresult import ValidationResult
from gamslib.validation.validator import Validator, ValidatorFactory


@ValidatorFactory.register("application/json")
@ValidatorFactory.register("application/ld+json")
class JSONValidator(Validator):
    """Validator for JSON files."""

    def validate(
        self, file_path: Path, schemata: Optional[list[SchemaInfo]] = None
    ) -> ValidationResult:
        "Validate a JSON file against a schema."
        raise NotImplementedError("JSON validation not implemented yet.")
