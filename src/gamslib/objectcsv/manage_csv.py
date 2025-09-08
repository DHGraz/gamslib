"""Functions to collect and update object and datastream CSV files for GAMS projects.

Provides utilities to aggregate metadata from all object folders into central CSV/XLSX files,
and to distribute updated metadata back to individual object folders.
"""

import logging
from pathlib import Path

from gamslib.objectcsv import objectcollection
from gamslib.objectcsv.objectcollection import ObjectCollection

logger = logging.getLogger()


def collect_csv_data(
    object_root_dir: Path,
    object_csv_path: Path | None = None,
    datastream_csv_path: Path | None = None,
) -> ObjectCollection:
    """
    Collect metadata from all object folders below object_root_dir and save to combined CSV files.

    Args:
        object_root_dir (Path): Root directory containing all object folders.
        object_csv_path (Path | None): Path to save combined object metadata CSV. Defaults to 'object.csv' in CWD.
        datastream_csv_path (Path | None): Path to save combined datastream metadata CSV. Defaults to 'datastreams.csv' in CWD.

    Returns:
        ObjectCollection: Collection containing all object and datastream metadata.

    Notes:
        - Reads all object.csv and datastreams.csv files below object_root_dir.
        - Saves aggregated metadata to the specified CSV files.
    """
    object_csv_path = object_csv_path or Path.cwd() / objectcollection.ALL_OBJECTS_CSV
    datastream_csv_path = (
        datastream_csv_path or Path.cwd() / objectcollection.ALL_DATASTREAMS_CSV
    )

    collector = ObjectCollection()
    collector.collect_from_objects(object_root_dir)
    collector.save_to_csv(object_csv_path, datastream_csv_path)
    return collector


def split_from_xlsx(
    object_root_dir: Path, xlsx_file: Path | None = None
) -> tuple[int, int]:
    """
    Update object folder CSV metadata from a combined XLSX file.

    Args:
        object_root_dir (Path): Root directory containing all object folders.
        xlsx_file (Path | None): Path to the XLSX file. Defaults to 'all_objects.xlsx' in CWD.

    Returns:
        tuple[int, int]: Number of updated objects and number of updated datastreams.

    Raises:
        UserWarning: If an object directory does not exist.

    Notes:
        - Reads the XLSX file created by collect_csv_data().
        - Updates object.csv and datastreams.csv files in all object folders below object_root_dir.
    """
    collector = ObjectCollection()
    collector.load_from_xlsx(xlsx_file)
    return collector.distribute_to_objects(object_root_dir)


def split_from_csv(
    object_root_dir: Path,
    object_csv_path: Path | None = None,
    ds_csv_path: Path | None = None,
) -> tuple[int, int]:
    """
    Update object folder CSV metadata from combined CSV files.

    Args:
        object_root_dir (Path): Root directory containing all object folders.
        object_csv_path (Path | None): Path to combined object metadata CSV. Defaults to 'object.csv' in CWD.
        ds_csv_path (Path | None): Path to combined datastream metadata CSV. Defaults to 'datastreams.csv' in CWD.

    Returns:
        tuple[int, int]: Number of updated objects and number of updated datastreams.

    Raises:
        UserWarning: If an object directory does not exist.

    Notes:
        - Reads the CSV files created by collect_csv_data().
        - Updates object.csv and datastreams.csv files in all object folders below object_root_dir.
    """
    collector = ObjectCollection()
    collector.load_from_csv(object_csv_path, ds_csv_path)
    return collector.distribute_to_objects(object_root_dir)
