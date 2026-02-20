"""Provides a XML Vaölidator class with support for various schema languages."""

# pylint: disable=c-extension-no-member
from functools import lru_cache
from pathlib import Path
from typing import Optional

import lxml.isoschematron
from lxml import etree as ET

from gamslib.validation.validator import (
    Validator,
    ValidatorFactory,
)
from gamslib.validation.schemainfo import SchemaInfo, SchemaType
from gamslib.validation.validationresult import ValidationResult, ValidationSubResult

# Number of cached schemas per schema type
MAX_CACHE_SIZE = 32


class SchemaProvider:
    """Load a compile schema. Uses caching for performance reasons."""

    @staticmethod
    @lru_cache(maxsize=MAX_CACHE_SIZE)
    def get_xsd(schema_uri: str) -> ET.XMLSchema:
        """Return an lxml XMLSchema object.

        The schema objects are cached for performance.

        Args:
            schema_uri (str): URI to the schema file.

        Returns:
            ET.XMLSchema: An lxml XMLSchema object
        """
        schema_doc = ET.parse(schema_uri)
        return ET.XMLSchema(schema_doc)

    @staticmethod
    @lru_cache(maxsize=MAX_CACHE_SIZE)
    def get_schematron(schema_path: str) -> ET.Schematron:
        """Return an lxml Schematron object.

        The schema objects are cached for performance.

        Args:
            schema_path (str): Path to the schema file.

        Returns:
            ET.Schematron: An lxml Schematron object
        """
        schema_doc = ET.parse(schema_path)
        # TODO: libxml does not support all query bindings, 
        # either restrict to some bindings or use a diffent validator (saxon?)
        query_binding = schema_doc.getroot().get("queryBinding", "xslt1")
        if query_binding == "xslt1":
            return lxml.isoschematron.Schematron(schema_doc)

        # This is complicated, because lxml does not support xslt2.
        # We need to set the queryBinding to xslt1 and hope that it works
        # or we use the pyschematron packages, which neither supports xslt2,
        # but works with the xslt2 queryBinding as long as xslt only uses
        # XPath.
        # Falling back to a remote validation service is also an option,
        # but would require network access and a service to be available.
        try:
            schema_doc.getroot().set("queryBinding", "xslt1")
            return lxml.isoschematron.Schematron(schema_doc)
        except ValueError:
            schema_doc.getroot().set("queryBinding", "xslt2")
            return lxml.isoschematron.Schematron(schema_doc)

    @staticmethod
    @lru_cache(maxsize=MAX_CACHE_SIZE)
    def get_relaxng(schema_path: str) -> ET.RelaxNG:
        """Return an lxml RelaxNG object.

        The schema objects are cached for performance.

        Args:
            schema_path (str): Path to the schema file.

        Returns:
            ET.RelaxNG: An lxml RelaxNG object
        """
        # try:
        #    schema_doc = ET.parse(schema_path)
        #    return ET.RelaxNG(schema_doc)
        # except ET.XMLSyntaxError:
        return ET.RelaxNG(file=schema_path)
        # raise ValueError(f"Cannot open schema file '{schema_path}': {exp.msg}") from exp

    # TODO: maybe we need a special getter for rnc (unsure if transformation is don automatically)
    #     see https://github.com/djc/rnc2rng/issues/43#issuecomment-1776970457

    @staticmethod
    @lru_cache(maxsize=MAX_CACHE_SIZE)
    def get_dtd(schema_path: str) -> ET.DTD:
        """Return an lxml DTD object.

        The schema objects are cached for performance.

        Args:
            schema_path (str): Path to the schema file.

        Returns:
            ET.DTD: An lxml DTD object
        """
        # schema_doc = ET.parse(schema_path)
        return ET.DTD(schema_path)  # ET.DTD(schema_doc)


