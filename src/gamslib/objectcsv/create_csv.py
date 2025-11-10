"""Create object.csv and datastreams.csv files for GAMS objects.

This module generates `object.csv` and `datastreams.csv` files for one or more object folders.
It uses data from the DC.xml file and the project configuration to populate metadata fields.
If information is missing, fields are left blank or filled with default values.
"""

import fnmatch
import logging
import mimetypes
import re
import warnings
from pathlib import Path

from gamslib import formatdetect
from gamslib.formatdetect.formatinfo import FormatInfo
from gamslib.projectconfiguration import Configuration

from . import defaultvalues
from .dsdata import DSData
from .dublincore import DublinCore
from .objectcsvmanager import ObjectCSVManager, OBJ_CSV_FILENAME, DS_CSV_FILENAME

from .objectdata import ObjectData
from .utils import find_object_folders

logger = logging.getLogger()


NAMESPACES = {
    "dc": "http://purl.org/dc/elements/1.1/",
}


def is_datastream_file(ds_file: Path, configuration: Configuration) -> bool:
    """
    Determine if a file should be treated as a datastream file.

    Excludes files named 'object.csv' or 'datastreams.csv', and files matching ignore patterns
    specified in the configuration.

    Args:
        ds_file (Path): Path to the candidate datastream file.
        configuration (Configuration): Project configuration containing ignore patterns.

    Returns:
        bool: True if the file should be used as a datastream, False otherwise.
    """
    if not ds_file.is_file():
        return False
    if ds_file.name in (
        OBJ_CSV_FILENAME,
        DS_CSV_FILENAME,
        ".DS_Store",
        "Thumbs.db",
    ):
        return False
    for pattern in configuration.general.ds_ignore_files:
        if fnmatch.fnmatch(ds_file.name, pattern):
            logger.debug(
                "Ignoring datastream file '%s' due to ignore pattern '%s'.",
                ds_file.name,
                pattern,
            )
            return False
    return True


def get_rights(config: Configuration, dc: DublinCore) -> str:
    """
    Retrieve the rights information for an object or datastream.

    Lookup order:

      1. Value from Dublin Core metadata (DC.xml).
      2. Value from project configuration.
      3. Default value if none found.

    Args:

      - config (Configuration): Project configuration.
      - dc (DublinCore): Dublin Core metadata object.

    Returns:
        str: Rights value.
    """
    rights = dc.get_element_as_str("rights", preferred_lang="en", default="")
    if not rights:  # empty string is a valid value
        rights = config.metadata.rights or defaultvalues.DEFAULT_RIGHTS
    return rights


def extract_dsid(datastream: Path | str, keep_extension=True) -> str:
    """
    Extract and validate the datastream ID from a file path.

    If keep_extension is False, attempts to remove the file extension from the ID.
    Validates the resulting ID format.

    Args:
        datastream (Path | str): Path or filename of the datastream.
        keep_extension (bool): Whether to keep the file extension in the ID.

    Returns:
        str: The extracted datastream ID.

    Raises:
        ValueError: If the resulting ID is invalid.
    """
    if isinstance(datastream, str):
        datastream = Path(datastream)

    pid = datastream.name

    if not keep_extension:
        # not everything after the last dot is an extension :-(
        mtype = mimetypes.guess_type(datastream)[0]
        if mtype is None:
            known_extensions = []
        else:
            known_extensions = mimetypes.guess_all_extensions(mtype)
        if datastream.suffix in known_extensions:
            pid = pid.removesuffix(datastream.suffix)
            logger.debug("Removed extension '%s' for ID: %s", datastream.suffix, pid)
        else:
            parts = pid.split(".")
            if re.match(r"^[a-zA-Z]+\w?$", parts[-1]):
                pid = ".".join(parts[:-1])
                logger.debug("Removed extension for ID: %s", parts[0])
            else:
                warnings.warn(
                    f"'{parts[-1]}' does not look like an extension. Keeping it in PID.",
                    UserWarning,
                )

    if re.match(r"^[a-zA-Z0-9]+[-.%_a-zA-Z0-9]+[a-zA-Z0-9]+$", pid) is None:
        raise ValueError(f"Invalid PID: '{pid}'")

    logger.debug(
        "Extracted PID: %s from %s (keep_extension=%s)", pid, datastream, keep_extension
    )
    return pid


