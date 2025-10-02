"""General-purpose library for shared GAMS package functionality.

The gamslib package provides reusable modules for GAMS projects, 
including:

  - formatdetect: Functions to identify file formats based on file 
    content. Provides multiple detectors, which can be configured
    in the project configuration (e.g. pyproject.toml). Currently
    these Detectors are available:
      - MimietDetector: Uses the `mimetypes` library to identify
        file formats based on file extensions. This is a minimal detector
        and should be used as a fallback only.
      - MagikaDetector: Uses the Google Magika library to identify
        file formats based on file content. This is the preferred
        detector and should be used by default.
    All detectors implement the FormatDetector abstract base class
    and return FormatInfo objects with the detected format information.
    The FormatInfo object includes the MIME type, detector name, and the
    subformat name if applicable. The subformat is determined by heuristics
    based on the MIME type and file content. Currenntly supported subformats
    include:
      - XML subformats
      - JSON subformats
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