@ValidatorFactory.register("application/rdf+xml")
@ValidatorFactory.register("application/tei+xml")
@ValidatorFactory.register("application/xml")
@ValidatorFactory.register("text/xml")
class XMLValidator(Validator):
    """Validate an XML Document against a list of schemas."""

    def validate(
        self, file_path: Path, schemata: Optional[list[SchemaInfo]] = None
    ) -> ValidationResult:
        """Validate an XML file against a schema.

        Args:
            file_path (Path): The xml file to be validated.
            schemata (list of SchemaInfo objects): The schemas to validate against.

        Returns:
            ValidationResult: A ValidationResult object
        """
        result = ValidationResult(file_path)
        # is file well formed?
        try:
            doc = ET.parse(file_path)
        except ET.XMLSyntaxError as exp:
            result.add_subresult(
                ValidationSubResult(
                    False,
                    "XML Wellformedness Validator",
                    message=f"XML document '{file_path}' has syntax errors (not well formed?)",
                    errors=[f"Syntax error: {exp!s}"],
                )
            )
            return result  # validating does not make sense
        # do we have schemas to validate against?
        if not schemata:
            result.add_subresult(
                ValidationSubResult(
                    True,
                    "XML Validator",
                    message="Document has no schemas to validate against",
                    warnings=["Document '{file_path}' has no schemas"],
                )
            )
        for schema_info in schemata:
            match schema_info.schema_type:
                case SchemaType.XSD:
                    result.add_subresult(self._validate_xsd(doc, schema_info))
                case SchemaType.SCH:
                    result.add_subresult(self._validate_schematron(doc, schema_info))
                case SchemaType.RNG:
                    result.add_subresult(self._validate_relaxng(doc, schema_info))
                case SchemaType.RNC:
                    result.add_subresult(
                        self._validate_relaxng_compact(doc, schema_info)
                    )
                case SchemaType.DTD:
                    result.add_subresult(self._validate_dtd(doc, schema_info))
                case _:
                    result.add_subresult(
                        ValidationSubResult(
                            False,
                            "XMLValidator",
                            schema_uri=schema_info.schema_uri,
                            message="Unknown schema type",
                            errors=[
                                f"Unknown schema format: {schema_info.schema_uri} for file {file_path}"
                            ],
                        )
                    )
        return result

    def _validate_xsd(
        self, doc: ET._ElementTree, schema_info: SchemaInfo
    ) -> ValidationResult:
        try:
            xsd_validator = SchemaProvider.get_xsd(schema_info.schema_uri)

            if xsd_validator.validate(doc):
                return ValidationSubResult(
                    True,
                    "XML XSD Validator",
                    schema_uri=schema_info.schema_uri,
                    message=f"Document validates against schema {schema_info.schema_uri}",
                )
            errors = [str(err) for err in xsd_validator.error_log]
            return ValidationSubResult(
                False,
                "XML XSD Validator",
                schema_uri=schema_info.schema_uri,
                message=f"Document does not validate against schema {schema_info.schema_uri}",
                errors=errors,
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            return ValidationSubResult(
                False,
                "XML XSD Validator",
                schema_uri=schema_info.schema_uri,
                message=f"Document does not validate against schema {schema_info.schema_uri}",
                errors=[f"XSD Error: {e!s}"],
            )

    def _validate_schematron(
        self, doc: ET._ElementTree, schema_info: SchemaInfo
    ) -> ValidationResult:
        try:
            schematron_validator = SchemaProvider.get_schematron(schema_info.schema_uri)

            if schematron_validator.validate(doc):
                return ValidationSubResult(
                    True,
                    "XML Schematron Validator",
                    schema_uri=schema_info.schema_uri,
                    message=f"Document validates against schema {schema_info.schema_uri}",
                )
            errors = [str(err) for err in schematron_validator.error_log]
            return ValidationSubResult(
                False,
                "XML Schematron Validator",
                message=f"Document does not validate against schema {schema_info.schema_uri}",
                errors=errors,
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            return ValidationSubResult(
                False,
                "XML Schematron Validator",
                message=f"Document does not validate against schema {schema_info.schema_uri}",
                errors=[f"Schematron Error: {e!s}"],
            )

    def _validate_relaxng(self, doc, schema_info: SchemaInfo) -> ValidationResult:
        try:
            relaxng_validator = SchemaProvider.get_relaxng(schema_info.schema_uri)

            if relaxng_validator.validate(doc):
                return ValidationSubResult(
                    True,
                    "XML RelaxNG Validator",
                    schema_uri=schema_info.schema_uri,
                    message=f"Document validates against schema {schema_info.schema_uri}",
                )
            errors = [str(err) for err in relaxng_validator.error_log]
            return ValidationSubResult(
                False,
                "XML RelaxNG Validator",
                schema_uri=schema_info.schema_uri,
                message=f"Document does not validate against schema {schema_info.schema_uri}",
                errors=errors,
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            return ValidationSubResult(
                False,
                "XML RelaxNG Validator",
                message=f"Document does not validate against schema {schema_info.schema_uri}",
                errors=[f"RNG Error: {e!s}"],
            )

    # TODO: Maybe we do not need to distinguish between rnc and rng
    def _validate_relaxng_compact(
        self, doc, schema_info: SchemaInfo
    ) -> ValidationResult:
        try:
            relaxng_validator = SchemaProvider.get_relaxng(schema_info.schema_uri)

            if relaxng_validator.validate(doc):
                return ValidationSubResult(
                    True,
                    "XML RelaxNG Compact Validator",
                    schema_uri=schema_info.schema_uri,
                    message=f"Document validates against schema {schema_info.schema_uri}",
                )
            errors = [str(err) for err in relaxng_validator.error_log]
            return ValidationSubResult(
                False,
                "XML RelaxNG Validation",
                schema_uri=schema_info.schema_uri,
                message=f"Document does not validate against schema {schema_info.schema_uri}",
                errors=errors,
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            return ValidationSubResult(
                False,
                "XML RelaxNG Compact Validator",
                schema_uri=schema_info.schema_uri,
                message=f"Document does not validate against schema {schema_info.schema_uri}",
                errors=[f"RNC Error: {e!s}"],
            )

    def _validate_dtd(
        self, doc: ET._ElementTree, schema_info: SchemaInfo
    ) -> ValidationResult:
        try:
            dtd_validator = SchemaProvider.get_dtd(schema_info.schema_uri)
            if dtd_validator.validate(doc):
                return ValidationSubResult(
                    True,
                    "XML DTD Validator",
                    schema_uri=schema_info.schema_uri,
                    message=f"Document validates against schema {schema_info.schema_uri}",
                )
            errors = [str(err) for err in dtd_validator.error_log]
            return ValidationSubResult(
                False,
                "XML DTD Validator",
                schema_uri=schema_info.schema_uri,
                message=f"Document does not validate against schema {schema_info.schema_uri}",
                errors=errors,
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            return ValidationSubResult(
                False,
                "XML DTD Validator",
                schema_uri=schema_info.schema_uri,
                message=f"Document does not validate against schema {schema_info.schema_uri}",
                errors=[f"DTD Error: {e!s}"],
            )

    # TODO: this was proposed by AI. Does it make sense?
    # def _validate_internal_dtd_schema(self) -> ValidationResult:
    #     try:
    #         tree = ET.parse(self.file_path, ET.XMLParser(dtd_validation=True))
    #         validation_result = ValidationSubResult("internal DTD", "internal DTD")
    #         validation_result.valid = True
    #         return validation_result
    #     except ET.XMLSyntaxError as exp:
    #         validation_result = ValidationSubResult()
    #         validation_result.valid = False
    #         validation_result.add_error(exp.msg)
    #         return validation_result
