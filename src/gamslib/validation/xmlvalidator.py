"""Provides XML SchemaValidator classes for validation of XML schema languages.

Supported Schema languages are currently

- XML Schema (XSD),
- RelaxNG (RNG),
- RelaxNG Compact (RNC),
- Schematron
- DTD.
"""

# pylint: disable=c-extension-no-member
import abc
import io
import logging
from functools import lru_cache
from pathlib import Path
from typing import Final, Optional, Union

import lxml.isoschematron
import rnc2rng
from lxml import etree as ET

from gamslib.validation.combined_resolver import CombinedCatalogResolver
from gamslib.validation.schemainfo import SchemaInfo, SchemaType
from gamslib.validation.validationresult import ValidationResult, ValidationSubResult
from gamslib.validation.validator import (
    Validator,
    ValidatorFactory,
)

logger = logging.getLogger(__name__)
# Number of cached schemas per schema type
MAX_CACHE_SIZE = 32


class SchemaValidator(abc.ABC):
    """Abstract base class for schema-specific validators.

    SchemaValidator objects are small wrappers around existing schema validators
    (e.g. from lxml or saxon) that provide a common interface for validating an
    XML document  against a specific schema type.

    Each validator represents a specific schema  and provides a validate() method,
    which always returns a ValidationSubResult.
    """

    def __init__(self, schema_uri: str):
        self.schema_uri: str = schema_uri
        self.schema_validator = None
        self.resolver = CombinedCatalogResolver()
        self.parser = ET.XMLParser()
        self.parser.resolvers.add(self.resolver)
        # this is a special error message which is set if the creation of
        # the validator fails (not found, not well formed etc.).
        self._creation_error: Union[ValidationSubResult, None] = None

        try:
            self.schema_validator = self._make_validator(schema_uri)
        except ET.LxmlError as exp:
            errors = self._extract_lxml_errors_from_exception(exp)
            self._creation_error = ValidationSubResult(
                False,
                schema_uri=schema_uri,
                validator_name=self.validator_name,
                message=f"Unable to create the validator for '{schema_uri}: {exp}.'",
                errors=errors,
            )
        except Exception as exp:  # pylint: disable=broad-exception-caught
            self._creation_error = ValidationSubResult(
                False,
                schema_uri=schema_uri,
                validator_name=self.validator_name,
                message=f"Unable to create the validator for '{schema_uri}'",
                errors=[f"{exp!s}"],
            )

    @abc.abstractmethod
    def _make_validator(self, schema_uri: str) -> ET.XMLSchema:
        raise NotImplementedError

    @abc.abstractmethod
    def validate(self, tree: ET.ElementTree) -> ValidationSubResult:
        """Validate an XML file against the specific subtype.

        Args:
            tree (ET.ElementTree): The xml tree to be validated.
            file_path (Path): The xml file to be validated. We use both tree and file_path,
            because both are available when initializing the validator and some validators
            require the path instread of the tree.

        Returns:
            ValidatioSubnResult: A ValidationSubResult object
        """
        raise NotImplementedError

    @property
    def validator_name(self) -> str:
        """The name of the validator."""
        readable_name = self.__class__.__name__.replace("Validator", " Validator")
        return readable_name

    @classmethod
    def _extract_lxml_errors_from_exception(cls, exp: ET.LxmlError) -> list[str]:
        """Extract all errors form a LxmlError exception.

        Return errors as list of strings.
        """
        if not isinstance(exp, ET.LxmlError):
            raise ValueError(
                "Expected an lxml.etree.LxmlError exception, but got a different type."
            )
        errors = []
        for error in exp.error_log:
            errors.append(f"Line {error.line}, Column {error.column}: {error.message}")
        return errors


