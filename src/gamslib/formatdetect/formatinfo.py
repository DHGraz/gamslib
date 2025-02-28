"""Describes the format of a file.

FormatInfo objects are returned by format detectors.
"""

from dataclasses import dataclass
from enum import StrEnum

# allowed values for subtypes
class SubType(StrEnum):
    # xml subtypes
    ATOM = "Atom Syndication Format"
    Collada = "Collada"
    DataCite = "DataCite Metadata Schema"
    DCMI = "Dublin Core Metadata Initiative"
    DocBook = "DocBook"
    EAD = "Encoded Archival Description"
    GML = "Geography Markup Language"
    KML = "Keyhole Markup Language"
    LIDO = "Lightweight Information Describing Objects Schema"
    MARC21 = "MARC 21 XML Schema"
    MathML = "Mathematical Markup Language"
    METS = "Metadata Encoding and Transmission Standard"
    MODS = "Metadata Object Description Schema"
    ODF = "OpenDocument Format"
    OWL = "Web Ontology Language"
    PREMIS = "Preservation Metadata Implementation Strategies"
    PresentationML = "Office Open XML PresentationML"
    RDF = "Resource Description Framework"
    RDFS = "RDF Schema"
    RelaxNG = "Relax NG Schema"
    RSS = "Really Simple Syndication"
    Schematron = "Schematron Schema"
    SMIL = "Synchronized Multimedia Integration Language"
    SOAP = "Simple Object Access Protocol"
    SpreadsheetML = "Office Open XML SpreadsheetML"
    SVG = "Scalable Vector Graphics"
    SVG_Animation = "SVG Animation (part of SMIL)"
    TEI = "Text Encoding Initiative"
    VoiceXML = "Voice Extensible Markup Language"
    WordprocessingML = "Office Open XML WordprocessingML"
    WSDL = "Web Services Description Language"
    X3D = "Extensible 3D"
    XBRL = "eXtensible Business Reporting Language"
    XForms = "XForms"
    XHTML = "Extensible Hypertext Markup Language"
    XHTML_RDFa = "XHTML+RDFa"
    Xlink = "XML Linking Language"
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
