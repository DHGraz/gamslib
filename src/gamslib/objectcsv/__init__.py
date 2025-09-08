"""Tools for managing object and datastream metadata in CSV files for GAMS projects.

This package provides utilities to read, write, validate, and manipulate metadata stored in
`object.csv` and `datastreams.csv` files, which accompany GAMS bags but are not part of the bag itself.

Main components:

  - ObjectCSVManager: Manages metadata for a single object and its datastreams. Handles reading, writing,
    validating, merging, and updating CSV files.
  - ObjectCollection: Aggregates metadata from multiple objects into a single CSV file and distributes
    updates back to individual object directories. Useful for batch editing and synchronization.
  - dublincore_csv: Functions for accessing and processing Dublin Core metadata from 'DC.xml' files,
    including language preference utilities.
  - create_csv: Initializes CSV files for all objects in a project.
  - manage_csv: Collects metadata from all objects into a single CSV for efficient editing, and updates
    individual object directories from the aggregated data.
  - xlsx: Converts CSV files to XLSX format and vice versa, enabling spreadsheet-based editing and
    avoiding encoding issues common with CSV imports/exports.

Public API:

    DSData
    ObjectCSVManager
    ObjectCollection
    ObjectData
    collect_csv_data()
    create_csv_files()
    csv_to_xlsx()
    split_from_csv()
    split_from_xlsx()
    xlsx_to_csv()

These classes and functions are imported into the package namespace for direct use.
"""

from .dsdata import DSData
from .objectdata import ObjectData
from .objectcsvmanager import ObjectCSVManager
from .objectcollection import ObjectCollection
from .create_csv import create_csv_files
from .xlsx import csv_to_xlsx, xlsx_to_csv
from .manage_csv import split_from_csv, split_from_xlsx, collect_csv_data

__all__ = [
    "DSData",
    "ObjectCSVManager",
    "ObjectCollection",
    "ObjectData",
    "collect_csv_data",
    "create_csv_files",
    "csv_to_xlsx",
    "split_from_csv",
    "split_from_xlsx",
    "xlsx_to_csv",

]