class XMLSchemaValidator(SchemaValidator):
    """A validator for XML Schema (XSD) schemas using lxml."""

    def _make_validator(self, schema_uri: str) -> ET.XMLSchema:
        tree = ET.parse(schema_uri, parser=self.parser)
        return ET.XMLSchema(tree)

    def validate(self, tree: ET.ElementTree) -> ValidationSubResult:
        """Validate an XML file against the XSD schema.

        Args:
            tree (ET.ElementTree): The xml tree to be validated.

        Returns:
            ValidationResult: A ValidationResult object
        """
        # catch if there was an error during the creation of the validator
        # e.g. because the schema was not found or not well formed
        if self._creation_error:
            return self._creation_error

        # do a normal validation
        result = ValidationSubResult(
            False, self.validator_name, schema_uri=self.schema_uri
        )

        try:
            if self.schema_validator.validate(tree):
                result.is_valid = True
                result.message = f"Document validates against schema {self.schema_uri}"
            else:
                result.message = (
                    f"Document does not validate against schema {self.schema_uri}"
                )
                result.errors = [str(err) for err in self.schema_validator.error_log]
        except Exception as e:  # pylint: disable=broad-exception-caught # pragma: no cover
            result.message = (
                f"Document does not validate against schema {self.schema_uri}"
            )
            result.errors = [f"XSD Error: {e!s}"]
        return result


