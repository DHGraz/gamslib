"""Module for object directory management and validation in GAMS library."""

import logging
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Generator

from gamslib import formatdetect
from gamslib.formatdetect import formatinfo
from gamslib.objectcsv.defaultvalues import NAMESPACES
from gamslib.objectcsv.dublincore import DublinCore
from gamslib.objectcsv.objectcsvmanager import InvalidCSVFileError, ObjectCSVManager

logger = logging.getLogger(__name__)


class ObjectDirectoryValidationError(Exception):
    """Exception raised when an object directory is invalid."""


def is_object_folder(folder_path: Path) -> bool:
    """
    Check if the given folder is an object folder.

    An object folder is defined as a folder that contains a DC.xml file.

    Args:
        folder_path (Path): Path to the folder to check.

    Returns:
        bool: True if the folder is an object folder, False otherwise.
    """
    return (folder_path / "DC.xml").is_file()


def find_object_folders(root_folder: Path) -> Generator[Path, None, None]:
    """
    Find all object folders in the root folder or below.

    Args:
        root_folder (Path): Root directory to search for object folders.

    Yields:
        Path: Path to each object folder containing a DC.xml file.

    Notes:
        - Skips folders that do not contain a DC.xml file and logs a warning.
    """
    # Path.walk() only was introduced in Python 3.12, so we use os.walk() here
    for root, _, _ in os.walk(root_folder):
        path = Path(root)
        if is_object_folder(path):
            yield path
        else:
            logger.debug(
                "Skipping folder %s as it does not contain a DC.xml file.", root
            )


def validate_directory_structure(object_path: Path) -> None:
    """
    Validate the structure of the object directory.

    Structure is valid if it contains at least these files:
      * DC.xml
      * object.csv
      * datastreams.csv
      * all files referenced in datastreams.csv


    Args:
        object_path (Path): Path to the object directory.

    Raises:
        ObjectDirectoryValidationError: If the directory structure is invalid.
    """
    if not object_path.is_dir():
        raise ObjectDirectoryValidationError(
            f"Object directory '{object_path.name}' does not exist or is not a directory."
        )

    if not (object_path / "DC.xml").exists():
        raise ObjectDirectoryValidationError(
            f"Object directory '{object_path.name}' does not contain a DC.xml file."
        )

    # Check the object.csv file
    if not (object_path / "object.csv").is_file():
        raise ObjectDirectoryValidationError(
            f"Object directory '{object_path.name}' does not contain an object.csv file."
        )
    if not (object_path / "datastreams.csv").is_file():
        raise ObjectDirectoryValidationError(
            f"Object directory '{object_path.name}' does not contain a datastreams.csv file."
        )


def _extract_id_from_tei(tei_file: Path | str) -> str | None:
    """
    Extract the identifier from a TEI file.

    Args:
        tei_file (Path or str): Path to the TEI XML file.

    Returns:
        str: Identifier extracted from the TEI file, or None if not found.
    """
    tei = ET.parse(tei_file)
    # This is very specific to GAMS(3) TEI but as we only use this to compare IDs,
    # getting None is fine if there is no PID
    id_node = tei.find(
        'tei:teiHeader[1]/tei:fileDesc[1]/tei:publicationStmt[1]/tei:idno[@type="PID"]',
        namespaces=NAMESPACES,
    )
    return id_node.text if id_node is not None else None


def _extract_id_from_lido(lido_file: Path | str) -> str | None:
    """
    Extract the identifier from a LIDO file.

    Args:
        lido_file (Path or str): Path to the LIDO XML file.
    Returns:
        str: Identifier extracted from the LIDO file, or None if not found.
    """
    lido = ET.parse(lido_file)
    # This is very specific to GAMS(3) LIDO but as we only use this to compare IDs,
    # getting None is fine if there is no PID
    id_node = lido.find(
        'lido:lidoRecID[@lido:type="PID"]',
        namespaces=NAMESPACES,
    )
    return id_node.text if id_node is not None else None


def validate_main_resource_id(object_dir: Path):
    """Validate if the main resource file has the same ID as the object directory

    Raise a ObjectDirectoryValidationError if the main resource is a TEI or LIDO file and
    the ID in this file does not have the same ID as the object directory.

    In all other cases, this function does not raise an error.

    Args:
        object_dir (Path): Path to the object directory.
    Raises:
        ObjectDirectoryValidationError: If the main resource file has the same ID as
        the object directory
    """
    csv_mgr = ObjectCSVManager(object_dir)
    main_resource = csv_mgr.get_mainresource()
    if main_resource is not None:
        object_id = None
        main_resource_path = object_dir / Path(main_resource.dspath).name
        main_format = formatdetect.detect_format(main_resource_path)
        if main_format.subtype == formatinfo.SubType.TEI:
            object_id = _extract_id_from_tei(main_resource_path)
        elif main_format.subtype == formatinfo.SubType.LIDO:
            object_id = _extract_id_from_lido(main_resource_path)
        dir_id = object_dir.name.replace("%3A", ":")
        if object_id is not None and dir_id != object_id:
            raise ValueError(
                f"Object directory name '{object_dir.name}' does not match "
                f"the object ID '{object_id}' extracted from the main resource "
                f"file '{main_resource_path.name}'."
            )


