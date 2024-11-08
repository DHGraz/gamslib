"""Tests for the configuration package.
"""

import tomllib

import pytest

from gamslib.projectconfiguration import load_configuration
from gamslib.projectconfiguration.configuration import find_project_toml


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


def test_load_config(datadir):
    "Loadconfig should return a Configuration object."
    cfg = load_configuration(datadir)
    assert cfg.project.metadata.projectname == "Test Project"
    assert cfg.project.metadata.creator == "GAMS Test Project"
    assert cfg.project.metadata.publisher == "GAMS"
    assert "commons" in cfg.project.metadata.rights
    assert cfg.toml_file == datadir / "project.toml"

    # now with an explict toml file (Path)
    cfg_file = datadir / "project.toml"
    cfg = load_configuration(datadir, cfg_file)
    assert cfg.project.metadata.projectname == "Test Project"

    # now with an explict toml file (str)
    cfg = load_configuration(datadir, str(cfg_file))
    assert cfg.project.metadata.projectname == "Test Project"


def tests_load_config_with_explicit_toml(datadir):
    "Test load_config with an explicit TOML file."
    cfg = load_configuration(datadir, datadir / "xxx.toml")
    assert cfg.project.metadata.projectname == "XXX Project"
    assert cfg.project.metadata.creator == "XXX Test Project"
    assert cfg.project.metadata.publisher == "XXX"
    assert cfg.project.metadata.rights == "XXX License"
    assert cfg.toml_file == datadir / "xxx.toml"


def test_load_config_toml_invalid_toml(datadir):
    "An invalid TOML file should raise an error."
    with pytest.raises(tomllib.TOMLDecodeError):
        load_configuration(datadir, datadir / "invalid.toml")


def test_load_config_toml_validation_missing_key(datadir):
    "Test load_config where a required key is missing."

    with pytest.raises(ValueError):
        load_configuration(datadir, datadir / "missing_key.toml")


def test_load_config_toml_validation_required_value(datadir):
    "Check if missing required values are detected."
    ## a required value is missing
    with pytest.raises(ValueError):
        load_configuration(datadir, datadir / "missing_value.toml")
