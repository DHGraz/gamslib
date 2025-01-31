"""This module contains data and functions to detect XML types and subtypes.
"""
import warnings
from enum import StrEnum
from pathlib import Path

from lxml import etree as ET

# pylint: disable=c-extension-no-member

# These are additional MIME Types not contained in MIMETYPES (as returned
# by a detection tool are handled as XML files.)
XML_MIME_TYPES = [
    "application/xml",
    "text/xml",
]

# pylint: disable=invalid-name
class XMLTypes(StrEnum):
    """Enum for defined XML types"""

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


# Mapping of XML namspaces to XMLTypes
NAMESPACES = {
    "http://datacite.org/schema/kernel-4": XMLTypes.DataCite,
    "http://docbook.org/ns/docbook": XMLTypes.DocBook,
    "http://ead3.archivists.org/schema/": XMLTypes.EAD,
    "http://purl.oclc.org/dsdl/schematron": XMLTypes.Schematron,
    "http://purl.org/dc/elements/1.1/": XMLTypes.DCMI,
    "http://purl.org/rss/1.0/": XMLTypes.RSS,
    "http://relaxng.org/ns/structure/1.0": XMLTypes.RelaxNG,
    "http://schemas.openxmlformats.org/presentationml/2006/main": XMLTypes.PresentationML,
    "http://schemas.openxmlformats.org/spreadsheetml/2006/main": XMLTypes.SpreadsheetML,
    "http://schemas.openxmlformats.org/wordprocessingml/2006/main": XMLTypes.WordprocessingML,
    "http://schemas.xmlsoap.org/soap/envelope/": XMLTypes.SOAP,
    "http://schemas.xmlsoap.org/wsdl/": XMLTypes.WSDL,
    "http://www.collada.org/2005/11/COLLADASchema": XMLTypes.Collada,
    "http://www.lido-schema.org": XMLTypes.LIDO,
    "http://www.loc.gov/MARC21/slim": XMLTypes.MARC21,
    "http://www.loc.gov/METS/": XMLTypes.METS,
    "http://www.loc.gov/mods/v3": XMLTypes.MODS,
    "http://www.loc.gov/premis/rdf/v1#": XMLTypes.PREMIS,
    "http://www.opengis.net/gml": XMLTypes.GML,
    "http://www.opengis.net/kml/2.2": XMLTypes.KML,
    "http://www.tei-c.org/ns/1.0": XMLTypes.TEI,
    "http://www.w3.org/1998/Math/MathML": XMLTypes.MathML,
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#": XMLTypes.RDF,
    "http://www.w3.org/1999/XSL/Transform": XMLTypes.XSLT,
    "http://www.w3.org/1999/xhtml": XMLTypes.XHTML,
    "http://www.w3.org/1999/xhtml/vocab#": XMLTypes.XHTML_RDFa,
    "http://www.w3.org/1999/xlink": XMLTypes.Xlink,
    "http://www.w3.org/2000/01/rdf-schema#": XMLTypes.RDFS,
    "http://www.w3.org/2000/SMIL20/": XMLTypes.SMIL,
    "http://www.w3.org/2000/svg": XMLTypes.SVG,
    "http://www.w3.org/2001/SMIL20/Language": XMLTypes.SMIL,
    "http://www.w3.org/2001/XMLSchema": XMLTypes.XSD,
    "http://www.w3.org/2001/vxml": XMLTypes.VoiceXML,
    "http://www.w3.org/2002/07/owl#": XMLTypes.OWL,
    "http://www.w3.org/2002/xforms": XMLTypes.XForms,
    "http://www.w3.org/2005/Atom": XMLTypes.ATOM,
    "http://www.w3.org/XML/1998/namespace": XMLTypes.XML,
    "http://www.web3d.org/specifications/x3d-namespace": XMLTypes.X3D,
    "urn:oasis:names:tc:opendocument:xmlns:office:1.0": XMLTypes.ODF,
}


