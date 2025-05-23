"""Provide an manage project configuration.

Module configuration provides classes and functions to manage the configuration.


Module projectconf has a 'config' variable which contains the configuration object.
The module also g
The projectconfiguration package contains the classes and functions to
manage the configuration of a GAMS project.

It tries to find a configuration, validates the configuration and provides
all configuration inline tables as Python objects.
"""

import os
from functools import lru_cache
from pathlib import Path

from . import utils
from .configuration import Configuration


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


@lru_cache
def get_configuration(config_file: Path | str | None = None) -> Configuration:
    """Read the configuration file and return a configuration object.

    If config_file is set, the configuration will be read from this file.
    If no configuration file is given, the function checks

    1. if the environment variable 'GAMSCFG_PROJECT_TOML' is set and points to a file.
    2. if a '.env' file exists in the current directory and if it contains
       a 'project_toml' field.

    If no configuration file is found, a ValueError is raised.

    Be aware, that values from the 'project.toml' file will be overwritten by
    values in the '.env' file and the environment.

    E.g.: If 'project.toml' has set 'metatdata.publisher' set to 'foo',
    this value is used. If '.env' has set 'metadata.publisher' to 'bar',
    this value is used. If the environment variable 'GAMSCFG_METADATA_PUBLISHER'
    is set to 'baz', this value is used.
    """
    if config_file is not None:
        config_path = Path(config_file)
    else:
        config_path = utils.get_config_file_from_env()

    if config_path is None:
        raise MissingConfigurationException
    return Configuration.from_toml(config_path)