def detect_languages(ds_file: Path, delimiter: str = " ") -> str:
    """
    Detect the language(s) of a file.

    Returns detected language(s) as a string separated by the given delimiter.
    (Currently returns an empty string; language detection is not implemented.)

    Args:
        ds_file (Path): Path to the file.
        delimiter (str): Delimiter for joining detected languages.

    Returns:
        str: Detected languages, or empty string if none.
    """
    languages = []
    # we decided not to use language detection for now
    return delimiter.join(languages) if languages else ""


def collect_object_data(pid: str, config: Configuration, dc: DublinCore) -> ObjectData:
    """
    Collect metadata for an object to populate object.csv.

    Resolves values from Dublin Core metadata and project configuration.

    Args:
        pid (str): Object identifier.
        config (Configuration): Project configuration.
        dc (DublinCore): Dublin Core metadata object.

    Returns:
        ObjectData: Populated object metadata.
    """
    title = "; ".join(dc.get_en_element("title", default=pid))
    # description = "; ".join(dc.get_element("description", default=""))

    return ObjectData(
        recid=pid,
        title=title,
        project=config.metadata.project_id,
        description="",
        creator=config.metadata.creator,
        rights=get_rights(config, dc),
        source=defaultvalues.DEFAULT_SOURCE,
        objectType=defaultvalues.DEFAULT_OBJECT_TYPE,
        publisher=config.metadata.publisher,
        funder=config.metadata.funder,
    )


def make_ds_title(dsid: str, format_info: FormatInfo) -> str:
    """
    Generate a title for a datastream based on its ID and format.

    Args:
        dsid (str): Datastream ID.
        format_info (FormatInfo): Format information for the datastream.

    Returns:
        str: Generated datastream title.
    """
    return f"{format_info.description}: {dsid}"


def make_ds_description(dsid: str, format_info: FormatInfo) -> str:
    """
    Generate a description for a datastream based on its ID and format.

    Uses the format subtype as the description if available.

    Args:
        dsid (str): Datastream ID.
        format_info (FormatInfo): Format information for the datastream.

    Returns:
        str: Datastream description, or empty string if not available.
    """
    # We have agreed to set the format subtype as description if available.
    # Not happy with this, but we need the subtype in csv data.
    # I'd prefer an extra field for the subtype, but this was rejected
    # by the team.
    if format_info.subtype:
        return format_info.subtype.name
    return ""


def collect_datastream_data(
    ds_file: Path, config: Configuration, dc: DublinCore
) -> DSData:
    """
    Collect metadata for a single datastream to populate datastreams.csv.

    Uses file information, format detection, and configuration values.

    Args:
        ds_file (Path): Path to the datastream file.
        config (Configuration): Project configuration.
        dc (DublinCore): Dublin Core metadata object.

    Returns:
        DSData: Populated datastream metadata.
    """
    dsid = extract_dsid(ds_file, config.general.dsid_keep_extension)

    # I think it's not possible to derive a ds title or description from the DC file
    # title = "; ".join(dc.get_element("title", default=dsid)) # ??
    # description = "; ".join(dc.get_element("description", default="")) #??

    format_info: FormatInfo = formatdetect.detect_format(ds_file)

    return DSData(
        dspath=str(ds_file.relative_to(ds_file.parents[1])),  # objectsdir
        dsid=dsid,
        title=make_ds_title(dsid, format_info),
        description=make_ds_description(dsid, format_info),
        mimetype=mimetypes.guess_type(ds_file)[0] or "",
        creator=config.metadata.creator,
        rights=get_rights(config, dc),
        lang=detect_languages(ds_file, delimiter=";"),
        tags="",
    )


