"""Default values for the datastream meatadata."""

import xml.etree.ElementTree as ET
NAMESPACES = {
    "tei": "http://www.tei-c.org/ns/1.0",
    "lido": "http://www.lido-schema.org",
}

DEFAULT_CREATOR = "Unknown"
DEFAULT_MIMETYPE = "application/octet-stream"
DEFAULT_OBJECT_TYPE = "text"
DEFAULT_RIGHTS = ("Creative Commons Attribution-NonCommercial 4.0 "
                  "(https://creativecommons.org/licenses/by-nc/4.0/)")
DEFAULT_SOURCE = "local"

# This is a mapping of filenames to default metadata values.
# Add new entries here if you want to add new metadata fields.
FILENAME_MAP = {
    "DC.xml": {
        "title": "Dublin Core Metadata",
        "description": "Dublin Core Metadata in XML format for this content file.",
    },
    # Elisabeth says, this makes no sense; better extract from TEI/LIDO
    #"TEI.xml": {
    #    "title": "Main TEI file",
    #    "description": "The central TEI File for this object",
    #},
    #"LIDO.xml": {
    #    "title": "Main LIDO file",
    #    "description": "The central LIDO file of this object",
    #},
    "RDF.xml": {"title": "RDF Statements", "description": ""},
}


def extract_title_from_tei(tei_file):
    tei = ET.parse(tei_file)
    title_node = tei.find('tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:title', namespaces=NAMESPACES)
    return title_node.text if title_node is not None else ""


def extract_title_from_lido(lido_file):
    "Extract the title from a LIDO file."
    lido = ET.parse(lido_file)
    title_node = lido.find('lido:descriptiveMetadata/lido:objectIdentificationWrap/lido:titleWrap/lido:titleSet/lido:appellationValue', namespaces=NAMESPACES)
    return title_node.text if title_node is not None else ""