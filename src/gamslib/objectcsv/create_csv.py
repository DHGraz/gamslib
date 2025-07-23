"""Create object.csv and datastreams.csv files.

This module creates the object.csv and datastreams.csv files for one or many given
object folder. It uses data from the DC.xml file and the project configuration
to fill in the metadata. When not enough information is available, some fields
will be left blank or filled with default values.
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
    """Check if the file should be used as datastream file.

    We ignore objects.csv and datastreams.csv files, as well as files
    matching any of the ignore patterns in the configuration.
    """
    if not ds_file.is_file():
        return False
    if ds_file.name in (
        OBJ_CSV_FILENAME,
        DS_CSV_FILENAME,
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
    """Get the rights from various sources.

    Lookup in this ortder:

      1. Check if set in dublin core
      2. Check if set in the configuration
      3. Use a default value.
    """
    rights = dc.get_element_as_str("rights", preferred_lang="en", default="")
    if not rights:  # empty string is a valid value
        rights = config.metadata.rights or defaultvalues.DEFAULT_RIGHTS
    return rights


def extract_dsid(datastream: Path | str, keep_extension=True) -> str:
    """Extract and validate the datastream id from a datastream path.

    If remove_extension is True, the file extension is removed from the PID.
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
    """Detect the language(s) of a file.

    Return detected language(s) as a string separated by the given delimiter.
    """
    languages = []
    # we decided not to use language detection for now
    return delimiter.join(languages) if languages else ""


def collect_object_data(pid: str, config: Configuration, dc: DublinCore) -> ObjectData:
    """Find data for the object.csv by examining dc file and configuration.

    This is the place to change the resolving order for data from other sources.
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
    """Create a title for the datastream based on its ID and format."""
    return f"{format_info.description}: {dsid}"


def make_ds_description(dsid: str, format_info: FormatInfo) -> str:
    """Create a description for the datastream based on its ID and format.

    If no subtype is available, an empty string is returned.
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
    """Collect data for a single datastream."""
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
    """Generate the csv file containing the preliminary metadata for a single object.

    Existing csv files will not be touched unless 'force_overwrite' is True.
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
    """Update an existing CSV file for a given object directory.

    This function is used to update the metadata for an object directory with existing CSV files.

    This function is useful if new datastreams have been added to an object directory
    after the CSV files have been initailly created.
    Another use case is when settings in the metadata coniguration
    have changed and the metadata in the CSV files need to be updated.
    The CSV files are not overwritten, but updated with the new data.
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
    """Create the CSV files for all objects below root_folder."""
    extended_objects: list[ObjectCSVManager] = []
    for path in find_object_folders(root_folder):
        if update:
            extended_obj = update_csv(path, config)
        else:
            extended_obj = create_csv(path, config, force_overwrite)

        if extended_obj is not None:
            extended_objects.append(extended_obj)
    return extended_objects
