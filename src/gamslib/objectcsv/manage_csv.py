"""Function do collect and update csv files."""

import logging
from pathlib import Path

from gamspreprocessor.objectcsv import ObjectCSV

from ..utils import find_object_folders

logger = logging.getLogger()


# def read_csv(csvfile: Path, skip_header: bool = True) -> List[List[str]]:
#     """Read a csv file and return a list of rows."""
#     with open(csvfile, "r", encoding="utf-8", newline="") as f:
#         reader = csv.reader(f)
#         if skip_header:
#             next(reader)
#         return list(reader)


# def read_csv_dict(csvfile: Path) -> List[dict]:
#     """Read a csv file and return a list of dictionaries."""
#     with open(csvfile, "r", encoding="utf-8", newline="") as f:
#         reader = csv.DictReader(f)
#         return list(reader)


def collect_csv_data(
    object_root_dir: Path,
    collected_csv_dir: Path | None = None,
    # objects_file: Path = Path.cwd() / "all_objcts.csv",
    # datastreams_file: Path = Path.cwd() / "all_datastreams.csv",
) -> tuple[Path, Path]:
    """Collect data from all csv files in all object folders.

    This function collects all data from all object.csv and all datastream.csv files
    below root_dir.
    The collected data is stored in two files: objects_file and ds_file.

    Returns the Path to all_objects.csv and all_datastreams.csv as tuple of Path objects.
    """
    # This is were we put all collected data
    all_objects_csv = ObjectCSV(collected_csv_dir or object_root_dir)
    # object_rows:list[dict[str, str]] = []
    # ds_rows = DatastreamsCSVFile(datastreams_file)
    for objectfolder in find_object_folders(object_root_dir):
        obj_csv = ObjectCSV(objectfolder)

        all_objects_csv.add_objectdata(obj_csv.object_data)
        all_objects_csv.add_datastreamscsvfile(obj_csv.datastream_data)

        for obj_data in obj_csv.get_objectdata():
            all_objects_csv.add_objectdata(obj_data)
        for ds_data in obj_csv.get_datastreamdata():
            all_objects_csv.add_datastream(ds_data)
        obj_csv.write()

    all_objects_csv.write()
    return all_objects_csv


#    ds_rows.to_csv(datastreams_file)

# with open(objects_file, "w", encoding="utf-8") as f:
#     writer = csv.writer(f)
#     writer.writerows(object_rows)
# with open(datastreams_file, "w", encoding="utf-8", newline="") as f:
#     writer = csv.writer(f)
#     writer.writerows(ds_rows)
# return objects_file, datastreams_file

# # TODO
# def group_datastreams(ds_data: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
#     """Group datastreams by object."""
#     grouped = {}
#     for row in ds_data:
#         obj_id = row["dspath"].split("/")[0]
#         if obj_id not in grouped:
#             grouped[obj_id] = []
#         grouped[obj_id].append(row)
#     return grouped


# def update_object_csv(object_csv_path: Path, csv_data: Dict[str, str]) -> int:
#     """Update a single object csv file with data from csv_data.

#     Return 1 if the file was updated, 0 otherwise.
#     """
#     with open(object_csv_path, "r", encoding="utf-8") as f:
#         reader = csv.DictReader(f)
#         existing_rows = list(reader)[0]
#     if existing_rows == csv_data:
#         return 0

#     # write new data
#     with open(object_csv_path, "w", encoding="utf-8", newline="") as f:
#         writer = csv.DictWriter(f, fieldnames=csv_data.keys())
#         writer.writeheader()
#         writer.writerow(csv_data)
#     return 1


# def update_ds_csv(ds_csv_path: Path, ds_data: List[Dict[str, str]]) -> int:
#     """Update datastream metadata of one object.

#     Return number of updated data stream metadata records.
#     """
#     existing_records = {}
#     changed_records = 0

#     # Read the existing csv as dict of dicts with dsid as key
#     with open(ds_csv_path, "r", encoding="utf-8", newline="") as f:
#         reader = csv.DictReader(f)
#         for row in reader:
#             existing_records[row["dsid"]] = row

#     # check for each record if it has been changed
#     for new_record in ds_data:
#         if new_record["dsid"] in existing_records:
#             if existing_records[new_record["dsid"]] != new_record:
#                 existing_records[new_record["dsid"]] = new_record
#                 changed_records += 1
#         else:
#             logger.warning("Datastream '%s' not found in '%s'", new_record['dsid'], ds_csv_path)

#     if changed_records > 0:
#         with open(ds_csv_path, "w", encoding="utf-8", newline="") as f:
#             writer = csv.DictWriter(f, fieldnames=ds_data[0].keys())
#             writer.writeheader()
#             for key in sorted(existing_records.keys()):
#                 writer.writerow(existing_records[key])
#     return changed_records


# def find_object_dir(root_dir: Path, recid: str) -> Path:
#     """Normally, an object directory is expected as direct child dir of the root_dir.

#     But, as we want to support deeply nested object directories, too, we need to search for
#     the object directory, as the csv file does not contain information about the path.
#     """
#     for obj_dir in find_object_folders(root_dir):
#         if obj_dir.name == recid:
#             return obj_dir
#     raise FileNotFoundError(f"Object directory for {recid} not found below {root_dir}")


def update_csv_files(
    object_root_dir: Path,
    collected_csv_dir: Path | None = None,
    # object_csv: Path = Path.cwd() / "all_objects.csv",
    # dc_csv: Path = Path.cwd() / "all_datastreams.csv",
) -> tuple[int, int]:
    """Update csv metadata files with data from the combined csv data.

    If collected_csv_dir is None, we assume that the directory
    containing the combined csv data is object_root. This is
    where collect_csv_data() stores the data by default.

    In other words: this function updates all object and datatstream
    metadata with data changed in the central csv files.

    Returns a a tuple of ints: number of updated objects and number of updated datastreams.
    """
    num_of_changed_objects = 0
    num_of_changed_datastreams = 0

    all_objects_csv = ObjectCSV(collected_csv_dir or object_root_dir)

    for objectfolder in find_object_folders(object_root_dir):
        obj_csv = ObjectCSV(objectfolder)
        obj_csv.clear()
        for obj_data in all_objects_csv.get_objectdata(obj_csv.object_id):
            num_of_changed_objects += 1
            obj_csv.add_objectdata(obj_data)
        for ds_data in obj_csv.get_datastreamdata(obj_csv.object_id):
            num_of_changed_datastreams += 1
            obj_csv.add_datastream(ds_data)
        obj_csv.write()
        # all_objects_csv.add_objectdata(objdata)
        # all_objects_csv.add_objectdata(obj_csv.object_data)
        # all_objects_csv.add_datastreamscsvfile(obj_csv.datastream_data)
    # object_data = read_csv_dict(object_csv)
    # grouped_ds_data = group_datastreams(read_csv_dict(dc_csv))

    return num_of_changed_objects, num_of_changed_datastreams