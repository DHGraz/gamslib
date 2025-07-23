"""Function do collect and update csv files."""

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
    """Collect csv data from all object folders below object_root_dir.

    This function collects all data from all object.csv and all datastream.csv files
    below root_dir.
    The collected data is stored in two files 'object_csv_path'  and 'datastream_csv_path'.

    Returns a ObjectCSV object containing all object and datastream metadata.
    """
    object_csv_path = object_csv_path or Path.cwd() / objectcollection.ALL_OBJECTS_CSV
    datastream_csv_path = (
        datastream_csv_path or Path.cwd() / objectcollection.ALL_DATASTREAMS_CSV
    )

    collector = ObjectCollection()
    collector.collect_from_objects(object_root_dir)
    collector.save_to_csv(object_csv_path, datastream_csv_path)
    return collector

    # all_objects_csv = ObjectCSVManager(object_root_dir)
    # for objectfolder in find_object_folders(object_root_dir):
    #     obj_csv = ObjectCSVManager(objectfolder)
    #     for objmeta in obj_csv.get_objectdata():
    #         all_objects_csv.add_objectdata(objmeta)
    #     for dsmeta in obj_csv.get_datastreamdata():
    #         all_objects_csv.add_datastream(dsmeta)
    # all_objects_csv.sort()
    # all_objects_csv.write(object_csv_path, datastream_csv_path)
    # return all_objects_csv


def split_from_xlsx(
    object_root_dir: Path, xlsx_file: Path | None = None
) -> tuple[int, int]:
    """Update object folder csv metadata from the an xlsx file.

    This function reads the xlsx file, which was created by collect_csv_data(), and
    updates the csv files in all object folders below object_root_dir.

    object_root_dir is the root directory containing all object folders.
    If xlsx_file is None, it defaults to the current working directory with the name
    'all_objects.xlsx'.

    Returns a a tuple of ints: number of updated objects and number of updated datastreams.

    Raises a UserWarning if an object directory does not exist.
    """
    collector = ObjectCollection()
    collector.load_from_xlsx(xlsx_file)
    return collector.distribute_to_objects(object_root_dir)


def split_from_csv(
    object_root_dir: Path,
    object_csv_path: Path | None = None,
    ds_csv_path: Path | None = None,
) -> tuple[int, int]:
    """Update object folder csv metadata from the combined csv data.

    This function reads the csv files, which were created by collect_csv_data(), and
    updates the csv files in all object folders below object_root_dir.

    object_root_dir is the root directory containing all object folders.
    If object_csv_path and ds_csv_path are None, it defaults to the current working
    directory with the name 'object.csv' and 'datastreams.csv'.

    Returns a a tuple of ints: number of updated objects and number of updated datastreams.

    Raises a UserWarning if an object directory does not exist.
    """
    collector = ObjectCollection()
    collector.load_from_csv(object_csv_path, ds_csv_path)
    return collector.distribute_to_objects(object_root_dir)


#     object_root_dir: Path,
#     input_dir: Path | None = None,
#     object_csv_filename: str = objectcollection.ALL_OBJECTS_CSV,
#     ds_csv_filename: str = objectcollection.ALL_DATASTREAMS_CSV,
# ) -> tuple[int, int]:
#     """Update csv metadata files with data from the combined csv data.

#     If collected_csv_dir is None, we assume that the directory
#     containing the combined csv data is the local working directory. This is
#     where collect_csv_data() stores the data by default.

#     `object_csv_filename` and `ds_csv_filename` are the names of the csv files.
#     The must only be set, if the names are different from the default names.

#     In other words: this function updates all object and datatstream
#     metadata with data changed in the central csv files.

#     Returns a a tuple of ints: number of updated objects and number of updated datastreams.
#     """
#     collector = ObjectCollection()
#     collector.load_from_csv(object_csv_path, ds_csv_path)
#     # num_of_changed_objects = 0
#     # num_of_changed_datastreams = 0

#     # if input_dir is None:
#     #     input_dir = Path.cwd()

#     # all_objects_csv = ObjectCSV(input_dir, object_csv_filename, ds_csv_filename)
#     # for objectfolder in find_object_folders(object_root_dir):
#     #     obj_csv = ObjectCSV(objectfolder)
#     #     obj_csv.clear()
#     #     for obj_data in all_objects_csv.get_objectdata(obj_csv.object_id):
#     #         obj_csv.add_objectdata(obj_data)
#     #         num_of_changed_objects += 1

#     #     for ds_data in all_objects_csv.get_datastreamdata(obj_csv.object_id):
#     #         obj_csv.add_datastream(ds_data)
#     #         num_of_changed_datastreams += 1

#     #     obj_csv.write()

#     # return num_of_changed_objects, num_of_changed_datastreams
