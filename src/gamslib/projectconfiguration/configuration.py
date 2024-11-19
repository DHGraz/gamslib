"Provides a configuration class"

# pylint: disable=too-many-arguments
# pylint: disable=too-few-public-methods
# pylint: disable=too-many-positional-arguments

import json
from dataclasses import dataclass
from importlib import resources as impresources
from pathlib import Path
import tomllib

import jsonschema


def find_project_toml(start_dir: Path) -> Path:
    """Find the project.toml file in the start_dir or above.

    Return a path object to the project.toml file.
    If no project.toml file is found, raise a FileNotFoundError.
    """
    for folder in (start_dir / "a_non_existing_folder_to_include_start_dir").parents:
        project_toml = folder / "project.toml"
        if project_toml.exists():
            return project_toml

    # if we read this point, no project.toml has been found in object_root or above
    # So we check if there's a project.toml in the current working directory
    project_toml = Path.cwd() / "project.toml"

    if project_toml.exists():
        return project_toml
    raise FileNotFoundError("No project.toml file found in or above the start_dir.")


@dataclass
class Project:
    """Represent the 'project' section of the configuration file."""

    def __init__(
        self,
        project_id: str,
        creator: str,
        publisher: str,
        rights: str,
        dsid_keep_extension: bool,
    ):
        self._project_id = project_id
        self._creator = creator
        self._publisher = publisher
        self._rights = rights
        self._dsid_keep_extension = dsid_keep_extension

    @property
    def project_id(self):
        """Return the project id."""
        return self._project_id

    @property
    def creator(self):
        """Return the creator."""
        return self._creator

    @property
    def publisher(self):
        """Return the publisher."""
        return self._publisher

    @property
    def rights(self):
        """Return the rights."""
        return self._rights

    @property
    def dsid_keep_extension(self):
        """Return the dsid_keep_extension."""
        return self._dsid_keep_extension


class Configuration:
    """Represent the configuration from tge project toml file.

    The only reason, to use this class and not a dictionary is,
    that we expect changes to the tomls file. Using a class
    allows to keep the interface stable or provide a legacy interface.
    """

    def __init__(self, toml_file: Path):
        cfg_dict = self._load_config(toml_file)
        self.toml_file = toml_file

        try:
            jsonschema.validate(cfg_dict, self._load_schema())
        except jsonschema.ValidationError as e:
            path = ".".join([str(x) for x in e.absolute_path])
            msg = f"Error in project TOML file '{toml_file}': {e.message} at [{path}]"
            raise ValueError(msg) from e
        self.project = Project(**cfg_dict["project"])

    @staticmethod
    def _load_config(toml_file: Path) -> dict:
        """Read the configuration file and return toml as dict."""
        with toml_file.open("rb") as config_file:
            cfg_dict = tomllib.load(config_file)
        return cfg_dict

    @staticmethod
    def _load_schema() -> dict:
        """Load the schema for the configuration file."""
        schema_file = (
            impresources.files("gamslib")
            / "projectconfiguration"
            / "resources"
            / "projecttoml_schema.json"
        )
        with schema_file.open("r", encoding="utf-8") as f:
            cfg_schema = json.load(f)
        return cfg_schema


def load_configuration(object_root: Path, config_file: Path | str | None = None):
    """Read the configuration file and return a configuration object."""
    if config_file is None:
        config_file = find_project_toml(object_root)
    if isinstance(config_file, str):
        config_file = Path(config_file)

    return Configuration(config_file)