def create_csv(
    object_directory: Path, configuration: Configuration, force_overwrite: bool = False
) -> ObjectCSVManager | None:
    """
    Generate object.csv and datastreams.csv for a single object directory.

    Existing CSV files are not overwritten unless 'force_overwrite' is True.
    Metadata is collected from DC.xml and configuration.

    Args:
        object_directory (Path): Path to the object directory.
        configuration (Configuration): Project configuration.
        force_overwrite (bool): Whether to overwrite existing CSV files.

    Returns:
        ObjectCSVManager | None: Manager for the created CSV files, or None if not created.
    """
    if not object_directory.is_dir():
        logger.warning("Object directory '%s' does not exist.", object_directory)
        return None

    objectcsv = ObjectCSVManager(object_directory)

    # Avoid that existing (and potentially already edited) metadata is replaced
    if force_overwrite and not objectcsv.is_empty():
        objectcsv.clear()
    if not objectcsv.is_empty():
        logger.info(
            "CSV files for object '%s' already exist. Will not be re-created.",
            objectcsv.object_id,
        )
        return None

    dc = DublinCore(object_directory / "DC.xml")
    obj = collect_object_data(objectcsv.object_id, configuration, dc)
    objectcsv.set_object(obj)
    for ds_file in object_directory.glob("*"):
        if is_datastream_file(ds_file, configuration):
            objectcsv.add_datastream(
                collect_datastream_data(ds_file, configuration, dc)
            )
    objectcsv.guess_mainresource()
    objectcsv.validate()
    objectcsv.save()
    return objectcsv


def update_csv(
    object_directory: Path, configuration: Configuration
) -> ObjectCSVManager | None:
    """
    Update existing CSV files for an object directory with new metadata.

    Adds new datastreams and updates metadata if configuration or DC.xml has changed.
    Existing CSV files are updated, not overwritten.

    Args:
        object_directory (Path): Path to the object directory.
        configuration (Configuration): Project configuration.

    Returns:
        ObjectCSVManager | None: Manager for the updated CSV files, or None if not updated.
    """
    if not object_directory.is_dir():
        logger.warning("Object directory '%s' does not exist.", object_directory)
        return None

    objectcsv = ObjectCSVManager(object_directory, ignore_existing_csv_files=True)

    if objectcsv.is_empty():
        logger.warning(
            "Object directory '%s' has no existing CSV files. Will be created.",
            object_directory,
        )
    dc = DublinCore(object_directory / "DC.xml")

    objectcsv.merge_object(collect_object_data(objectcsv.object_id, configuration, dc))
    for ds_file in object_directory.glob("*"):
        if is_datastream_file(ds_file, configuration):
            dsdata = collect_datastream_data(ds_file, configuration, dc)
            objectcsv.merge_datastream(
                collect_datastream_data(ds_file, configuration, dc)
            )

    objectcsv.guess_mainresource()
    objectcsv.save()
    return objectcsv


def create_csv_files(
    root_folder: Path,
    config: Configuration,
    force_overwrite: bool = False,
    update: bool = False,
) -> list[ObjectCSVManager]:
    """
    Create or update CSV files for all objects under the given root folder.

    Iterates through all object directories found below root_folder and creates or updates
    their object.csv and datastreams.csv files.

    Args:
        root_folder (Path): Root directory containing object folders.
        config (Configuration): Project configuration.
        force_overwrite (bool): If True, overwrite existing CSV files.
        update (bool): If True, update existing CSV files instead of creating new ones.

    Returns:
        list[ObjectCSVManager]: List of managers for the processed object directories.
    """
    extended_objects: list[ObjectCSVManager] = []
    for path in find_object_folders(root_folder):
        if update:
            extended_obj = update_csv(path, config)
        else:
            extended_obj = create_csv(path, config, force_overwrite)

        if extended_obj is not None:
            extended_objects.append(extended_obj)
    return extended_objects
