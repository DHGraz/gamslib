"""General-purpose library for shared GAMS package functionality.

The gamslib package provides reusable modules for GAMS projects, 
including:

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
  - sip: Tools for creating, validating, and managing Submission Information
    Packages (SIPs) in accordance with GAMS and DSA standards.

Other modules may be added to support common tasks across GAMS packages.
"""
