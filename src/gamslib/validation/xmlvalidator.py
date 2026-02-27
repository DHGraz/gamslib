"""Provides a XML Vaölidator class with support for various schema languages."""

# pylint: disable=c-extension-no-member
import abc
from functools import lru_cache
from pathlib import Path
from typing import Final, Optional

import lxml.isoschematron
from lxml import etree as ET

import gams_xml_catalog # this is important as we need the catalog

from gamslib.validation.validator import (
    Validator,
    ValidatorFactory,
)
from gamslib.validation.schemainfo import SchemaInfo, SchemaType
from gamslib.validation.validationresult import ValidationResult, ValidationSubResult

# Number of cached schemas per schema type
MAX_CACHE_SIZE = 32


class SchemaValidator(abc.ABC):
    """Abstract base class for schema-specific validators.

    SchemaValidator objects are small wrappers around existing schema validator (e.g.
    from lxml or saxon) that provide a common interface for validating an XML document
    against a specific schema type.

    Each validator represents a specific schema  and provides a validate() method, which
    always returns a ValidationSubResult.
    TODO: document what happens if parsing the schema fails, e.g. because the file is not found or not well formed.
    """

    def __init__(self, schema_uri: str):
        self.schema_uri: str = schema_uri
        # this is a special error message which is set if the creation of the validator fails.
        # this might happen if the schema file is not found, not well formed, or if there is an error in the schema itself.
        self._creation_error: Optional[ValidationSubResult] = None

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


