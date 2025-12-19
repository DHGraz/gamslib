"""Utilities to convert object and datastream CSV files to XLSX format and back.

Provides functions to read CSV files, convert them to XLSX spreadsheets with separate sheets,
and split XLSX files back into object and datastream CSV files.
"""

import csv
from pathlib import Path

import pylightxl as xl


def read_csv(csvfile: Path, skip_header: bool = True) -> list[list[str]]:
    """
    Read a CSV file and return a list of rows.

    Args:
        csvfile (Path): Path to the CSV file.
        skip_header (bool): If True, skip the first row (header).

    Returns:
        list[list[str]]: List of rows, each row as a list of strings.
    """
    with open(csvfile, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        if skip_header:
            next(reader)
        return list(reader)


def csv_to_xlsx(object_csv: Path, ds_csv: Path, output_file: Path) -> Path:
    """
    Convert object and datastream CSV files to a single XLSX file.

    Args:
        object_csv (Path): Path to the object metadata CSV file.
        ds_csv (Path): Path to the datastream metadata CSV file.
        output_file (Path): Path for the output XLSX file.

    Returns:
        Path: Path to the created XLSX file.

    Notes:
        - Object metadata is written to the "Object Metadata" sheet.
        - Datastream metadata is written to the "Datastream Metadata" sheet.
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
    """
    Convert a XLSX metadata file to two CSV files: object.csv and datastreams.csv.

    Args:
        xlsx_path (Path): Path to the XLSX file containing metadata.
        obj_csv_path (Path): Path for the output object metadata CSV file.
        ds_csv_path (Path): Path for the output datastream metadata CSV file.

    Returns:
        tuple[Path, Path]: Paths to the created object and datastream CSV files.

    Notes:
        - Reads "Object Metadata" and "Datastream Metadata" sheets from the XLSX file.
        - Writes each sheet to its respective CSV file.
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