MIMETYPES = {
    XMLTypes.DataCite: "application/datacite+xml",
    XMLTypes.DocBook: "application/docbook+xml",
    XMLTypes.EAD: "application/ead+xml",
    XMLTypes.Schematron: "application/schematron+xml",
    # XMLTypes.DCMI: "application/dcmitype+xml",
    XMLTypes.RSS: "application/rss+xml",
    XMLTypes.RelaxNG: "application/relax-ng+xml",
    XMLTypes.PresentationML: "application/vnd.openxmlformats-officedocument.presentationml",
    XMLTypes.SpreadsheetML: "application/vnd.openxmlformats-officedocument.spreadsheetml",
    XMLTypes.WordprocessingML:
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    XMLTypes.SOAP: "application/soap+xml",
    XMLTypes.WSDL: "application/wsdl+xml",
    XMLTypes.Collada: "application/vnd.collada+xml",
    XMLTypes.LIDO: "application/xml",
    XMLTypes.MARC21: "application/marcxml+xml",
    XMLTypes.METS: "application/mets+xml",
    XMLTypes.MODS: "application/mods+xml",
    XMLTypes.PREMIS: "application/rdf+xml",
    XMLTypes.GML: "application/gml+xml",
    XMLTypes.KML: "application/vnd.google-earth.kml+xml",
    XMLTypes.TEI: "application/tei+xml",
    XMLTypes.MathML: "application/mathml+xml",
    XMLTypes.RDF: "application/rdf+xml",
    XMLTypes.XSLT: "application/xslt+xml",
    XMLTypes.XHTML: "application/xhtml+xml",
    XMLTypes.XHTML_RDFa: "application/xhtml+xml",
    XMLTypes.Xlink: "application/xlink+xml",
    XMLTypes.RDFS: "application/rdf+xml",
    XMLTypes.SMIL: "application/smil+xml",
    XMLTypes.SVG: "image/svg+xml",
    XMLTypes.SVG_Animation: "application/smil+xml",
    XMLTypes.XSD: "application/xml",
    XMLTypes.VoiceXML: "application/voicexml+xml",
    XMLTypes.OWL: "application/owl+xml",
    XMLTypes.XForms: "application/xforms+xml",
    XMLTypes.ATOM: "application/atom+xml",
    XMLTypes.XML: "application/xml",
    XMLTypes.X3D: "model/x3d+xml",
    XMLTypes.ODF: "application/vnd.oasis.opendocument.text",
}


def is_xml_type(mimetype: str) -> bool:
    "Return True if mimetype is a known XML type."
    return mimetype in MIMETYPES.values() or mimetype in XML_MIME_TYPES


def guess_xml_subtype(filepath: Path) -> str:
    """This is a custom way to find out what kind of xml we are dealing with.

    This tool uses a registry of namespaces to find out what kind of xml
    we are dealing with. If the file has a namespace that is not in the registry,
    the function will raise a Warning and return None.

    Tools like FITS are capable of detecting subtypes (at least some of them)
    so this function might be especially useful for simpler detectors or
    exotic formats.
    """
    for _, elem in ET.iterparse(filepath, events=["start-ns"]):
        # the second item of the tuple is the qualified namespace
        namespace = elem[1]
        try:
            return NAMESPACES[namespace]
        except KeyError:
            warnings.warn(
                f"xml format detection failed because of unknown namespace: {namespace}"
            )
    return None


def get_format_info(filepath: Path, mime_type: str) -> tuple[str, str]:
    """Get the format info for an XML file.

    Args:
        filepath: The path to the file.
        mimetype: The mimetype of the file as detected by another tool.

    Returns:
        A tuple containing the (probably fixed) mimetype and subtype of the file.
    """
    xmltype = guess_xml_subtype(filepath)
    if xmltype is None:  # cannot detect a subtype
        subtype = ""
    #        format_info = FormatInfo(mimetype=mime_type, subtype="")
    else:
        subtype = xmltype.name
        mime_type = MIMETYPES.get(xmltype, mime_type)
    return mime_type, subtype
