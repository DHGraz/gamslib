# The `objectcsv` subpackage

Tools for managing object and datastream metadata in CSV files for GAMS projects.

This package provides utilities to read, write, validate, and manipulate metadata stored in object.csv and datastreams.csv files, which accompany GAMS bags but are not part of the bag itself.

## Modules

  - [create_csv](create_csv.md): Create CSV files for all objects and datastreams inside an project dir
  - [manage_csv](manage_csv.md): Collects metadata from all objects into a single CSV for efficient 
       editing, and updates individual object directories from the aggregated data
  - [utils](utils.md): Some useful functions for dealing with projectdirs
  - [xlsx](xlsx.md): Converts CSV files to XLSX format and vice versa, enabling 
    spreadsheet-based editing and avoiding encoding issues common with CSV imports/exports.


## Important classes

  - [DSData](dsdata.md): Represents metadata of a single GAMS data stream
  - [DublinCore](dublincore.md): A class which represents Dublin Core metadata (from the DC.xml file).
  - [ObjectCollection](objectcollection.md): Aggregates metadata from multiple objects into a single CSV file
    and distributes updates back to individual object directories. Useful for batch 
    editing and synchronization.
  - [ObjectCSVManager](objectcsvmanager.md): Manages metadata for a single object and its 
    datastreams. Handles reading, writing, validating, merging, and updating CSV files.
  - [ObjectData](objectdata.md): Represents Metadata of a single GAMS object
  





