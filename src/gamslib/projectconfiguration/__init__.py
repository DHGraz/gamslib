"""Handle project configuration.

The projectconfiguration package contains the classes and functions to
manage the configuration of a GAMS project.

It tries to find a configuration, validates the configuration and provides
all configuration inline tables as Python objects.
"""

from pathlib import Path
from importlib import resources as impresources
import shutil
import logging
from .configuration import Configuration, load_configuration

__all__ = ["Configuration", "load_configuration"]

logger = logging.getLogger()


def create_configuration(objects_dir: Path) -> Path | None:
    """Create a project.toml template file in the objects_dir directory.

    It is assumed that the objects_dir is the root directory of a GAMS project
    and that the directory exists.
    The template file will not be created if a project.toml file already exists.
    Return the path to the created project.toml file or None if the file already exists.
    """
    toml_file = objects_dir / "project.toml"
    if toml_file.exists():
        logger.warning("'%s' already exists. Will not be re-created.", toml_file)
        return None
    toml_template_file = str(
        impresources.files("gamslib")
        / "projectconfiguration"
        / "resources"
        / "project.toml"
    )
    shutil.copy(toml_template_file, toml_file)
    return objects_dir / "project.toml"
