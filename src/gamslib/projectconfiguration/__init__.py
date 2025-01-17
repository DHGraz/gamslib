"""Handle project configuration.

The projectconfiguration package contains the classes and functions to
manage the configuration of a GAMS project.

It tries to find a configuration, validates the configuration and provides
all configuration inline tables as Python objects.
"""

import logging
import os
import shutil
import warnings
from importlib import resources as impresources
from pathlib import Path

from dotenv import dotenv_values

from .configuration import Configuration, find_project_toml

__all__ = ["Configuration"]

logger = logging.getLogger()

# Be aware, that this might still ne None after the module has been loaded, 
# if no configuration has been configured via environment variables, a .env 
# file or by calling the load_configuration function.
config = None

def create_configuration(objects_dir: Path) -> Path | None:
    """Create a project.toml template file in the objects_dir directory.

    It is assumed that the objects_dir is the root directory of a GAMS project
    and that the directory exists.
    The template file will not be created if a project.toml file already exists.
    Return the path to the created project.toml file or None if the file already exists.
    """
    toml_file = objects_dir / "project.toml"
    if toml_file.exists():
        warnings.warn(f"'{toml_file}' already exists. Will not be re-created.", UserWarning)
        return None
    toml_template_file = str(
        impresources.files("gamslib")
        / "projectconfiguration"
        / "resources"
        / "project.toml"
    )
    shutil.copy(toml_template_file, toml_file)
    return objects_dir / "project.toml"

def load_configuration(object_root: Path = None, config_file: Path | str | None = None, make_global=False) -> Configuration:
    """Read the configuration file and return a configuration object.
    
    Give either the Path to a project directory (or a subdirectory of 
    the project directory) or an explicit path to the 'project.toml' file.
    If both are given, the explicit path ('config_file') is used.

    'make_gloabal' is a flag to indicate that the configuration object should be stored as a module global.
    If 'make_global' is True, the configuration object will be stored in the module global 'config' variable, 
    even if such an object already exists (will be automatically created, when the module is loaded if either 
    a 'project_toml' is set in the '.env' file or an environment variable 'GAMSCFG_PROJECT_TOML' is set).
    """
    global config
    if object_root is None and config_file is None:
        raise ValueError("Either 'object_root' or 'config_file' must be given when calling load_configuration().")

    if config_file is None:
        config_file = find_project_toml(object_root)
    if isinstance(config_file, str):
        config_file = Path(config_file)
    cfg = Configuration.from_toml(config_file)
    cfg.update_from_dotenv()
    cfg.update_from_env()
    if make_global:
        config = cfg
    return cfg

def init_config():
    """Try to create a module global configuration object (as singleton).
    
    This function should not be called directly, because it is run when 
    the module is loaded. The function expects 
    either a environment variable 'GAMSCFG_PROJECT_TOML' or a '.env' file
    containing at least a 'project_toml' field which points to the project.toml 
    file.

    If none of these are found, the function will return None. This should
    not cause problems, because in most real life use cases the config
    object will be created from the CLI or GUI by calling the 'load_configuration'
    function (where the project dir or even the project.toml file is required).

    If both environment values are set, the 'GAMSCFG_PROJECT_TOML' will be used.
    """
    global config
    if config is None:
        project_toml_file = None
        env_values = dotenv_values('.env')
        if 'GAMSCFG_PROJECT_TOML' in os.environ:
            project_toml_file = os.environ['GAMSCFG_PROJECT_TOML']
        elif 'project_toml' in env_values:
            project_toml_file = env_values['project_toml']
        else:
            logger.warning("No 'project_toml' found in environment variables or in '.env' file. "
                           "You might want to create a configuration object later via load_configuration()")
        if project_toml_file is not None:
            toml_path = Path(project_toml_file)
            if not toml_path.exists():
                raise FileNotFoundError(f"Project toml file '{toml_path}' not found.")
            config = load_configuration(config_file= toml_path)

config = init_config()