class XMLSchemaValidator(SchemaValidator):
    """A validator for XML Schema (XSD) schemas using lxml."""

    def __init__(self, schema_uri: str):
        super().__init__(schema_uri)
        try:
            schema_tree = ET.parse(schema_uri)
            self.schema = ET.XMLSchema(schema_tree)
        except Exception as exp:  # pylint: disable=broad-exception-caught
            self._creation_error = ValidationSubResult(
                False,
                "XML XSD Validator",
                message=f"Unable to create the validator for '{schema_uri}'",
                errors=[f"XMLSchemaParseError: {exp!s}"],
            )

    def validate(self, tree: ET.ElementTree) -> ValidationSubResult:
        """Validate an XML file against the XSD schema.

        Args:
            tree (ET.ElementTree): The xml tree to be validated.

        Returns:
            ValidationResult: A ValidationResult object
        """
        # catch if there was an error during the creation of the validator, e.g. because the
        # schema was not found or not well formed, and return a ValidationSubResult with the error message.
        if self._creation_error:
            return self._creation_error

        # do a normal validation
        result = ValidationSubResult(
            False, "XML XSD Validator (lxml)", schema_uri=self.schema_uri
        )

        try:
            if self.schema.validate(tree):
                result.is_valid = True
                result.message = f"Document validates against schema {self.schema_uri}"
            else:
                result.message = (
                    f"Document does not validate against schema {self.schema_uri}"
                )
                result.errors = [str(err) for err in self.schema.error_log]
        except Exception as e:  # pylint: disable=broad-exception-caught
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
    SAXON_BINDINGS: Final[list[str]] = ["xslt2", "xslt3", "xpath2", "xpath3"]

    # validator names
    LXML_NAME: Final[str] = "XML Schematron Validator (lxml)"
    SAXON_NAME: Final[str] = "XML Schematron Validator (saxon)"

    def __init__(self, schema_uri: str):
        super().__init__(schema_uri)
        self.schema_validator = None
        self.binding = self._get_schematron_binding(schema_uri)
        if self.binding is not None:
            if self.binding in SchematronValidator.SAXON_BINDINGS:
                self._make_saxon_validator()
            else:
                self._make_lxml_validator()

    def _make_lxml_validator(self):
        """Set the schema validator to a lxml.Schematron object.

        If something goes wrong (eg. the schema is not well formed or not found),
        self._creation_error is set to a ValidationSubResult with the error message and
        self.schema_validator is left to None.
        """
        # This result is only used as self._creation_error if creation fails
        result = ValidationSubResult(
            False, SchematronValidator.LXML_NAME, schema_uri=self.schema_uri
        )
        try:
            schema_tree = ET.parse(self.schema_uri)
            self.schema_validator = lxml.isoschematron.Schematron(
                schema_tree, store_report=True
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            # unable to create the schema object, e.g. schema is not well formed or not found
            result.message = ("Unable to create the Schematron validator instance for  "
                              f"schema {self.schema_uri}")
            result.errors = [f"Schema Error: {e!s}"]
            self._creation_error = result

    def _make_saxon_validator(self):
        """Set the schema validator to a saxon Schematron validator.

        If something goes wrong (eg. the schema is not well formed or not found),
        self._creation_error is set to a ValidationSubResult with the error message and
        self.schema_validator is left to None.
        """
        result = ValidationSubResult(
            False, SchematronValidator.SAXON_NAME, schema_uri=self.schema_uri
        )
        try:
            from saxonche import PySaxonProcessor  # pylint: disable=import-outside-toplevel  # noqa: PLC0415
            with PySaxonProcessor(license=False) as proc:
                xslt_proc = proc.new_xslt30_processor()
                compiler_file = (
                    Path(__file__).parent / "resources" / "schxslt2" / "transpile.xsl"
                ).as_posix()
                # convert Schematron (.sch) into a validating XSLT
                compiler_executable = xslt_proc.compile_stylesheet(stylesheet_file=compiler_file)
                schema_file = self.schema_uri 
                validator_xslt_str = compiler_executable.transform_to_string(source_file=schema_file)
                self.schema_validator = xslt_proc.compile_stylesheet(stylesheet_text=validator_xslt_str)
        except ImportError:   # saxon not installed
            msg = f"Cannot validate because binding {self.binding} requires Saxon. Install saxonche to enable this validation."
            result.message = msg
            result.errors = [
                "Saxon is not available, cannot validate schema, becauce the schema requires a queryBinding of {self.binding}"
            ]
            self._creation_error = result
        except Exception as e:  # pylint: disable=broad-exception-caught
            # unable to create the schema object, e.g. because the schema is not well formed or not found.
            result.message = f"Unable to create the Schematron validator instance for  schema {self.schema_uri}"
            result.errors = [f"Schema Error: {e!s}"]
            self._creation_error = result

    # TODO: does it make sense to have the tree here?
    def validate(self, 
                 tree: Optional[ET.ElementTree] = None, 
                 file_path: Optional[Path] = None) -> ValidationSubResult:
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
        if tree is None and file_path is None:
            raise ValueError("Either a tree or a file_path must be given.")
        if tree is not None and file_path is not None:
            raise ValueError("Either a tree or a file_path must be given, but not both.")
        
        if file_path is not None:
            tree = ET.parse(file_path)

        if tree is not None and file_path is not None:
            raise ValueError("Either a tree or a file_path must be given, but not both.")
        # if the _creation_error is set something went wrong when creating the validator
        if self._creation_error is not None:
            result = ValidationResult(tree.docinfo.URL)
            result.add_subresult(self._creation_error)
            return result
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
            False, SchematronValidator.LXML_NAME, schema_uri=self.schema_uri
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
        except Exception as e:  # pylint: disable=broad-exception-caught
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
            False, SchematronValidator.SAXON_NAME, schema_uri=self.schema_uri
        )
        xml_file = file_path.as_posix()
        svrl_report = self.schema_validator.transform_to_string(
            source_file=str(xml_file)
        )
        #print(svrl_report)
        svrl_report_root = ET.fromstring(svrl_report.encode("utf-8"))
        errors, warnings = SchematronValidator.srvl_to_message_lists(svrl_report_root
                                                                     )
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

    def _get_schematron_binding(self, schema_location: str | Path) -> str:
        """Get the query binding of a Schematron schema.

        Use Path objects for local files, and strings for URIs.

        Return a string like 'xslt2' or None, if detecting the binding fails. 
        """
        binding = "xslt"
        try:
            if isinstance(schema_location, Path):
                # use iterparse to avoid loading the entire schema.
                for _, el in ET.iterparse(Path(schema_location), events=("start",)):
                    if el.tag == "{http://purl.oclc.org/dsdl/schematron}schema":
                        binding = el.get("queryBinding") or el.get(
                            "{http://purl.oclc.org/dsdl/schematron}queryBinding"
                        )
                        break
                    # return binding.lower() if binding else "xslt"
            elif isinstance(schema_location, str):
                # if schema_location.startswith("http"):
                schema_tree = ET.parse(schema_location)
                root = schema_tree.getroot()
                binding = root.get("queryBinding") or root.get(
                    "{http://purl.oclc.org/dsdl/schematron}queryBinding"
                )
            return binding.lower() if binding else "xslt"
        except Exception as exp:  # pylint: disable=broad-exception-caught
            # If there is an error parsing the schema, we None
            self._creation_error = ValidationSubResult(
                False,
                SchematronValidator.LXML_NAME,
                schema_uri=self.schema_uri,
                message=("Unable to create the Schematron validator instance for "
                        f"schema {self.schema_uri}"),
                errors=[f"Schema Error: {exp!s}"],
            )
            return None

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
            for txt in failed_assert.findall(".//svrl:text", ns):
                errors.append(
                    f"Error at {failed_assert.get('location', '')} ({failed_assert.get('test', '')}): {txt.text}"
                )
        for successful_report in report_root.findall("svrl:successful-report", ns):
            for txt in successful_report.find(".//svrl:text", ns):
                warnings.append(
                    f"Warning at {successful_report.get('location', '')} ({successful_report.get('test', '')}): {txt.text}"
                )
        return errors, warnings


