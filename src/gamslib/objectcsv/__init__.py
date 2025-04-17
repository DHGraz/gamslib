"""Handle object and datastream metadata in csv files.

When creating bags for GAMS, we provide some metadata in csv
files (which are not part of the bag, btw).

The objectcsv package provides tools to handle this metadata.

  * The ObjectCSV class represents the object and datastream csv data
    for a single object. It is created by providing the path to the
    object directory. It is composed of two classes:

    * ObjectCSVFile represents the object metadata. It hold typically
      a single ObjectData object, but can hold multiple objects if needed.
    * DatastreamsCSVFile represents the datastream metadata. It holds
        typically multiple DSData objects, one for each datastream.
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

  * ObjectCSV
  * ObjectData
  * DSData
  * create_csv_files
  * collect_csv_data
  * update_csv_files
  * csv_to_xlsx
  * xlsx_to_csv
"""

from .dsdata import DSData
from .objectdata import ObjectData
from .objectcsv import ObjectCSV
from .create_csv import create_csv_files
from .manage_csv import collect_csv_data, split_csv_files
from .xlsx import csv_to_xlsx, xlsx_to_csv

__all__ = [
    "ObjectCSV",
    "collect_csv_data",
    "create_csv_files",
    "csv_to_xlsx",
    "dsdata",
    "objectdata",
    "split_csv_files",
    "xlsx_to_csv",
]