class SchematronValidator(SchemaValidator):
    """A validator for Schematron schemas.

    This Validator uses lxml for validation by default, but it will use Saxon if the
    queryBinding of the schema is xslt2/xpath2 or higher, because lxml only supports xslt1.

    Falling back to saxon only works, if the saxonche package is installed. If saxon is
    not available, the validator will return a ValidationSubResult with an error message
    indicating that saxon is required for validation.
    """

    # use saxon for these bindings
    _SAXON_BINDINGS: Final[list[str]] = ["xslt2", "xslt3", "xpath2", "xpath3"]

    def __init__(self, schema_uri: str):
        self.binding = None  # self._get_schematron_binding(schema_uri)
        super().__init__(schema_uri)

    @property
    def validator_name(self) -> str:
        """The name of the validator."""
        if self.binding in SchematronValidator._SAXON_BINDINGS:
            return "XML Schematron Validator (saxon)"
        return "XML Schematron Validator (lxml)"

    def _make_validator(self, schema_uri: str):
        """Factory method to create the schema_validator for a schema.

        Important: This does not create an instance of SchemaValidator, but a schema 
        validator instance used internally by the SchemaVallidator subclass.
        """
        self.binding = self._get_schematron_binding(schema_uri)
        if self.binding in SchematronValidator._SAXON_BINDINGS:
            validator = self._make_saxon_validator(schema_uri)
        else:
            validator = self._make_lxml_validator(schema_uri)
        return validator

    def _make_lxml_validator(self, schema_uri: str):
        """Set the schema validator to a lxml.Schematron object.

        If something goes wrong (eg. the schema is not well formed or not found),
        self._creation_error is set to a ValidationSubResult with the error message and
        self.schema_validator is left to None.
        """
        schematron_document = ET.parse(schema_uri, parser=self.parser)
        return lxml.isoschematron.Schematron(schematron_document, store_report=True)

    def _make_saxon_validator(self, schema_uri: str):
        """Set the schema validator to a saxon Schematron validator.

        If something goes wrong (eg. the schema is not well formed or not found),
        self._creation_error is set to a ValidationSubResult with the error message and
        self.schema_validator is left to None.
        """
        try:
            from saxonche import (  # pylint: disable=import-outside-toplevel # noqa: PLC0415
                PySaxonProcessor,
            )

            saxon_proc = PySaxonProcessor(license=False)
            xslt_proc = saxon_proc.new_xslt30_processor()
            compiler_file = (
                Path(__file__).parent / "resources" / "schxslt2" / "transpile.xsl"
            ).as_posix()
            # convert Schematron (.sch) into a validating XSLT
            compiler_executable = xslt_proc.compile_stylesheet(
                stylesheet_file=compiler_file
            )
            schema_content = self.resolver.get_content(schema_uri).decode("utf-8")
            schema_xdm_node = saxon_proc.parse_xml(xml_text=schema_content)
            # compile schematron to XSLT
            validator_xslt_str = compiler_executable.transform_to_string(
                xdm_node=schema_xdm_node
            )
            # Compile the XSLT Validator
            return xslt_proc.compile_stylesheet(stylesheet_text=validator_xslt_str)

        except ImportError as exp:  # saxon not installed # pragma: no cover
            msg = (
                f"Cannot validate because binding {self.binding} requires Saxon. "
                "Install saxonche to enable this validation."
            )
            raise ImportError(msg) from exp

    def validate(
        self, tree: Optional[ET.ElementTree] = None, file_path: Optional[Path] = None
    ) -> ValidationSubResult:
        """Validate an XML file against the Schematron schema.

        Either a tree or a file_path must be given. Do not need both!
        Args:
            tree (ET.ElementTree): The xml tree to be validated.
                Should be None if a file_path is given.
            file_path (Path): The path to the file to be validated.
                Should be None if a tree is given.

        Returns:
            ValidationSubResult: A ValidationSubResult object
        """
        # we need to make sure that only one of tree or file_path is given
        if tree is None and file_path is None:
            raise ValueError("Either a tree or a file_path must be given.")
        if tree is not None and file_path is not None:
            raise ValueError(
                "Either a tree or a file_path must be given, but not both."
            )

        if self._creation_error is not None:
            return self._creation_error

        if file_path is not None:
            tree = ET.parse(file_path)  # pragma: no cover

        if self.binding in ["xslt2", "xslt3", "xpath2", "xpath3"]:
            file_path = Path(tree.docinfo.URL)
            return self._validate_with_saxon(file_path)
        return self._validate_with_lxml(tree)

    def _validate_with_lxml(self, tree: ET.ElementTree) -> ValidationSubResult:
        """Validate an XML file an return a ValidationSubResult.

        Use the lxml validator, which only supports xslt1 and may not work
        for all schemas, but does not require saxon.
        """
        result = ValidationSubResult(
            False, self.validator_name, schema_uri=self.schema_uri
        )

        try:
            if self.schema_validator.validate(tree):
                result.is_valid = True
                result.message = f"Document validates against schema {self.schema_uri}"
            else:
                result.message = (
                    f"Document does not validate against schema {self.schema_uri}"
                )
                result.errors, result.warnings = (
                    SchematronValidator.srvl_to_message_lists(
                        self.schema_validator.validation_report
                    )
                )
        # last ressort
        except Exception as e:  # pylint: disable=broad-exception-caught # pragma: no cover
            result.message = (
                f"Document does not validate against schema {self.schema_uri}"
            )
            result.errors = [f"Schematron Error: {e!s}"]
        return result

    def _validate_with_saxon(self, file_path: Path) -> ValidationSubResult:
        """Validate an XML file an return a ValidationSubResult.

        Use the Saxon validator, which supports xslt2/xslt3/xpath2/xpath3 and requires saxon.
        """
        result = ValidationSubResult(
            False, self.validator_name, schema_uri=self.schema_uri
        )
        xml_file = file_path.as_posix()
        svrl_report = self.schema_validator.transform_to_string(
            source_file=str(xml_file)
        )
        # print(svrl_report)
        svrl_report_root = ET.fromstring(svrl_report.encode("utf-8"))
        errors, warnings = SchematronValidator.srvl_to_message_lists(svrl_report_root)
        if errors:
            result.message = (
                f"Document does not validate against schema {self.schema_uri}"
            )
            result.errors = errors
            result.warnings = warnings
        else:
            result.is_valid = True
            result.message = f"Document validates against schema {self.schema_uri}"
        return result

    def _get_schematron_binding(self, schema_uri: str | Path) -> str:
        """Get the query binding of a Schematron schema.

        Use Path objects for local files, and strings for URIs.

        Return a string like 'xslt2' or None, if detecting the binding fails.
        """
        binding = "xslt"
        schema_bytes = self.resolver.get_content(str(schema_uri))
        if schema_bytes is None:
            raise ValueError(
                f"Unable to load schematron schema {schema_uri} to detect queryBinding."
            )
        schema_tree = ET.parse(io.BytesIO(schema_bytes))
        root = schema_tree.getroot()
        binding = root.get("queryBinding") or root.get(
            "{http://purl.oclc.org/dsdl/schematron}queryBinding"
        )
        return binding.lower() if binding else "xslt"

    @staticmethod
    def srvl_to_message_lists(report_root: ET.Element) -> tuple[list[str], list[str]]:
        """Convert a Schematron SVRL report to a list of errors and warnings.

        Each entry in both lists is a string containing the error or warning message.
        Both lists may be empty.
        """
        errors = []
        warnings = []
        ns = {"svrl": "http://purl.oclc.org/dsdl/svrl"}
        for failed_assert in report_root.findall("svrl:failed-assert", ns):
            for text_element in failed_assert.findall(".//svrl:text", ns):
                errors.append(
                    f"Error at {failed_assert.get('location', '')} "
                    f"({failed_assert.get('test', '')}): {text_element.text}"
                )
        for successful_report in report_root.findall("svrl:successful-report", ns):
            for text_element in successful_report.findall(".//svrl:text", ns):
                warnings.append(
                    f"Warning at {successful_report.get('location', '')} "
                    f"({successful_report.get('test', '')}): {text_element.text}"
                )
        return errors, warnings


