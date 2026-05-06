"""Provides a RDF validator for validating RDF files against RDF schemas.

The RDFValidator is a subclass of the abstract Validator class and implements
the validate method for RDF files.
"""

from pathlib import Path
from typing import Optional

from gamslib.validation.schemainfo import SchemaInfo
from gamslib.validation.validationresult import ValidationResult
from gamslib.validation.validator import Validator, ValidatorFactory


@ValidatorFactory.register("application/pdf")
class RDFValidator(Validator):
    """Validator for RDF files."""

    def validate(
        self, file_path: Path, schemata: Optional[list[SchemaInfo]] = None
    ) -> ValidationResult:
        "Validate a RDF file against a schema."
        raise NotImplementedError("RDF validation not implemented yet.")
