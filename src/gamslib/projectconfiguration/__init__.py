"""GAMS Project Configuration Management.

This module provides tools to locate, validate, and load project configuration files 
for GAMS projects.
Supported sources include `project.toml`, `.env`, and environment variables, with a 
clear precedence order.

Main features:

  - Automatic discovery of configuration files.
  - Validation of configuration structure and values.
  - Access to configuration data as Python objects.
  - Layered overrides: `.env` values override `project.toml`, environment variables override both.

Usage:
    Call `get_configuration()` to retrieve the current project configuration.
    If no configuration file is found, `MissingConfigurationException` is raised.

Precedence example:

  - `project.toml`: base configuration.
  - `.env`: overrides values in `project.toml`.
  - Environment variables: override both `.env` and `project.toml`.
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


@lru_cache()
def get_configuration(config_file: Path | str | None = None) -> Configuration:
    """
    Load and return the project configuration.

    The configuration is determined in the following order:

      1. If `config_file` is provided, use it.
      2. If the environment variable `GAMSCFG_PROJECT_TOML` is set, use its value as the path.
      3. If a `.env` file exists in the current directory and contains a `project_toml` field, use that.

    Raises:
        MissingConfigurationException: If no configuration file is found.

    Note:
        Values from `project.toml` are overridden by those in `.env`, which are further overridden by environment variables.
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
