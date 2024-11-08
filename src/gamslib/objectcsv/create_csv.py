import mimetypes
from pathlib import Path
import logging
import re
from gamspreprocessor.configuration import Configuration
from . import DSData, ObjectCSV, ObjectData
from ..utils import find_object_folders 
from .dublincore import DublinCore

logger = logging.getLogger()

DEFAULT_RIGHTS = (
    "Creative Commons Attribution-NonCommercial 4.0 "
    "(https://creativecommons.org/licenses/by-nc/4.0/)"
)
DEFAULT_SOURCE = "local"
DEFAULT_OBJECT_TYPE = "text"

NAMESPACES = {
    "dc": "http://purl.org/dc/elements/1.1/",
}


def get_rights(config: Configuration, dc: DublinCore) -> str:
    """Get the rights from various sources.

    Lookup in this ortder:

      1. Check if set in dublin core
      2. Check if set in the configuration
      3. Use a default value.
    """
    rights = dc.get_element_as_str("rights", default=None)
    if rights is None:
        if config.project.metadata.rights:
            rights = config.project.metadata.rights
        else:
            rights = DEFAULT_RIGHTS
    return rights


def extract_dsid(datastream: Path | str, remove_extension=False) -> str:
    """Extract and validate the datastream id from a datastream path.

    If remove_extension is True, the file extension is removed from the PID.
    """
    if isinstance(datastream, str):
        datastream = Path(datastream)

    pid = datastream.name

    if remove_extension:
        # not everything after the last dot is an extension :-(
        mtype = mimetypes.guess_type(datastream)[0]
        known_extensions = mimetypes.extensions.get(mtype, [])
        if datastream.suffix in known_extensions:
            pid = pid.removesuffix(datastream.suffix)
            logger.debug("Removed extension '%s' for ID: %s", datastream.suffix, pid)
        else:
            parts = pid.split(".")
            if re.match(r"^[a-zA-Z]+\w?$", parts[-1]):
                pid = ".".join(parts[:-1])
                logger.debug("Removed extension for ID: %s", parts[0])
            else:
                logger.warning(
                    "'%s' does not look like an extension. Keeping it in PID.", pid[-1]
                )

    if re.match(r"^[a-zA-Z0-9]+[-.%_a-zA-Z0-9]+[a-zA-Z0-9]+$", pid) is None:
        raise ValueError(f"Invalid PID: '{pid}'")

    logger.debug(
        "Extracted PID: %s from %s (remove_extension=%s)",
        pid,
        datastream,
        remove_extension,
    )
    return pid


def collect_object_data(pid: str, config: Configuration, dc: DublinCore) -> ObjectData:
    """Find data for the object.csv by examining dc file and configuration.

    This is the place to change the resolving order for data from other sources.
    """

    title = "; ".join(dc.get_element("title", default=pid))
    description = "; ".join(dc.get_element("description", default=""))

    return ObjectData(
        recid=pid,
        title=title,
        project=config.project,
        description=description,
        creator=config.creator,
        rights=get_rights(config, dc),
        source=DEFAULT_SOURCE,
        objectType=DEFAULT_OBJECT_TYPE,
    )


def collect_datastream_data(
    ds_file: Path, object_pid: str, config: Configuration, dc: DublinCore,
    remove_extension_for_id=False
) -> DSData:
    """Create a DSData object for a datastream file.

    This is the place to change the resolving order for data from other sources.
    """

    # maybe there are more files which always have the same metadata title / description?
    if ds_file.name == "DC.xml":
        title = "Dublin Core Metadata"
        description = "DC Metadata describing the data stream"
    else:
        title = ""
        description = ""

    return DSData(
        dspath=object_pid + "/" + ds_file.name,
        dsid=extract_dsid(ds_file, remove_extension_for_id),
        title=title,
        description=description,
        # there should be a more reliable way to get the mimetype
        mimetype=mimetypes.guess_type(ds_file)[0],  
        creator=config.metadata.creator,
        rights=get_rights(config, dc)
    )


def create_csv(object_directory: Path, configuration: Configuration) -> None:
    """Generate the csv file containing the preliminary metadata for a single object."""
    objectcsv = ObjectCSV(object_directory)
    object_pid = object_directory.name
    # Avoid that existing (and potentially already edited) metadata is replaced
    if objectcsv.is_new():
        logger.info(
            "CSV files for object '%s' already exist. Will not be re-created.", object_pid
        )
        return

    dc = DublinCore(object_directory / "DC.xml")

    objectcsv.add_objectdata(collect_object_data(object_pid, configuration, dc))
    for ds_file in object_directory.glob("*"):
        if ds_file.is_file() and ds_file.name not in ("object.csv", "datastreams.csv"):
            objectcsv.add_datastream(
                collect_datastream_data(ds_file, object_pid, configuration, dc)
            )
    objectcsv.write()


def create_csv_files(root_folder: Path, config: Configuration) -> list[Path]:
    """Create the CSV files for all objects below root_folder.
    """
    processed_folders = []
    for path in find_object_folders(root_folder):
        create_csv(path, config)
        processed_folders.append(path.relative_to(root_folder))
    return processed_folders
