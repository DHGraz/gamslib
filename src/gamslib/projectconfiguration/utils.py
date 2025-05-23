"""Utility function for the projectconfiguration sub module."""

import os
import shutil
import warnings
from importlib import resources as impresources
from io import StringIO
from pathlib import Path

from dotenv import dotenv_values
from tomlkit import toml_file


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


def create_gitignore(project_dir: Path) -> None:
    """Create a .gitignore file in the project_dir directory."""
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
    """Create a project.toml template file in the project_dir directory.

    It is assumed that the project_dir is the root directory of a GAMS project
    and that the directory exists.
    The template file will not be created if a project.toml file already exists.

    Return the path to the created project.toml file or None if the file already exists.
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


def get_config_file_from_env():
    """Tries to extract the path to the config file from the environment.

    The path can either be set in the environment variable 'GAMSCFG_PROJECT_TOML'
    or in the .env file in the current directory ('project_toml =').
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
    """Check if the config file needs to be updated."""

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
    """Update the configuration file with missing entries from config template.

    This function adds new config file entries from the template file to the existing config file.
    Currently it only handles additions, not deletions or changes.
    Existing values in the config file will not be overwritten.
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
