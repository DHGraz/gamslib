"""
Basic class for validators.

Defines an abstract Validator class and a Validator Factory class.

To register a new validator, create a subclass of Validator and decorate it
with `@ValidatorFactory.register(mime_type)`, where `mime_type` is the MIME
type that the validator should be associated with. For example:

```python
@ValidatorFactory.register("application/pdf")
class PDFValidator(Validator):
    def validate(self, 
                 file_path: Path, 
                 schemata: Optional[list[list[SchemaInfo]]] = None
        ) -> ValidationResult:
        # Implementation of PDF validation logic
```
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar, Optional, Type

from gamslib.formatdetect.formatinfo import FormatInfo
from gamslib.validation.schemainfo import SchemaInfo
from gamslib.validation.validationresult import ValidationResult


class Validator(ABC):
    """A base class for validators."""

    @abstractmethod
    def validate(
        self, file_path: Path, schemata: Optional[list[list[SchemaInfo]]] = None
    ) -> ValidationResult:
        """
        Validate a file against a schema.

        :param file_path: The path to the file to be validated.
        :param schema_path: The path to the schema to validate against.
        :return: A ValidationResult object containing the result of the validation.
        """


class ValidatorFactory:
    "A factory class for validator objects."

    _registry: ClassVar[dict[str, Type[Validator]]] = {}

    @classmethod
    def register(cls, mime_type: str):
        """Decorator, to register a Validator for a specific class.

        If a Validator class is decorated with
        `@ValidatorFactory.register()`it will be automatically registered by the given mime type,
        eg: `@ValidatorFactory.register("application/pdf")`
        """

        def wrapper(subclass: Type[Validator]):
            cls._registry[mime_type.lower()] = subclass
            return subclass

        return wrapper

    @classmethod
    def get_validator(cls, format_info: FormatInfo) -> Validator:
        """Return a Validator for a specific type."""
        if format_info is None:
            raise ValueError("FormatInfo must not be None.")
        validator_cls = cls._registry.get(format_info.mimetype.lower())
        if not validator_cls:
            # Use the AlwaysValidValidator, as no specific validator is registered for this type.
            # This will return a valid result, but with a warning.
            validator_cls = cls._registry.get("*")
        return validator_cls()
