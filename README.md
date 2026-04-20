# gamslib

Gamslib is a collection of GAMS related modules and packages, which are used in multiple other packages.

## Installation

gamslib is available on pypi.org and can be installed via pip:

```
pip install gamslib
```

## Usage

As gamslib is a library, it can only we used with other code. 

The main purpose is to make code reusable in other GAMS5 projects and to have
a unique way of doing things. If you are not working on GAMS5 reated code
(which is very likely), this library will be useless for you.

Currently these subpackages are available (more to come):

## objectcsv

Handle object and datastream metadata in object csv files.

When creating bags for GAMS, we provide some metadata in csv
files (which are not part of the bag, btw).

The objectcsv package provides tools to handle this metadata.

  * The ObjectCSV class represents the object    and datastream csv data for a
    single object. It is created by providing the path to the  object
    directory. 
  * The manage_csv module can be used to collect csv data from all objects into
    a single file, which makes editing the data more efficient. It also has a
    function to update the csv files in the object directories based on the
    collected data.
  * The xlsx module can be used to convert the csv files to xlsx files and vice
    versa. This is useful for editing the data in a spreadsheet without the
    hassles of importing and exporting the csv files, which led to encoding
    problems in the past.

### Migration notes (since 0.7.13)

`DSData` now enforces required-field validation on every assignment.

What changed:

  * Setting invalid values for required fields (`dspath`, `dsid`, `mimetype`,
    `rights`) raises `ValueError` immediately.
  * Failed assignments are atomic: the previous value is kept unchanged.
  * `dspath` safety checks are applied immediately (`..` traversal, absolute
    paths, and `~`-prefixed paths are rejected).

How to migrate existing code:

  * Do not rely on temporary invalid intermediate states anymore.
  * When updating multiple values, apply only values that are valid at each
    step.
  * If older code set invalid values first and called `validate()` later,
    move that validation logic to the assignment point and handle `ValueError`
    there.

  Example:

  ```python
  # before (no longer valid): temporary invalid state
  ds = DSData(dspath="TEI.xml", dsid="TEI.xml", mimetype="application/xml", rights="GPLv3")
  ds.dsid = ""
  ds.validate()  # used to fail later

  # after: fail at assignment time
  ds = DSData(dspath="TEI.xml", dsid="TEI.xml", mimetype="application/xml", rights="GPLv3")
  try:
    ds.dsid = ""
  except ValueError:
    pass  # ds.dsid is still "TEI.xml"
  ```

## projectconfiguration

This package contains a central class `Configuration` that represents the
project configuration. To create this object, the function
`load_configuration(OBJECT_ROOT, [PATH_TO_TOML_FILE])` should be used.

The function tries to find the project configuration file, validates its
content, and creates the central Configuration object with all sub-objects
(Each TOML inline table is provided as its own sub-object). These sub-objects
are currently:

  * general
  * metadata

A basic configuration file can be generated via the `create_condiguration()`
function.


## Contributing

The Github repository is ment to be a read only mirror of the work repository
hosted on our institutional private GitLab server. You can use the bug tracker
on Github, but everything else should happen in the Zimlab Github repo.


## License

[MIT](https://choosealicense.com/licenses/mit/)
