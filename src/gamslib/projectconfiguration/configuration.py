"Provides a configuration class"

from pathlib import Path

import tomllib
from pydantic import AfterValidator, BaseModel, StringConstraints
from pydantic_core import ValidationError
from typing_extensions import Annotated


class ProjectMetadata(BaseModel):
    """Metadata of a project.
    
    This is a Pydantic model for the project.metadata inline table.
    It is an aggregation of the Project object.
    """
    projectname: Annotated[
        str,
        StringConstraints(strip_whitespace=True),
        AfterValidator(lambda x: x),
        StringConstraints(min_length=2),
    ]
    creator: Annotated[
        str,
        StringConstraints(strip_whitespace=True),
        AfterValidator(lambda x: x),
        StringConstraints(min_length=2),
    ]
    publisher: Annotated[
        str,
        StringConstraints(strip_whitespace=True),
        AfterValidator(lambda x: x),
        StringConstraints(min_length=2),
    ]
    rights: str = ""


class ObjectCSV(BaseModel):
    dsid_keep_extension: bool             

class Project(BaseModel):
    """A project object.
    
    This is a Pydantic model for the project inline table 
    used as aggregation of the Configuration project.
    """
    metadata: ProjectMetadata
    


class Configuration(BaseModel):
    """A configuration object."""

    toml_file: Path
    project: Project
    objectcsv: ObjectCSV

    @classmethod
    def from_toml(cls, toml_file: Path):
        """Create a configuration object from a TOML file.

        Rewrites some Errors to make them easier to understand.
        """
        try:
            data = tomllib.loads(toml_file.read_text())
            data["toml_file"] = toml_file
            return cls(**data)
        except tomllib.TOMLDecodeError as e:
            raise tomllib.TOMLDecodeError(
                f"Error in project TOML file '{toml_file}': {e}"
            ) from e
        except ValidationError as e:
            error = e.errors()[0]
            if error["type"] == "missing":
                raise ValueError(
                    f"Error in project TOML file '{toml_file}': "
                    f"missing required field '{'.'.join([str(e) for e in error['loc']])}'"
                ) from e

            raise ValueError(
                f"Error in project TOML file '{toml_file}': {e}"
            ) from e


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


def load_configuration(
    object_root: Path, config_file: Path | str | None = None
) -> Configuration:
    """Read the configuration file and return a configuration object."""
    if config_file is None:
        config_file = find_project_toml(object_root)
    if isinstance(config_file, str):
        config_file = Path(config_file)
    configuration = Configuration.from_toml(config_file)
    return configuration
