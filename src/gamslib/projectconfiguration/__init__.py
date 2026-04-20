"""A helper module for GAMS project configuration management.

This module provides a central way to access and update project 
configuration data for GAMS projects. On subpackage level, it 
provides the following functions:

  - `get_configuration()`: Retrieve the current project configuration as a 
    `Configuration` object. Call this function to access configuration 
    values in your code. It is implemented as module level function with 
    caching to ensure that the configuration is loaded only once per session. 
    The configuration is sourced from multiple locations with a clear 
    precedence order. See below for more details. 
  - `MissingConfigurationException`: Exception raised when no configuration
    file is found.
  - `configuration_needs_update()`: Check if the current configuration file 
    is missing required keys compared to the template.
  - `update_configuration()`: Update the configuration file with missing 
    keys from the template. This might become useful when the template 
    is updated with new keys and you want to update your existing 
    configuration file without losing existing values.   

The get_configuration() function returns a `Configuration` object which 
represents the complete configuration for a GAMS project. The coniguration 
data is organized in `tables` (e.g., `metadata`, `general`) and each table
contains specific fields` (e.g., `metadata.publisher`, `general.loglevel`). 

Currently, these fields are defined in the `Configuration` class: 

  - `metadata.project_id`: the id of the project (eg.: hsa)
  - `metadata.creator`: the creator of the project (e.g. the name of the principal 
    investigator)
  - `metadata.funder`: the funder of the project (e.g. FWF)
  - `metadata.rights`: the default license for the project (can be overridden in 
    project.csv and datastream.csv for single objects/data streams. Default is 
    'CC BY-NC 4.0', which should be kept if you are using GAMS to publish 
    your data)
  - `metadata.publisher`: the publisher of the project (default is GAMS, which 
    should be kept if you are using GAMS to publish your data)

  - `general.loglevel`: the logging level. Default is "info". Possible values are 
    "debug", "info", "warning", "error" and "critical".
  - `general.dsid_keep_extension`: whether to keep the file extension for dsid. We 
    suggest to keep the extension, because it makes it easier to identify the 
    file type of the datastreams. Set to false if you want to strip the 
    extension for dsid. This field is used when creating datastreams.csv. 
  - `general.format_detector="siegfried`: the format detector to use. You might want to
    keep this unless for good reasons because the older detectors might be removed in 
    the future.
  - `general.format_detector_url`: the URL for the format detector service. 
    Currently not used, so keep it empty. 
  - `general.ds_ignore_files`:   a list of filenames/filename patterns 
    which should be ignored when creating datastreams.csv. This is useful to 
    exclude files which might be in the object directory but but should not be 
    added as datastreams. `object.csv`and `datastreams.csv` are automatically ignored.


This object aggregates configuration data from multiple sources, including the 
`gamsproject.toml` file, `.env` file, and environment variables in this 
order of precedence, meaning that values from `.env` override those 
in `project.toml`, and environment variables override both.

To override configuration values in the `.env` file, create a `.env` file in the 
current working directory. Each field in the configuration can be overridden 
by adding a line in the `.env` file in the format `GAMSCFG_<TABLE>.<FIELD>=value`. 
For example, to override the creator, add `GAMSCFG_METADATA.CREATOR=John Doe`. 

To override configuration values using environment variables, set environment 
variables with the prefix `GAMSCFG_` followed by the table and field name in 
uppercase. For example, to override the creator, set 
`GAMSCFG_METADATA.CREATOR=Jane Doe`.


The `gamsconfig.toml` file containing the project configuration should be located 
in the project directory, the current working directory or a a location
specified by the `GAMSCFG_PROJECT_TOML` environment variable.
"""

import os
from functools import lru_cache
from pathlib import Path

from . import utils
from .configuration import Configuration
from .utils import configuration_needs_update, update_configuration


class MissingConfigurationException(Exception):
    """Raised if the configuration is missing."""

    def __init__(
        self,
        message=(
            "You must provide a configuration file. Set it when calling the "
            "get_configuration() function, use the 'GAMSCFG_PROJECT_TOML' environment "
            "variable or set 'project_toml' in the .env file."
        ),
    ):
        self.message = message
        super().__init__(self.message)


@lru_cache()
def get_configuration(config_file: Path | str | None = None) -> Configuration:
    """
    Load and return the project configuration.

    The configuration is determined in the following order:

      1. If `config_file` is provided, use it.
      2. If the environment variable `GAMSCFG_PROJECT_TOML` is set, use its value 
         as the path.
      3. If a `.env` file exists in the current directory and contains a `project_toml` 
         field, use that.

    Raises:
        MissingConfigurationException: If no configuration file is found.

    Note:
        Values from `project.toml` are overridden by those in `.env`, which are further 
        overridden by environment variables.
        For example:

          - `project.toml` sets `metadata.publisher = "foo"` → used by default.
          - `.env` sets `metadata.publisher = "bar"` → overrides `project.toml`.
          - Environment variable `GAMSCFG_METADATA_PUBLISHER = "baz"` → overrides both.
    """
    if config_file is not None:
        config_path = Path(config_file)
    else:
        config_path = utils.get_config_file_from_env()

    if config_path is None:
        raise MissingConfigurationException()
    return Configuration.from_toml(config_path)

__all__ = ["Configuration", "MissingConfigurationException", "configuration_needs_update", "get_configuration", "update_configuration"]
