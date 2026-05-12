---
icon: lucide/rocket
---

# Overview

The gamslib library provides reusable modules for GAMS related software.
GAMS is the *Geisteswissenschaftliches Asset Management System*, developed 
at Graz University (https://gams.uni-graz.at).


The package consists of several sub packages:

  - formatdetect: Functions to identify file formats based on file
       content. Provides multiple detectors, which can be configured
       in the project configuration (e.g. pyproject.toml). 
  - gamsconfig: Tools for managing GAMS package configuration,
       including reading from pyproject.toml and validating configuration
       settings.
  - objectcsv: Tools for reading, writing, validating, and managing
       object and datastream metadata in CSV format for GAMS objects.
       Supports batch editing, conversion to XLSX, and metadata
       aggregation.
  - sip: Tools for creating, validating, and managing *Submission 
       Information Packages* (SIPs) in accordance with GAMS and DSA standards.

Other modules may be added to support common tasks across GAMS packages.



## Installation

gamlib is avaiable via pypi (). Use your package manager to install it like any other package from pypi:

```bash
pip install gamslib
```

or, if you prefer uv:

```
uv install gamslib
```

If you rely the (depricated) Magika Detector, use `uv install gamslib[magika]` instead.

Normally an explicit installation only makes sense for developers. For normal users, gamslib should be
set as depenency in the programs using the library.

## Contributing

The Github repository under https://github.com/dhgraz/gamslib/ is ment to be a read only mirror of the work repository
hosted on our institutional private GitLab server. You can use the bug tracker
on Github, but everything else should happen in the Zimlab Github repo.


## License

[MIT](https://choosealicense.com/licenses/mit/)
