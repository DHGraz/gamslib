"""Utility functions for the objectcsv module.

Provides helpers for finding object folders, extracting titles from TEI and LIDO files,
and splitting CSV entries into lists.
"""

import logging
from pathlib import Path
import xml.etree.ElementTree as ET


from .defaultvalues import NAMESPACES

logger = logging.getLogger()


def split_entry(entry: str) -> list[str]:
    """
    Split a string of CSV entries into a list using semicolon as delimiter.

    Args:
        entry (str): String containing CSV entries separated by semicolons.

    Returns:
        list[str]: List of trimmed entries. Returns an empty list if entry is empty.

    Notes:
        - Leading and trailing whitespace is removed from each entry.
        - Only non-empty entries are included in the result.
    """
    values = entry.split(";") if entry else []
    return [value.strip() for value in values if value.strip()]


def extract_title_from_tei(tei_file: Path | str) -> str:
    """
    Extract the title from a TEI file.

    Args:
        tei_file (Path or str): Path to the TEI XML file.

    Returns:
        str: Title extracted from the TEI file, or an empty string if not found.
    """
    tei = ET.parse(tei_file)
    title_node = tei.find(
        "tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:title", namespaces=NAMESPACES
    )
    return title_node.text if title_node is not None else ""


def extract_title_from_lido(lido_file: Path | str) -> str:
    """
    Extract the title from a LIDO file.

    Args:
        lido_file (Path or str): Path to the LIDO XML file.

    Returns:
        str: Title extracted from the LIDO file, or an empty string if not found.
    """
    lido = ET.parse(lido_file)
    # pylint: disable=line-too-long
    title_node = lido.find(
        "lido:descriptiveMetadata/lido:objectIdentificationWrap/lido:titleWrap/lido:titleSet/lido:appellationValue",
        namespaces=NAMESPACES,
    )
    return title_node.text if title_node is not None else ""


def find_object_root(start_path: Path) -> Path:
    """
    Find the root folder of an object by looking a DC.XML file in the current and parent directories.

    Args:
        start_path (Path): The path to start searching from.

    Returns:
        Path: The root folder of the object.
    Raises:
        FileNotFoundError: If no DC.XML file is found in the current or parent directories
    """
    current_path = start_path
    while True:
        if (current_path / "DC.XML").is_file():
            return current_path
        if current_path.parent == current_path:
            raise FileNotFoundError(
                f"No DC.XML file found in {start_path} or any parent directory."
            )
        current_path = current_path.parent


def distinctify(values: str) -> str:
    """Remove duplicate values from a semicolon-separated string."""
    # we want to keep the order, so no set
    clean_values = []
    for val in split_entry(values):
        if val not in clean_values:
            clean_values.append(val)
    return "; ".join(clean_values)


