"""A validator for PDF files."""

from pathlib import Path
from typing import Optional

from gamslib.validation.schemainfo import SchemaInfo
from gamslib.validation.validationresult import ValidationResult
from gamslib.validation.validator import Validator, ValidatorFactory


@ValidatorFactory.register("application/pdf")
class PDFValidator(Validator):
    """A validator for PDF files."""

    def validate(
        self, file_path: Path, schemata: Optional[list[SchemaInfo]] = None
    ) -> ValidationResult:
        raise NotImplementedError("PDF validation not implemented yet.")
