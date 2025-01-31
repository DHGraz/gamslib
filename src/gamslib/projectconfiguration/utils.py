"""Utility function for the projectconfiguration sub module."""
import shutil
import warnings
from importlib import resources as impresources
from io import StringIO
from pathlib import Path

from dotenv import dotenv_values


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


def create_configuration(project_dir: Path) -> Path | None:
    """Create a project.toml template file in the project_dir directory.

    It is assumed that the project_dir is the root directory of a GAMS project
    and that the directory exists.
    The template file will not be created if a project.toml file already exists.

    Return the path to the created project.toml file or None if the file already exists.
    """
    toml_file = project_dir / "project.toml"
    if toml_file.exists():
        warnings.warn(
            f"'{toml_file}' already exists. Will not be re-created.", UserWarning
        )
        return None
    toml_template_file = str(
        impresources.files("gamslib")
        / "projectconfiguration"
        / "resources"
        / "project.toml"
    )
    shutil.copy(toml_template_file, toml_file)
    return project_dir / "project.toml"


def read_path_from_dotenv(dotenv_file: Path, fieldname: str) -> Path | None:
    """Read a path value from a dotenv file.

    This utility function returns a correct path, even if the path was given as a
    windows path ('c:\foo\bar') in the dotenv file. If the given filed_name is not
    found in the dotenv file, None is returned.
    """
    fixed_lines = []
    with dotenv_file.open(encoding="utf-8", newline="") as f:
        for line in f.read().splitlines():
            if line.lstrip().startswith(fieldname):
                fixed_lines.append(line.replace("\\", "/").replace("//", "/"))
    envdata = dotenv_values(stream=StringIO("\n".join(fixed_lines)))
    return Path(envdata[fieldname]) if fieldname in envdata else None
