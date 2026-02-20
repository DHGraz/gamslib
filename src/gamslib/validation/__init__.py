"""A sub package fpor file format and schema validation." """

import warnings
from pathlib import Path

from gamslib import formatdetect
from gamslib.formatdetect.formatinfo import FormatInfo
from gamslib.validation import xmlschemadetector
from gamslib.validation.schemainfo import SchemaInfo
from gamslib.validation.validator import ValidatorFactory


def extract_referenced_schemas(
    file_path: Path,
    format_info: FormatInfo | None = None,
    use_default_schema: bool = True,
) -> list[SchemaInfo]:
    """Find schema referenced in file_path.

    :param file_path: Path to the file to check for referenced schemas.
    :param format_info: The format information of the file. As detecting the format can
        be expensive, you can pass the format information here if you have it already.
    :param use_default_schema: If True, a default schema is used for certain file types
        if no schema is referenced inside the document.
        E.g.: If True, a TEI file without any referenced schema will be validated against tei_all.xsd
    :return: A list of SchemaInfo objects
    """
    referenced_schemas = []
    if format_info is not None:
        if format_info.is_xml_type():
            referenced_schemas = xmlschemadetector.detect_schemata(
                file_path, format_info, use_default_schema
            )
        elif format_info.is_json_type():
            raise NotImplementedError("JSON schema detection not implemented")
    return referenced_schemas


def validate(
    file_path: Path,
    schema_location: str | None = None,
    format_info: FormatInfo | None = None,
):
    """Validate a file.

    :param file_path: Path to the file to validate.
    :param schema_location: The schema location to validate against.
           If not given, we try to detect the schema from the file.
    :param format_info: The format information of the file. As detecting the format
              can be expensive, you can pass the format information here if you habe it already.
    :return: A ValidationResult
    """
    schemas: list[SchemaInfo] = []
    if format_info is None:
        format_info = formatdetect.detect_format(file_path)
    # if a schema location is given, we use only this, unless other
    # referenced schemas are found in the file. This means that we do no not use a
    # default schema for specific suptypes if a schema location is given.
    use_default_schema = True
    if schema_location is not None:
        schemas.append(SchemaInfo(Path(schema_location).resolve().as_uri()))
        use_default_schema = False
    schemas.extend(
        extract_referenced_schemas(file_path, format_info, use_default_schema)
    )

    validator = ValidatorFactory.get_validator(format_info)
    result = validator.validate(file_path, schemas)
    return result
