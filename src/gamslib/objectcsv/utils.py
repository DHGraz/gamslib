"""Utility functions for the objectcsv module."""

import logging
import warnings
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Generator

from .defaultvalues import NAMESPACES

logger = logging.getLogger()


def find_object_folders(root_directory: Path) -> Generator[Path, None, None]:
    """Find all object folders below root_directory."""
    for directory in root_directory.rglob("*"):
        if directory.is_dir():
            if "DC.xml" in [f.name for f in directory.iterdir()]:
                yield directory
            else:
                warnings.warn(
                    f"Skipping '{directory}' as folder does not contain a DC.xml file.",
                    UserWarning,
                )


def extract_title_from_tei(tei_file):
    "Extract the title from a TEI file."
    tei = ET.parse(tei_file)
    title_node = tei.find(
        "tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:title", namespaces=NAMESPACES
    )
    return title_node.text if title_node is not None else ""


def extract_title_from_lido(lido_file):
    "Extract the title from a LIDO file."
    lido = ET.parse(lido_file)
    # pylint: disable=line-too-long
    title_node = lido.find(
        "lido:descriptiveMetadata/lido:objectIdentificationWrap/lido:titleWrap/lido:titleSet/lido:appellationValue",
        namespaces=NAMESPACES,
    )
    return title_node.text if title_node is not None else ""


def split_entry(entry: str) -> list[str]:
    """Split a string of csv entries into a list.

    The only supported delimiter is a semicolon (;).
    If the entry is empty, an empty list is returned.
    Leading and trailing whitespace is removed from each entry.
    """
    values = entry.split(";") if entry else []
    return [value.strip() for value in values if value.strip()]
