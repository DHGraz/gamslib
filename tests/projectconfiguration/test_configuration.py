"""Tests for the configuration package."""

import copy
import json
import re
import shutil
from importlib import resources as impresources
from pathlib import Path

import jsonschema
import pytest
import toml
import tomllib

from gamslib.projectconfiguration import load_configuration
from gamslib.projectconfiguration.configuration import (
    Configuration,
    Project,
    find_project_toml,
)


def test_find_project_toml(datadir):
    "Test finding the project.toml file."

    # toml is in datadir
    project_toml = datadir / "project.toml"
    assert find_project_toml(project_toml.parent) == project_toml

    # toml is in a child folder
    assert find_project_toml(datadir / "foo") == project_toml

    # toml is in a child folder of the child folder
    assert find_project_toml(datadir / "foo" / "bar") == project_toml


def test_find_project_toml_current_folder(datadir, tmp_path, monkeypatch):
    "Test finding the project.toml file in the current folder."

    # we switch to datadir, where a project.toml file is located
    monkeypatch.chdir(datadir)
    # there in no project.toml in tmp_path, so the funtion should return the project.toml in datadir
    assert find_project_toml(tmp_path) == datadir / "project.toml"


def test_find_project_toml_not_found(tmp_path):
    "Test finding the project.toml file when it is not found."

    # toml is not in the parent folder
    with pytest.raises(FileNotFoundError):
        find_project_toml(tmp_path / "foo" / "bar" / "baz")


def test_template_matches_schema():
    "Test if the template matches the schema."
    schema_file = (
        impresources.files("gamslib")
        / "projectconfiguration"
        / "resources"
        / "projecttoml_schema.json"
    )
    template_file = (
        impresources.files("gamslib")
        / "projectconfiguration"
        / "resources"
        / "project.toml"
    )
    with schema_file.open(encoding="utf-8", newline="") as schema_file:
        schema = json.load(schema_file)
    with template_file.open("rb") as template_file:
        template = tomllib.load(template_file)

    jsonschema.validate(instance=template, schema=schema)


def test_project_class():
    "Test the Project class."

    project = Project(
        project_id="Test Project",
        creator="GAMS Test Project",
        publisher="GAMS",
        rights="commons",
        dsid_keep_extension=True,
    )

    assert project.project_id == "Test Project"
    assert project.creator == "GAMS Test Project"
    assert project.publisher == "GAMS"
    assert project.rights == "commons"
    assert project.dsid_keep_extension


def test_configuration_init(datadir):
    """Test if the creation of a Configuration object works.

    Here the configuration is loaded from a valid TOML file.
    """
    toml_file = datadir / "project.toml"
    cfg = Configuration(toml_file)
    assert cfg.project.project_id == "Test Project"
    assert cfg.project.creator == "GAMS Test Project"
    assert cfg.project.publisher == "GAMS"
    assert "commons" in cfg.project.rights
    assert cfg.project.dsid_keep_extension
    assert cfg.toml_file == toml_file


def test_configuration_missing_required_keys(datadir):
    "Check if missing required keys are detected."

    def comment_key(toml_file: Path, key: str):
        "Comment out a key in a TOML file."
        new_lines = []
        with toml_file.open("r", encoding="utf-8", newline="") as f:
            for line in f:
                # remove existing comment
                line = re.sub(r"^#\s*", "", line)
                # add comment if key matches
                if re.match(r"^" + key + r"\s*=", line):
                    line = "#" + line
                new_lines.append(line)
        with toml_file.open("w", encoding="utf-8", newline="") as f:
            f.writelines(new_lines)

    toml_file = datadir / "project.toml"

    comment_key(toml_file, "project_id")
    with pytest.raises(ValueError, match=r"'project_id' is a required property"):
        Configuration(toml_file)

    comment_key(toml_file, "creator")
    with pytest.raises(ValueError, match=r"'creator' is a required property"):
        Configuration(toml_file)

    comment_key(toml_file, "publisher")
    with pytest.raises(ValueError, match=r"'publisher' is a required property"):
        Configuration(toml_file)

    comment_key(toml_file, "dsid_keep_extension")
    with pytest.raises(
        ValueError, match=r"'dsid_keep_extension' is a required property"
    ):
        Configuration(toml_file)


def test_configuration_invalid_values(datadir):
    "Check if invalid values are detected."

    def set_value(table: str, field: str, value: str):
        "Replace a value in a TOML file."

        with (datadir / "project.toml").open("rb") as f:
            orig_data = tomllib.load(f)
            test_data = copy.deepcopy(orig_data)
            test_data[table][field] = value
        with test_toml.open("w") as f:
            toml.dump(test_data, f)

    test_toml = datadir / "test.toml"

    set_value("project", "project_id", "")
    with pytest.raises(ValueError, match=r"'' is too short at \[project.project_id\]"):
        Configuration(test_toml)

    set_value("project", "creator", "c")
    with pytest.raises(ValueError, match=r"'c' is too short at \[project.creator\]"):
        Configuration(test_toml)

    set_value("project", "publisher", "pu")
    with pytest.raises(ValueError, match=r"'pu' is too short at \[project.publisher\]"):
        Configuration(test_toml)

    set_value("project", "dsid_keep_extension", "true")
    with pytest.raises(
        ValueError,
        match=r"'true' is not of type 'boolean' at \[project.dsid_keep_extension\]",
    ):
        Configuration(test_toml)


def test_load_configuration(datadir):
    "Loadconfig should return a Configuration object."
    cfg = load_configuration(datadir)
    assert cfg.project.project_id == "Test Project"
    assert cfg.project.creator == "GAMS Test Project"
    assert cfg.project.publisher == "GAMS"
    assert "commons" in cfg.project.rights
    assert cfg.toml_file == datadir / "project.toml"

    # now with an explict toml file (Path)
    cfg_file = datadir / "project.toml"
    cfg = load_configuration(datadir, cfg_file)
    assert cfg.project.project_id == "Test Project"

    # now with an explict toml file (str)
    cfg = load_configuration(datadir, cfg_file)
    assert cfg.project.project_id == "Test Project"


def tests_load_config_with_explicit_toml(datadir, tmp_path):
    "Test load_config with an explicit TOML file."
    old_toml = datadir / "project.toml"
    new_toml = tmp_path / "new.toml"
    shutil.move(old_toml, new_toml)

    cfg = load_configuration(datadir, new_toml)
    assert cfg.project.project_id == "Test Project"
    assert cfg.project.creator == "GAMS Test Project"
    assert cfg.project.publisher == "GAMS"
    assert (
        cfg.project.rights
        == "Creative Commons Attribution-NonCommercial 4.0 (https://creativecommons.org/licenses/by-nc/4.0/)"
    )
    assert cfg.project.dsid_keep_extension
    assert cfg.toml_file == new_toml

def test_load_config_toml_as_str(datadir, tmp_path):
    "Test load_config where TOML file is a string."
    toml_path = datadir / "project.toml"

    cfg = load_configuration(datadir, str(toml_path))
    assert cfg.project.project_id == "Test Project"
    assert cfg.project.creator == "GAMS Test Project"
    assert cfg.project.publisher == "GAMS"
    assert (
        cfg.project.rights
        == "Creative Commons Attribution-NonCommercial 4.0 (https://creativecommons.org/licenses/by-nc/4.0/)"
    )
    assert cfg.project.dsid_keep_extension
    assert cfg.toml_file == toml_path
    

def test_load_config_toml_invalid_toml(datadir):
    "An invalid TOML file should raise an error."
    with pytest.raises(tomllib.TOMLDecodeError):
        load_configuration(datadir, datadir / "invalid.toml")