def _create_csvmgr_with_error_handling(object_path: Path) -> None:
    """
    Create an ObjectCSVManager with readable error messages.

    Use this function to catch TypeErrors raised during construction of
    ObjectCSVManager due to missing required or unexpected fields in the
    CSV files.

    The function returns a ObjectCSVManager instance if construction was successful,
    or raises an ObjectDirectoryValidationError with a descriptive message otherwise.

    Args:
        object_path (Path): Path to the object directory.

    Raises:
        ObjectDirectoryValidationError: With a descriptive message about the missing field.
    """
    try:
        return ObjectCSVManager(object_path)
    except TypeError as e:
        # if a csv file is missing required fields, dataclass raise a TypeError
        # "ObjectData.__init__() got an unexpected keyword argument 'id'"
        match = re.match(r"(.*)\.__init__\(\)(.*) '(.*)'$", str(e))
        if match:
            missing_field = match.group(3)
            csv_file = (
                "object.csv" if match.group(1) == "ObjectData" else "datastreams.csv"
            )
            if "unexpected" in match.group(2):
                raise ObjectDirectoryValidationError(
                    f"Object directory '{object_path.name}': {csv_file} contains an unexpected "
                    f"field '{missing_field}'."
                ) from e
            if "missing" in match.group(2):
                raise ObjectDirectoryValidationError(
                    f"Object directory '{object_path.name}': {csv_file} is missing a required "
                    f"field '{missing_field}'."
                ) from e
        # fallback for unexpected error messages
        raise ObjectDirectoryValidationError(
            f"Object directory '{object_path.name}': {e}"
        ) from e
    except InvalidCSVFileError as e:
        raise ObjectDirectoryValidationError(
            f"Object directory '{object_path.name}': {e}"
        ) from e    


def validate_csv_files(object_path: Path) -> None:
    """
    Validate the CSV files in the object directory.

    Args:
        object_path (Path): Path to the object directory.

    Raises:
        ObjectDirectoryValidationError: If any CSV file is invalid.
    """
    # use the ObjectCSVFile class to validate contents of the object.csv file
    csv_mgr = _create_csvmgr_with_error_handling(object_path)
    try:
        csv_mgr.validate()
        # check if recid matches directory name
        if csv_mgr.object_id != csv_mgr.get_object().recid:
            raise ObjectDirectoryValidationError(
                f"Object directory '{object_path.name}': Directory name '{csv_mgr.object_id}' "
                f"does not match recid '{csv_mgr.get_object().recid}' in object.csv."
            )
        # check if all datastream files exist
        for dsdata in csv_mgr.get_datastreamdata():
            ds_file_path = object_path / dsdata.dsid
            if not ds_file_path.is_file():
                raise ObjectDirectoryValidationError(
                    f"Object directory '{object_path.name}': Datastream file "
                    f"'{dsdata.dspath.split('/')[-1]}' "
                    f"referenced in datastreams.csv does not exist."
                )
    except ValueError as e:
        raise ObjectDirectoryValidationError(
            f"Object directory '{object_path.name}': {e}"
        ) from e


def validate_dc_file(object_path: Path) -> None:
    """
    Validate the DC.xml file in the object directory.

    Args:
        object_path (Path): Path to the object directory.

    Raises:
        ObjectDirectoryValidationError: If the DC.xml file is invalid.
    """
    dc_file = object_path / "DC.xml"
    try:
        dc = DublinCore(dc_file)
        dc.validate()
        identifiers = dc.get_element_all_langs("identifier")
        if object_path.name.replace("%3A", ":") not in identifiers:
            raise ObjectDirectoryValidationError(
                f"Object directory '{object_path.name}': DC.xml identifier value does not match "
                f"the object directory name."
            )
    except ValueError as e:
        raise ObjectDirectoryValidationError(
            f"Object directory '{object_path.name}': DC.xml file is invalid: {e}"
        ) from e


def validate_object_dir(object_path: Path) -> None:
    """
    Check if everything needed is present in the object directory.

    Args:
        object_path (Path): Path to the object directory.

    Raises:
        ObjectDirectoryValidationError: If the directory or required files are missing,
            or if object.csv is invalid.
    """
    validate_directory_structure(object_path)
    validate_dc_file(object_path)
    validate_csv_files(object_path)
    validate_main_resource_id(object_path)
