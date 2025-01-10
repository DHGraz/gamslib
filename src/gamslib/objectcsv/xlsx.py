"""Module to convert csv to xlsx files."""

import csv
from pathlib import Path

import pylightxl as xl


def read_csv(csvfile: Path, skip_header: bool = True) -> list[list[str]]:
    """Read a csv file and return a list of rows."""
    with open(csvfile, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        if skip_header:
            next(reader)
        return list(reader)


def csv_to_xlsx(object_csv: Path, ds_csv: Path, output_file: Path) -> Path:
    """Convert csv files to xlsx files.

    Convert the csv files object_csv and ds_csv to xlsx files in the output_dir.

    Returns Path to output file.
    """
    object_data = read_csv(object_csv, skip_header=False)
    ds_data = read_csv(ds_csv, skip_header=False)

    db = xl.Database()
    db.add_ws("Object Metadata")
    for row_id, row in enumerate(object_data, start=1):
        for col_id, value in enumerate(row, start=1):
            db.ws(ws="Object Metadata").update_index(row=row_id, col=col_id, val=value)
    db.add_ws("Datastream Metadata")
    for row_id, row_data in enumerate(ds_data, start=1):
        for col_id, value in enumerate(row_data, start=1):
            db.ws(ws="Datastream Metadata").update_index(
                row=row_id, col=col_id, val=value
            )
    xl.writexl(fn=output_file, db=db)
    return output_file


def xlsx_to_csv(
    xlsx_path: Path, obj_csv_path: Path, ds_csv_path: Path
) -> tuple[Path, Path]:
    """Convert a xlsx metadata file to 2 csv files: object.csv and datastreams.csv.

    Return Paths to the csv files as tuple (obj_csv_path, ds_csv_path).
    """
    db = xl.readxl(xlsx_path)

    object_data = list(db.ws(ws="Object Metadata").rows)
    ds_data = list(db.ws(ws="Datastream Metadata").rows)

    with open(obj_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(object_data)

    with open(ds_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(ds_data)
    return obj_csv_path, ds_csv_path