class RelaxNGValidator(SchemaValidator):
    """A validator for RelaxNG schemas using lxml."""

    def _make_validator(self, schema_uri: str):
        rng_document = ET.parse(schema_uri, parser=self.parser)
        return ET.RelaxNG(rng_document)

    def validate(self, tree: ET.ElementTree) -> ValidationSubResult:
        """Validate an XML file against the RelaxNG schema.

        Args:
            tree (ET.ElementTree): The xml tree to be validated.

        Returns:
            ValidationResult: A ValidationResult object
        """
        if self._creation_error:
            return self._creation_error

        result = ValidationSubResult(
            False, self.validator_name, schema_uri=self.schema_uri
        )

        try:
            if self.schema_validator.validate(tree):
                result.is_valid = True
                result.message = f"Document validates against schema {self.schema_uri}"
            else:
                result.message = (
                    f"Document does not validate against schema {self.schema_uri}"
                )
                result.errors = [str(err) for err in self.schema_validator.error_log]
        except Exception as e:  # pylint: disable=broad-exception-caught # pragma: no cover
            result.message = (
                f"Document does not validate against schema {self.schema_uri}"
            )
            result.errors = [f"RelaxNG Error: {e!s}"]
        return result


class RelaxNGCompactValidator(RelaxNGValidator):
    """A validator for RelaxNG Compact schemas."""

    def _make_validator(self, schema_uri: str):
        """Factory method to create the appropriate schema_validator for this schema.

        Important: This does not create an instance of SchemaValidator, but a schema 
        validator instance used internally by the SchemaVallidator subclass.
        """
        rnc = self.resolver.get_content(schema_uri).decode("utf-8")
        # convert rnc to rng using rnc2rngm which expects a string
        ast = rnc2rng.loads(rnc)
        rng_xml = rnc2rng.dumps(ast).encode("utf-8")
        rng_document = ET.parse(io.BytesIO(rng_xml), parser=self.parser)
        return ET.RelaxNG(rng_document)


class DTDValidator(SchemaValidator):
    """A validator for DTD schemas using lxml."""

    def _make_validator(self, schema_uri):
        dtd_parser = ET.XMLParser(load_dtd=True)
        dtd_parser.resolvers.add(self.resolver)
        dummy_xml = f'<!DOCTYPE root SYSTEM "{schema_uri}"><root/>'.encode("utf-8")
        # we need the tree, so we have to put the string into an io.BytesIO object
        tree = ET.parse(io.BytesIO(dummy_xml), parser=dtd_parser)
        # Prefer external DTD from SYSTEM identifier; fallback to internal DTD.
        if tree.docinfo.externalDTD is not None:
            return tree.docinfo.externalDTD
        raise ValueError(f"Unable to load DTD from {schema_uri}.")

    def validate(self, tree: ET.ElementTree):
        if self._creation_error:
            return self._creation_error

        # A minimal common SubResult
        result = ValidationSubResult(
            False, self.validator_name, schema_uri=self.schema_uri
        )

        # do a normal validation
        try:
            if self.schema_validator.validate(tree):
                result.is_valid = True
                result.message = f"Document validates against DTD {self.schema_uri}"
            else:
                result.message = (
                    f"Document does not validate against DTD {self.schema_uri}"
                )
                result.errors = [str(err) for err in self.schema_validator.error_log]
        # last ressort
        except Exception as e:  # pylint: disable=broad-exception-caught # pragma: no cover
            result.message = f"Document does not validate against DTD {self.schema_uri}"
            result.errors = [f"XSD Error: {e!s}"]
        return result


