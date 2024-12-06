# gamslib

gamslib is a collection of GAMS related modules and packages, which are used in multiple other packages.

## objectcsv

Handle object and datastream metadata in object csv files.

When creating bags for GAMS, we provide some metadata in csv
files (which are not part of the bag, btw).

The objectcsv package provides tools to handle this metadata.

  * The ObjectCSV class represents the object    
    and datastream csv data for a single object. It is created by providing the 
    path to the  object directory. 
  * The manage_csv module can be used to collect csv data from all objects 
    into a single file, which makes editing the data more efficient.
    It also has a function to update the csv files in the object directories 
    based on the collected data.
  * The xlsx module can be used to convert the csv files to xlsx files 
    and vice versa. This is useful for editing the data in a spreadsheet 
    without the hassles of importing and exporting the csv files, which 
    led to encoding problems in the past.

## projectconfiguration

This package contains a central class `Configuration` that represents the 
project configuration. To create this object, the function 
`load_configuration(OBJECT_ROOT, [PATH_TO_TOML_FILE])` should be used.

The function tries to find the project configuration file, validates 
its content, and creates the central Configuration object with all 
sub-objects (Each TOML inline table is provided as its own sub-object). 
These sub-objects are currently:

  * general
  * metadata

A basic configuration file can be generated via the `create_condiguration()` function.