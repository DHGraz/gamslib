"Provides a configuration class"

# pylint: disable=too-many-arguments
# pylint: disable=too-few-public-methods
# pylint: disable=too-many-positional-arguments

import json
from dataclasses import dataclass
from importlib import resources as impresources
from pathlib import Path
import tomllib
from abc import ABC

import jsonschema

#from pydantic import BaseModel


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
def AbstractConfigSection(ABC):
    """An abstract class for the configuration sections."""

    def __new__(cls, *args, **kwargs):
        if cls == AbstractConfigSection or cls.__bases__[0] == AbstractConfigSection: 
            raise TypeError("Cannot instantiate abstract class.") 
        return super().__new__(cls)        

    def validate(self, value: str):
        """Validate the value before setting it."""
        raise NotImplementedError("Method not implemented.")

    def set_value(self, name:str, value: str):
        """Set a value in the configuration object.
        
        name is a string with the format 'section.key'.
        """
        parts = name.split(".")
        key = parts.pop()
        if len(parts) == 1:  # so more subsections
            self.validate(parts[0], value)
            setattr(self, key, value)
        else:
            section_name = ".".join(parts)
            section_object = getattr(self, section_name, None)
            if section_object is None or isinstance(section_object, AbstractConfigSection):
                raise ValueError(f"Unknown section '{section_name}'")
            else:
                child_section = ".".join(parts.pop(0))
                setattr(section_object, child_section, value)



        # parts = name.split(".")
        # key = parts.pop()
        # for section_name in parts:
        #     section_object = getattr(self, section_name, None)
        #     if section_object is None or isinstance:
        #         raise ValueError(f"Unknown section '{section_name}'")
        #     else:
                
        #     if section == "metadata":
        #         setattr(self.metadata, key, value)
        #     elif section == "general":
        #         setattr(self.general, key, value)
        #     else:
        #         raise ValueError(f"Unknown section '{section}'")
        # if '.' in name:
            


@dataclass
class Metadata(AbstractConfigSection):
    """Represent the 'metadata' section of the configuration file."""

    project_id: str
    creator: str
    rights: str
    publisher: str
    
    def validate(self, key: str, value: str):
        if key in ["project_id", "creator", "rights", "publisher"]:
            if not value.strip():
                raise ValueError(f"{key} must not be empty")


# class Metadata:
#     """Represent the 'metadata' section of the configuration file."""

#     def __init__(
#         self,
#         project_id: str,
#         creator: str,
#         publisher: str,
#         rights: str,
#     ):
#         self._project_id = project_id
#         self._creator = creator
#         self._publisher = publisher
#         self._rights = rights

#     @property
#     def project_id(self):
#         """Return the project id."""
#         return self._project_id

#     @property
#     def creator(self):
#         """Return the creator."""
#         return self._creator

#     @property
#     def publisher(self):
#         """Return the publisher."""
#         return self._publisher

#     @property
#     def rights(self):
#         """Return the rights."""
#         return self._rights

@dataclass
class General(AbstractConfigSection):
    """Represent the 'general' section of the configuration file."""

    dsid_keep_extension: bool = True
    loglevel: str = "info"

    def validate(self, key: str, value: str):
        if key == "dsid_keep_extension":
            if type(value) != bool:
                raise ValueError("dsid_keep_extension must be a boolean")
        elif key == "loglevel":
            if value.lower() not in ["debug", "info", "warning", "error"]:
                raise ValueError("loglevel must be 'debug', 'info', 'warning' or 'error'")

# class General:
#     """Represent the 'general' section of the configuration file."""

#     def __init__(self, dsid_keep_extension: bool, loglevel: str):

#         self._dsid_keep_extension: bool = dsid_keep_extension
#         self._loglevel: str = loglevel

    
#     @property
#     def dsid_keep_extension(self):
#         """Return the dsid_keep_extension."""
#         return self._dsid_keep_extension
    
#     @property
#     def loglevel(self):
#         """Return the loglevel."""
#         return self._loglevel.lower()
    
class Configuration:
    """Represent the configuration from the project toml file.

    Properties can be accessed as attributes of the object and sub object:
        eg.: metadata.rights
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
        
        self.metadata = Metadata(**cfg_dict["metadata"])
        self.general = General(**cfg_dict["general"])

    def set_value(self, name:str, value: str):
        """Set a value in the configuration object.
        
        name is a string with the format 'section.key'. Is also capable to deal with more
        than one level of sections as long as the sublevel implement AbstractConfigSection.
        """
        parts = name.split(".")
        key = parts.pop()
        section_name = ".".join(parts)
        section_object = getattr(self, section_name, None)
        if section_object is None or isinstance(section_object, AbstractConfigSection):
            raise ValueError(f"Unknown section '{section_name}'")
        else:
            child_section = ".".join(parts.pop(0))
            setattr(section_object, child_section, value)
                
        #     if section == "metadata":
        #         setattr(self.metadata, key, value)
        #     elif section == "general":
        #         setattr(self.general, key, value)
        #     else:
        #         raise ValueError(f"Unknown section '{section}'")
        # if '.' in name:
            
            sections = parts[:-1]
            key = parts[-1]
        else:
            sections = []
            key = name
        if section == "metadata":
            setattr(self.metadata, key, value)
        elif section == "general":
            setattr(self.general, key, value)
        else:
            raise ValueError(f"Unknown section '{section}'")
        
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