# TODO: what about internal DTDs?


class SchemaProvider:
    """Load a schema from schema_uri and return a SchemaValidator instance for this schema.

    Uses caching for performance reasons.
    """

    @staticmethod
    def get_schemavalidator(
        schema_uri: str, schema_type: SchemaType
    ) -> SchemaValidator:
        """Return a Validator instance for the given schema_uri and schema_type.

        The returned object implements the SchemaValidator interface (it has a validate method).

        Args:
            schema_uri (str): URI to the schema file.
            schema_type (SchemaType str): The type of the schema

        Raises:
            ValueError: If the schema type is unknown.
        Returns:
            SchemaValidator: A SchemaValidator instance for the given schema.
        """
        if schema_type == SchemaType.XSD:
            return SchemaProvider.get_xsd(schema_uri)
        if schema_type == SchemaType.RNG:
            return SchemaProvider.get_relaxng(schema_uri)
        if schema_type == SchemaType.RNC:
            return SchemaProvider.get_relaxng_compact(schema_uri)
        if schema_type == SchemaType.DTD:
            return SchemaProvider.get_dtd(schema_uri)
        if schema_type == SchemaType.SCH:
            return SchemaProvider.get_schematron(schema_uri)
        raise ValueError(f"Unknown schema type '{schema_type}'")

    @staticmethod
    @lru_cache(maxsize=MAX_CACHE_SIZE)
    def get_xsd(schema_uri: str) -> XMLSchemaValidator:
        """Return an lxml XMLSchemaValidator object.

        The schemaalitator objects are cached for performance.

        Args:
            schema_uri (str): URI to the schema file.

        Returns: XMLSchemaValidator: An XMLSchemaValidator object
        """
        return XMLSchemaValidator(schema_uri)

    @staticmethod
    @lru_cache(maxsize=MAX_CACHE_SIZE)
    def get_schematron(schema_uri: str) -> SchematronValidator:
        """Return an SchematronValidator object.

        The returned class is able to use either lxml or saxon, depending on the
        query binding of the schema an if saxonche is installed.

        The schema objects are cached for performance.

        Args:
            schema_path (str): Path to the schema file.

        Returns:
            SchematronValidator: An Schematron object
        """
        return SchematronValidator(schema_uri)

    @staticmethod
    @lru_cache(maxsize=MAX_CACHE_SIZE)
    def get_relaxng(schema_uri: str) -> RelaxNGValidator:
        """Return an lxml RelaxNG object.

        The schema objects are cached for performance.

        Args:
            schema_path (str): Path to the schema file.

        Returns:
            RelaxNGValidator: A RelaxNGValidator object
        """
        return RelaxNGValidator(schema_uri)

    @staticmethod
    @lru_cache(maxsize=MAX_CACHE_SIZE)
    def get_relaxng_compact(schema_uri: str) -> RelaxNGCompactValidator:
        """Return a RelaxNGCompactValidator object."""
        return RelaxNGCompactValidator(schema_uri)

    @staticmethod
    @lru_cache(maxsize=MAX_CACHE_SIZE)
    def get_dtd(schema_uri: str) -> ET.DTD:
        """Return a DTDValidator object.

        The schema objects are cached for performance.

        Args:
            schema_path (str): Path to the schema file.

        Returns:
            DTDValidator: An DTDValidator object.
        """
        return DTDValidator(schema_uri)


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
            try:
                validator = SchemaProvider.get_schemavalidator(
                    schema_info.schema_uri, schema_info.schema_type
                )
                result.add_subresult(validator.validate(doc))
            except ValueError as exp:  # this happens if the schema type is unknown
                result.add_subresult(
                    ValidationSubResult(
                        False,
                        "XML Schema Validator",
                        schema_uri=schema_info.schema_uri,
                        message=f"Unknown schema format for schema '{schema_info.schema_uri}'",
                        errors=[f"ValueError: {exp!s}"],
                    )
                )
        return result