class RelaxNGValidator(SchemaValidator):
    """A validator for RelaxNG schemas using lxml."""

    def __init__(self, schema_uri: str):
        super().__init__(schema_uri)
        # self.schema = SchemaProvider.get_relaxng(schema_uri)
        schema_tree = ET.parse(schema_uri)
        self.schema = ET.RelaxNG(schema_tree)

    def validate(self, tree: ET.ElementTree) -> ValidationSubResult:
        """Validate an XML file against the RelaxNG schema.

        Args:
            tree (ET.ElementTree): The xml tree to be validated.

        Returns:
            ValidationResult: A ValidationResult object
        """
        result = ValidationSubResult(
            False, "XML RelaxNG Validator (lxml)", schema_uri=self.schema_uri
        )

        try:
            # tree = ET.parse(file_path)
            if self.schema.validate(tree):
                result.is_valid = True
                result.message = f"Document validates against schema {self.schema_uri}"
            else:
                result.message = (
                    f"Document does not validate against schema {self.schema_uri}"
                )
                result.errors = [str(err) for err in self.schema.error_log]
        except Exception as e:  # pylint: disable=broad-exception-caught
            result.message = (
                f"Document does not validate against schema {self.schema_uri}"
            )
            result.errors = [f"RelaxNG Error: {e!s}"]
        return result


class RelaxNGCompactValidator(SchemaValidator):
    """A validator for RelaxNG compact schemas."""

    # currently we use the lxml RelaxNG validator for compact schemas as well,
    # because lxml can handle both RNG and RNC.
    # But want to keept rnc in its own class, to be more flexible
    def __init__(self, schema_uri: str):
        super().__init__(schema_uri)
        # self.schema = SchemaProvider.get_relaxng(schema_uri)
        schema_tree = ET.parse(schema_uri)
        self.schema = ET.RelaxNG(schema_tree)

    def validate(self, tree: ET.ElementTree) -> ValidationSubResult:
        """Validate an XML file against the RelaxNG Compact schema.


        Strictly speaking, this is not necessary as lxml can handle both RNG and RNC,
        but it allows us to provide more specific error messages and to distinguish between
        RNG and RNC schemas in the results.

        Args:
            tree (ET.ElementTree): The xml tree to be validated.

        Returns:
            ValidationResult: A ValidationResult object
        """
        result = ValidationSubResult(
            False, "XML RelaxNG Compact Validator (lxml)", schema_uri=self.schema_uri
        )

        try:
            # tree = ET.parse(file_path)
            if self.schema.validate(tree):
                result.is_valid = True
                result.message = f"Document validates against schema {self.schema_uri}"
            else:
                result.message = (
                    f"Document does not validate against schema {self.schema_uri}"
                )
                result.errors = [str(err) for err in self.schema.error_log]
        except Exception as e:  # pylint: disable=broad-exception-caught
            result.message = (
                f"Document does not validate against schema {self.schema_uri}"
            )
            result.errors = [f"RelaxNG Compact Error: {e!s}"]
        return result


