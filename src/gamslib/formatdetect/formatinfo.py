"""Describes the format of a file.

FormatInfo objects are returned by format detectors.
"""

from dataclasses import dataclass
from enum import StrEnum


# allowed values for subtypes
class SubType(StrEnum):
    """Enumeration of known file format subtypes."""
    # xml subtypes
    ATOM = "Atom Syndication Format"
    Collada = "Collada"  # pylint: disable=invalid-name
    DataCite = "DataCite Metadata Schema"  # pylint: disable=invalid-name
    DCMI = "Dublin Core Metadata Initiative"
    DocBook = "DocBook"  # pylint: disable=invalid-name
    EAD = "Encoded Archival Description"
    GML = "Geography Markup Language"
    KML = "Keyhole Markup Language"
    LIDO = "Lightweight Information Describing Objects Schema"
    MARC21 = "MARC 21 XML Schema"
    MathML = "Mathematical Markup Language"  # pylint: disable=invalid-name
    METS = "Metadata Encoding and Transmission Standard"
    MODS = "Metadata Object Description Schema"
    ODF = "OpenDocument Format"
    OWL = "Web Ontology Language"
    PREMIS = "Preservation Metadata Implementation Strategies"
    PresentationML = "Office Open XML PresentationML"  # pylint: disable=invalid-name
    RDF = "Resource Description Framework"
    RDFS = "RDF Schema"
    RelaxNG = "Relax NG Schema"  # pylint: disable=invalid-name
    RSS = "Really Simple Syndication"
    Schematron = "Schematron Schema"  # pylint: disable=invalid-name
    SMIL = "Synchronized Multimedia Integration Language"
    SOAP = "Simple Object Access Protocol"
    SpreadsheetML = "Office Open XML SpreadsheetML"  # pylint: disable=invalid-name
    SVG = "Scalable Vector Graphics"
    SVG_Animation = "SVG Animation (part of SMIL)"  # pylint: disable=invalid-name
    TEI = "Text Encoding Initiative"
    VoiceXML = "Voice Extensible Markup Language"  # pylint: disable=invalid-name
    WordprocessingML = "Office Open XML WordprocessingML"  # pylint: disable=invalid-name
    WSDL = "Web Services Description Language"
    X3D = "Extensible 3D"
    XBRL = "eXtensible Business Reporting Language"
    XForms = "XForms"  # pylint: disable=invalid-name
    XHTML = "Extensible Hypertext Markup Language"
    XHTML_RDFa = "XHTML+RDFa"  # pylint: disable=invalid-name
    Xlink = "XML Linking Language"  # pylint: disable=invalid-name
    XML = "Extensible Markup Language"
    XSD = "XML Schema Definition"
    XSLT = "Extensible Stylesheet Language Transformations"

    # json subtypes
    JSON = "JSON"
    JSONLD = "JSON-LD"
    JSONSCHEMA = "JSON-Schema"
    JSONL = "JSON Lines"


@dataclass
class FormatInfo:
    """Object contains basic information about the format of a file.

    FormatInfo objects are returned by format detectors.
    """

    detector: str  # name of the detector that detected the format
    mimetype: str  # eg. text/xml
    subtype: SubType | None = None
