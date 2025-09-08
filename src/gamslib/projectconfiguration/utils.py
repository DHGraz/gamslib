"""Utility functions for the projectconfiguration sub module."""

import os
import shutil
import warnings
from importlib import resources as impresources
from io import StringIO
from pathlib import Path

from dotenv import dotenv_values
from tomlkit import toml_file


def find_project_toml(start_dir: Path) -> Path:
    """
    Search for a 'project.toml' file starting from the given directory and moving upwards.

    Args:
        start_dir (Path): The directory to begin the search.

    Returns:
        Path: The path to the first 'project.toml' file found.

    Raises:
        FileNotFoundError: If no 'project.toml' file is found in the start_dir, its parents, or the current working directory.

    The function checks each parent directory of start_dir for a 'project.toml' file.
    If none is found, it checks the current working directory as a fallback.
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


def create_gitignore(project_dir: Path) -> None:
    """
    Create a '.gitignore' file in the specified project directory.

    If a '.gitignore' file already exists in the directory, a warning is issued and the file is not overwritten.
    Otherwise, a template '.gitignore' is copied from the package resources to the project directory.

    Args:
        project_dir (Path): The target directory for the '.gitignore' file.

    Raises:
        UserWarning: If the '.gitignore' file already exists and will not be recreated.
    """
    gitignore_target = project_dir / ".gitignore"
    if gitignore_target.exists():
        warnings.warn(
            f"'{gitignore_target}' already exists. Will not be re-created.", UserWarning
        )
    else:
        gitignore_src = (
            impresources.files("gamslib")
            / "projectconfiguration"
            / "resources"
            / "gitignore"
        )
        shutil.copy(gitignore_src, gitignore_target)


def create_project_toml(project_dir: Path) -> None:
    """
    Create a template 'project.toml' file in the specified project directory.

    If a 'project.toml' file already exists in the directory, a warning is issued and the file is not overwritten.
    Otherwise, a template file is copied from the package resources to the project directory.

    Args:
        project_dir (Path): The target directory for the 'project.toml' file.

    Returns:
        None

    Raises:
        UserWarning: If the 'project.toml' file already exists and will not be recreated.
    """
    toml_file_ = project_dir / "project.toml"
    if toml_file_.exists():
        warnings.warn(
            f"'{toml_file_}' already exists. Will not be re-created.", UserWarning
        )
    else:
        toml_template_file = str(
            impresources.files("gamslib")
            / "projectconfiguration"
            / "resources"
            / "project.toml"
        )
        shutil.copy(toml_template_file, toml_file_)


def initialize_project_dir(project_dir: Path) -> None:
    """Initialize a GAMS project directory.

    Create a skeleton project.toml file and a .gitignore file in the project_dir directory.
    Also creates a directory 'objects' in the project_dir directory.
    """
    create_project_toml(project_dir)
    create_gitignore(project_dir)

    obj_dir = project_dir / "objects"
    if not obj_dir.exists():
        obj_dir.mkdir()
    else:
        warnings.warn(
            f"'{obj_dir}' already exists. Will not be re-created.", UserWarning
        )


def read_path_from_dotenv(dotenv_file: Path, fieldname: str) -> Path | None:
    """
    Read and normalize a path value from a dotenv file.

    This function searches for the specified field name in the dotenv file and returns its value as a Path object.
    Windows-style backslashes are converted to forward slashes for cross-platform compatibility.
    If the field is not found, returns None.

    Args:
        dotenv_file (Path): Path to the dotenv file.
        fieldname (str): Name of the field to search for.

    Returns:
        Path | None: The normalized path value if found, otherwise None.
    """
    if not dotenv_file.is_file():
        return None

    fixed_lines = []
    with dotenv_file.open(encoding="utf-8", newline="") as f:
        for line in f.read().splitlines():
            # Only process lines that start with the field name (ignoring leading whitespace)
            if line.lstrip().startswith(fieldname):
                # Normalize Windows paths to POSIX style
                normalized_line = line.replace("\\", "/").replace("//", "/")
                fixed_lines.append(normalized_line)
    if not fixed_lines:
        return None

    envdata = dotenv_values(stream=StringIO("\n".join(fixed_lines)))
    value = envdata.get(fieldname)
    return Path(value) if value else None


def get_config_file_from_env() -> Path | None:
    """
    Retrieve the path to the project configuration file from environment sources.

    The function checks for the configuration file path in the following order:

      1. The 'GAMSCFG_PROJECT_TOML' environment variable.
      2. The 'project_toml' field in a '.env' file located in the current working directory.

    Returns:
        Path | None: The path to the configuration file if found, otherwise None.

    Note:
        If neither source provides a path, the function returns None.
    """
    if "GAMSCFG_PROJECT_TOML" in os.environ:
        config_path = Path(os.environ["GAMSCFG_PROJECT_TOML"])
    else:
        dotenv_file = Path.cwd() / ".env"
        # read_config_path_from_dotenv(dotenv_file)
        if dotenv_file.is_file():
            config_path = read_path_from_dotenv(dotenv_file, "project_toml")
        else:
            config_path = None
    return config_path


def configuration_needs_update(config_file: Path) -> bool:
    """
    Check if the given configuration file is missing required keys compared to the template.

    This function compares the structure of the provided config file against the template 'project.toml'
    included with the package. It returns True if any required keys from the template are missing in the
    config file, and False if all required keys are present.

    Args:
        config_file (Path): Path to the configuration file to check.

    Returns:
        bool: True if the config file is missing keys and needs to be updated, False otherwise.

    Notes:
        - Only missing keys are detected; extra keys or differing values are ignored.
        - If the config file does not exist, returns False.
        - Nested keys are checked recursively.
    """

    def deep_compare(real_doc, template_doc):
        "Return True if both configurations contain the same keys."
        for key, value in template_doc.items():
            if key not in real_doc:
                return False
            if isinstance(value, dict):
                return deep_compare(real_doc[key], value)
        return True

    # nothing to compare
    if not config_file.exists():
        return False

    template_file = (
        impresources.files("gamslib")
        / "projectconfiguration"
        / "resources"
        / "project.toml"
    )

    config_toml_file = toml_file.TOMLFile(config_file)
    config_toml_document = config_toml_file.read()
    template_toml_document = toml_file.TOMLFile(template_file).read()

    return not deep_compare(config_toml_document, template_toml_document)


def update_configuration(config_file: Path):
    """
    Update the configuration file by adding missing entries from the template.

    Compares the provided config file to the template 'project.toml' included with the package.
    Any keys present in the template but missing from the config file are added, preserving existing values and comments.
    The function does not remove or modify existing entries—only additions are handled.

    A backup of the original config file is created before any changes are made.

    Args:
        config_file (Path): Path to the configuration file to update.

    Notes:
        - Only missing keys are added; existing values are not overwritten.
        - Comments and formatting in the config file are preserved.
        - The original config file is backed up as '<filename>.bak' in the same directory.
    """

    def deep_update(real_doc, template_doc):
        for key, value in template_doc.items():
            if key not in real_doc:
                real_doc.add(key, value)
            elif isinstance(value, dict):
                if not key in real_doc:
                    real_doc.add(key, value)  # pragma: no cover
                else:
                    deep_update(real_doc[key], value)

    template_file = (
        impresources.files("gamslib")
        / "projectconfiguration"
        / "resources"
        / "project.toml"
    )

    # make a backup of the current config file
    backup_file = config_file.parent / f"{config_file.name}.bak"
    shutil.copy(config_file, backup_file)

    # parse the two files using tomlkit (keeps the comments)
    config_toml_file = toml_file.TOMLFile(config_file)
    config_toml_document = config_toml_file.read()
    template_toml_document = toml_file.TOMLFile(template_file).read()

    deep_update(config_toml_document, template_toml_document)

    config_toml_file.write(config_toml_document)
