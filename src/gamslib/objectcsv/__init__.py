"""Handle object and datastream metadata in csv files.

When creating bags for GAMS, we provide some metadata in csv
files (which are not part of the bag, btw).

The objectcsv package provides tools to handle this metadata.

  * The ObjectCSVManager class is used to manage the metadata
    of a single object and its datastreams. It reads and writes the
    metadata to CSV files named `object.csv` and `datastreams.csv`
    respectively. It also provides methods to validate, merge, and manipulate
    the object and datastream metadata.
  * The ObjectCollection class is used to collect metadata from multiple
    objects into a single csv file. It can also distribute the collected data
    back to the individual object directories. This is useful for managing
    metadata for a large number of objects, as it allows to edit the data in
    a single file and then distribute the changes back to the individual objects.
  * The dublincore_csv module represents the object metadata stored in
    the objects 'DC.xml' file. It provides useful functions for acessing
    DC data e.g. for prefered languages etc.
  * The create_csv module can be used to initally create the csv files for
    all objects
  * The manage_csv module can be used collect csv data from all objects
    into a single file, which makes editing the data more efficient.
    It also has a function to update the csv files in the object directories
    based on the collected data.
  * The xlsx module can be used to convert the csv files to xlsx files
    and vice versa. This is useful for editing the data in a spreadsheet
    without the hassles of importing and exporting the csv files, which
    led to encoding problems in the past.

The "public" functions and classes from the submodules are directly
available in the objectcsv:

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