class DTDValidator(SchemaValidator):
    """A validator for DTD schemas using lxml."""

    def __init__(self, schema_uri: str):
        super().__init__(schema_uri)
        self.schema = SchemaProvider.get_dtd(schema_uri)

    def validate(self, tree: ET.ElementTree) -> ValidationSubResult:
        """Validate an XML file against the DTD schema.

        Args:
            tree (ET.ElementTree): The xml tree to be validated.

        Returns:
            ValidationResult: A ValidationResult object
        """
        result = ValidationSubResult(
            False, "XML DTD Validator (lxml)", schema_uri=self.schema_uri
        )

        try:
            # tree = ET.parse(file_path)
            if self.schema.validate(tree):
                result.is_valid = True
                result.message = f"Document validates against schema {self.schema_uri}"
            else:
                result.message = (
                    f"Document does not validate against schema {self.schema_uri}"
                )
                result.errors = [str(err) for err in self.schema.error_log]
        except Exception as e:  # pylint: disable=broad-exception-caught
            result.message = (
                f"Document does not validate against schema {self.schema_uri}"
            )
            result.errors = [f"DTD Error: {e!s}"]
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
        elif schema_type == SchemaType.RNG:
            return SchemaProvider.get_relaxng(schema_uri)
        elif schema_type == SchemaType.RNC:
            return SchemaProvider.get_relaxng_compact(schema_uri)
        elif schema_type == SchemaType.DTD:
            return SchemaProvider.get_dtd(schema_uri)
        elif schema_type == SchemaType.SCH:
            return SchemaProvider.get_schematron(schema_uri)
        else:
            raise ValueError(f"Unknown schema type '{schema_type}'")

    # TODO: should return a SchemaValidator instance instead of the raw lxml validator, to provide a common interface for all schema types and to handle errors in a consistent way.
    @staticmethod
    @lru_cache(maxsize=MAX_CACHE_SIZE)
    def get_xsd(schema_uri: str) -> XMLSchemaValidator:
        """Return an lxml XMLSchema object.

        The schema objects are cached for performance.

        Args:
            schema_uri (str): URI to the schema file.

        Returns: XMLSchemaValidator: An XMLSchemaValidator object
        """
        return XMLSchemaValidator(schema_uri)
        # schema_doc = ET.parse(schema_uri)
        # return ET.XMLSchema(schema_doc)

    @staticmethod
    @lru_cache(maxsize=MAX_CACHE_SIZE)
    def get_schematron(schema_uri: str) -> SchematronValidator:
        """Return an lxml Schematron object.

        The schema objects are cached for performance.

        Args:
            schema_path (str): Path to the schema file.

        Returns:
            ET.Schematron: An lxml Schematron object
        """
        return SchematronValidator(schema_uri)
        # schema_doc = ET.parse(schema_uri)
        # # TODO: libxml does not support all query bindings,
        # # either restrict to some bindings or use a diffent validator (saxon?)
        # query_binding = schema_doc.getroot().get("queryBinding", "xslt1")
        # if query_binding == "xslt1":
        #     return lxml.isoschematron.Schematron(schema_doc)

        # # This is complicated, because lxml does not support xslt2.
        # # We need to set the queryBinding to xslt1 and hope that it works
        # # or we use the pyschematron packages, which neither supports xslt2,
        # # but works with the xslt2 queryBinding as long as xslt only uses
        # # XPath.
        # # Falling back to a remote validation service is also an option,
        # # but would require network access and a service to be available.
        # try:
        #     schema_doc.getroot().set("queryBinding", "xslt1")
        #     return lxml.isoschematron.Schematron(schema_doc)
        # except ValueError:
        #     schema_doc.getroot().set("queryBinding", "xslt2")
        #     return lxml.isoschematron.Schematron(schema_doc)

    @staticmethod
    @lru_cache(maxsize=MAX_CACHE_SIZE)
    def get_relaxng(schema_uri: str) -> RelaxNGValidator:
        """Return an lxml RelaxNG object.

        The schema objects are cached for performance.

        Args:
            schema_path (str): Path to the schema file.

        Returns:
            ET.RelaxNG: An lxml RelaxNG object
        """
        return RelaxNGValidator(schema_uri)
        # try:
        #    schema_doc = ET.parse(schema_path)
        #    return ET.RelaxNG(schema_doc)
        # except ET.XMLSyntaxError:
        # return ET.RelaxNG(file=schema_uri)
        # raise ValueError(f"Cannot open schema file '{schema_path}': {exp.msg}") from exp

    # TODO: maybe we need a special getter for rnc (unsure if transformation is don automatically)
    #     see https://github.com/djc/rnc2rng/issues/43#issuecomment-1776970457

    @staticmethod
    @lru_cache(maxsize=MAX_CACHE_SIZE)
    def get_relaxng_compact(schema_uri: str) -> RelaxNGCompactValidator:
        """Return a Schema Validator for RelaxNG compact."""
        return RelaxNGCompactValidator(schema_uri)

    @staticmethod
    @lru_cache(maxsize=MAX_CACHE_SIZE)
    def get_dtd(schema_uri: str) -> ET.DTD:
        """Return an lxml DTD object.

        The schema objects are cached for performance.

        Args:
            schema_path (str): Path to the schema file.

        Returns:
            ET.DTD: An lxml DTD object
        """
        # schema_doc = ET.parse(schema_path)
        # return ET.DTD(schema_path)  # ET.DTD(schema_doc)
        return DTDValidator(schema_uri)


