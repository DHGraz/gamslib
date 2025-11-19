"""Utility functions for the objectcsv module.

Provides helpers for finding object folders, extracting titles from TEI and LIDO files,
and splitting CSV entries into lists.
"""

import logging
import warnings
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Generator

from gamslib import formatdetect
from gamslib.formatdetect import formatinfo

from .defaultvalues import NAMESPACES

logger = logging.getLogger()


def find_object_folders(root_directory: Path) -> Generator[Path, None, None]:
    """
    Find all object folders below root_directory that contain a DC.xml file.

    Args:
        root_directory (Path): Root directory to search for object folders.

    Yields:
        Path: Path to each object folder containing a DC.xml file.

    Notes:
        - Skips directories that do not contain a DC.xml file and issues a warning.
    """
    for directory in root_directory.rglob("*"):
        if directory.is_dir():
            if "DC.xml" in [f.name for f in directory.iterdir()]:
                yield directory
            else:
                warnings.warn(
                    f"Skipping '{directory}' as folder does not contain a DC.xml file.",
                    UserWarning,
                )


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


def extract_id_from_tei(tei_file: Path | str) -> str:
    """
    Extract the identifier from a TEI file.

    Args:
        tei_file (Path or str): Path to the TEI XML file.

    Returns:
        str: Identifier extracted from the TEI file, or an empty string if not found.
    """
    tei = ET.parse(tei_file)
    id_node = tei.find(
        "tei:teiHeader[1]/tei:fileDesc[1]/tei:publicationStmt[1]/tei:idno[1]",
        namespaces=NAMESPACES,
    )
    return id_node.text if id_node is not None else ""


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


def extract_id_from_lido(lido_file: Path | str) -> str:
    """
    Extract the identifier from a LIDO file.

    Args:
        lido_file (Path or str): Path to the LIDO XML file.
    Returns:
        str: Identifier extracted from the LIDO file, or an empty string if not found.
    """
    lido = ET.parse(lido_file)
    id_node = lido.find(
        "lido:lidoRecID[1]",
        # "lido:descriptiveMetadata/lido:objectIdentificationWrap/lido:repositoryWrap/lido:repositorySet/lido:repositoryID",
        namespaces=NAMESPACES,
    )
    return id_node.text if id_node is not None else ""


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


def check_if_object_dir_matches_object_id(
    object_dir: Path, main_resource: Path | None = None
) -> None:
    """
    Check if the object directory name matches the given object identifier.

    Currently this only checks TEI and LIDO files if they are set as main resource.

    Raises:
        ValueError: If the object directory name does not match the object identifier.

    Args:
        object_dir (Path): Path to the object directory.
        object_id (str): Object identifier to compare against.

    Returns:
        None
    """
    # If we do not have a main resource, there is nothing to check
    object_id = None
    if main_resource is not None:
        main_format = formatdetect.detect_format(main_resource)
        if main_format.subtype == formatinfo.SubType.TEI:
            object_id = extract_id_from_tei(main_resource)
        elif main_format.subtype == formatinfo.SubType.LIDO:
            object_id = extract_id_from_lido(main_resource)
        dir_id = object_dir.name.replace("%3A", ":")
        if object_id is not None and dir_id != object_id:
            raise ValueError(
                f"Object directory name '{object_dir.name}' does not match "
                f"the object ID '{object_id}' extracted from the main resource "
                f"file '{main_resource.name}'."
            )