@ValidatorFactory.register("application/rdf+xml")
@ValidatorFactory.register("application/tei+xml")
@ValidatorFactory.register("application/xml")
@ValidatorFactory.register("text/xml")
class XMLValidator(Validator):
    """Validate an XML Document against a list of schemas."""

    def __init__(self):
        super().__init__()
        # try:
        #    import saxonche  # pylint: disable=import-outside-toplevel
        #    self.saxon_available = True
        # except ImportError:
        #    self.saxon_available = False

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
                result.add_subresult(validator.validate(doc, schema_info))
            except ValueError as exp:
                result.add_subresult(
                    ValidationSubResult(
                        False,
                        "XML Schema Validator",
                        schema_uri=schema_info.schema_uri,
                        message=f"Could not create schema validator for schema '{schema_info.schema_uri}'",
                        errors=[f"ValueError: {exp!s}"],
                    )
                )
            # match schema_info.schema_type:
            #     case SchemaType.XSD:
            #         # TODO: what happens if something goes wrong with creating the schemavalidator object?
            #         validator = SchemaProvider.get_xsd(schema_info.schema_uri)
            #         #result.add_subresult(self._validate_xsd(doc, schema_info))
            #     case SchemaType.SCH:
            #         validator = SchemaProvider.get_schematron(schema_info.schema_uri)
            #         # binding = XMLValidator.get_schematron_binding(schema_info)
            #         # if binding in ["xslt2", "xslt3", "xpath2", "xpath3"]:
            #         #     result.add_subresult(
            #         #         self._validate_schematron_with_saxon(file_path, schema_info, binding)
            #         #     )
            #         # else:  # the default schematron validator os lxml
            #         #     result.add_subresult(
            #         #         self._validate_schematron_with_lxml(doc, schema_info)
            #         # )
            #         # # elif binding == "xslt1":
            #         # #     if self.saxon_available:
            #         # #         result.add_subresult(
            #         # #             self._validate_schematron_with_saxon(doc, schema_info)
            #         # #         )
            #         # #     else:
            #         # #         result.add_subresult(
            #         # #             ValidationSubResult(
            #         # #                 False,
            #         # #                 "XML Schematron Validator",
            #         # #                 schema_uri=schema_info.schema_uri,
            #         # #                 message=f"Cannot validate because binding {binding} requires Saxon. Install saxonche to enable this validation.",
            #         # #                 errors=[
            #         # #                     "Saxon is not available, cannot validate schema"
            #         # #                 ],
            #         # #             )
            #         # #         )
            #         # # else: # default to xslt1, which is supported by lxml, but may not work for all schemas
            #         # #     result.add_subresult(
            #         # #         self._validate_schematron_with_lxml(doc, schema_info)
            #         # # )
            #     case SchemaType.RNG:
            #         validator = SchemaProvider.get_relaxng(schema_info.schema_uri)
            #         #result.add_subresult(self._validate_relaxng(doc, schema_info))
            #     case SchemaType.RNC:
            #         validator = SchemaProvider.get_relaxng_compact(schema_info.schema_uri)
            #         # result.add_subresult(
            #         #     self._validate_relaxng_compact(doc, schema_info)
            #         # )
            #     case SchemaType.DTD:
            #         validator = SchemaProvider.get_dtd(schema_info.schema_uri)
            #         #result.add_subresult(self._validate_dtd(doc, schema_info))
            #     case _:
            #         result.add_subresult(
            #             ValidationSubResult(
            #                 False,
            #                 "XMLValidator",
            #                 schema_uri=schema_info.schema_uri,
            #                 message="Unknown schema type",
            #                 errors=[
            #                     f"Unknown schema format: {schema_info.schema_uri} for file {file_path}"
            #                 ],
            #             )
            #         )
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

    def _validate_schematron_with_saxon(
        self, doc_path: Path, schema_info: SchemaInfo, binding: str
    ) -> ValidationResult:
        """Validate an XML document against a Schematron schema using Saxon."""
        validator = "XML Schematron Validator with Saxon"
        try:
            from saxonche import PySaxonProcessor  # pylint: disable=import-outside-toplevel  # noqa: PLC0415

            with PySaxonProcessor(license=False) as proc:
                xslt_proc = proc.new_xslt30_processor()

                # compile Schematron zu XSLT
                # requires the ISO-schematron-stylesheets (iso_svrl_for_xslt2.xsl)
                compiler_path = "iso_schematron/iso_svrl_for_xslt2.xsl"
                compiled_schematron_xslt = xslt_proc.compile_stylesheet(
                    stylesheet_file=compiler_path
                )

                # Das Ergebnis der Transformation ist das "Validator-XSLT"
                validator_xslt_code = compiled_schematron_xslt.transform_to_string(
                    source_file=schematron_path
                )

                # 2. Schritt: Das XML mit dem generierten Validator-XSLT prüfen
                validator_stylesheet = xslt_proc.compile_stylesheet(
                    stylesheet_text=validator_xslt_code
                )
                svrl_report = validator_stylesheet.transform_to_string(
                    source_file=xml_path
                )
                print(svrl_report)
            # TODO: Aus dem SVRL-Report die Validierungsergebnisse extrahieren und in ValidationSubResult umwandeln
            return svrl_report  # Gibt den Report im SVRL-Format (XML) zurück
        except ImportError:
            msg = f"Cannot validate because binding {binding} requires Saxon. Install saxonche to enable this validation."
            return ValidationSubResult(
                False,
                validator,
                message=msg,
                errors=["Saxon is not available, cannot validate schema"],
            )

    def _validate_schematron_with_lxml(
        self, tree: ET._ElementTree, schema_info: SchemaInfo
    ) -> ValidationResult:
        """Validate an XML document against a Schematron schema using lxml.

        :param tree: the ElementTree of the XML document to validate
        :param schema_info: the SchemaInfo object containing the schema URI and type
        :return: a ValidationSubResult object containing the validation result and any errors
        """
        validator = "XML Schematron Validator (lxml)"
        try:
            schematron_validator = SchemaProvider.get_schematron(schema_info.schema_uri)

            if schematron_validator.validate(tree):
                return ValidationSubResult(
                    True,
                    validator,
                    schema_uri=schema_info.schema_uri,
                    message=f"Document validates against schema {schema_info.schema_uri}",
                )
            errors = [str(err) for err in schematron_validator.error_log]
            return ValidationSubResult(
                False,
                validator,
                message=f"Document does not validate against schema {schema_info.schema_uri}",
                errors=errors,
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            return ValidationSubResult(
                False,
                validator,
                message=f"Document does not validate against schema {schema_info.schema_uri}",
                errors=[f"Schematron Error: {e!s}"],
            )

    def _validate_relaxng(self, tree, schema_info: SchemaInfo) -> ValidationResult:
        """Validate an XML document against a RelaxNG schema."""
        validator = "XML RelaxNG Validator"
        try:
            relaxng_validator = SchemaProvider.get_relaxng(schema_info.schema_uri)

            if relaxng_validator.validate(tree):
                return ValidationSubResult(
                    True,
                    validator,
                    schema_uri=schema_info.schema_uri,
                    message=f"Document validates against schema {schema_info.schema_uri}",
                )
            errors = [str(err) for err in relaxng_validator.error_log]
            return ValidationSubResult(
                False,
                validator,
                schema_uri=schema_info.schema_uri,
                message=f"Document does not validate against schema {schema_info.schema_uri}",
                errors=errors,
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            return ValidationSubResult(
                False,
                validator,
                message=f"Document does not validate against schema {schema_info.schema_uri}",
                errors=[f"RNG Error: {e!s}"],
            )

    # TODO: Maybe we do not need to distinguish between rnc and rng
    def _validate_relaxng_compact(
        self, tree, schema_info: SchemaInfo
    ) -> ValidationResult:
        """Validate an XML document against a RelaxNG Compact schema."""
        valitator = "XML RelaxNG Compact Validator"
        try:
            relaxng_validator = SchemaProvider.get_relaxng_compact(
                schema_info.schema_uri
            )

            if relaxng_validator.validate(tree):
                return ValidationSubResult(
                    True,
                    valitator,
                    schema_uri=schema_info.schema_uri,
                    message=f"Document validates against schema {schema_info.schema_uri}",
                )
            errors = [str(err) for err in relaxng_validator.error_log]
            return ValidationSubResult(
                False,
                valitator,
                schema_uri=schema_info.schema_uri,
                message=f"Document does not validate against schema {schema_info.schema_uri}",
                errors=errors,
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            return ValidationSubResult(
                False,
                valitator,
                schema_uri=schema_info.schema_uri,
                message=f"Document does not validate against schema {schema_info.schema_uri}",
                errors=[f"RNC Error: {e!s}"],
            )

    def _validate_dtd(
        self, tree: ET._ElementTree, schema_info: SchemaInfo
    ) -> ValidationResult:
        """Validate an XML document against a DTD schema."""
        validator = "XML DTD Validator"
        try:
            dtd_validator = SchemaProvider.get_dtd(schema_info.schema_uri)
            if dtd_validator.validate(tree):
                return ValidationSubResult(
                    True,
                    validator,
                    schema_uri=schema_info.schema_uri,
                    message=f"Document validates against schema {schema_info.schema_uri}",
                )
            errors = [str(err) for err in dtd_validator.error_log]
            return ValidationSubResult(
                False,
                validator,
                schema_uri=schema_info.schema_uri,
                message=f"Document does not validate against schema {schema_info.schema_uri}",
                errors=errors,
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            return ValidationSubResult(
                False,
                validator,
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
