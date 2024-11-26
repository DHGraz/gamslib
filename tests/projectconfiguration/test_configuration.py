"""Tests for the configuration package."""

# pylint: disable=protected-access

import copy
import re
import shutil
import tomllib
from pathlib import Path

import pytest
import toml


from gamslib.projectconfiguration import load_configuration
from gamslib.projectconfiguration.configuration import (
    Configuration,
    General,
    Metadata,
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


def test_metadata_class():
    "Test the Project class."

    metadata = Metadata(
        project_id="Test Project",
        creator="GAMS Test Project",
        publisher="GAMS",
        rights="commons",
    )

    assert metadata.project_id == "Test Project"
    assert metadata.creator == "GAMS Test Project"
    assert metadata.publisher == "GAMS"
    assert metadata.rights == "commons"


def test_general_class():
    "Test cleation of a General object."

    general = General(loglevel="error", dsid_keep_extension=False)
    assert general.dsid_keep_extension is False
    assert general.loglevel == "error"


def test_configuration_from_toml(datadir):
    """Test if the creation of a Configuration object works.

    Here the configuration is loaded from a valid TOML file.
    """
    toml_file = datadir / "project.toml"
    cfg = Configuration.from_toml(toml_file)

    assert cfg.toml_file == toml_file

    assert cfg.metadata.project_id == "Test Project"
    assert cfg.metadata.creator == "GAMS Test Project"
    assert cfg.metadata.publisher == "GAMS"
    assert "commons" in cfg.metadata.rights

    assert cfg.general.loglevel == "info"
    assert cfg.general.dsid_keep_extension


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
    with pytest.raises(
        ValueError, match=r"missing required field: 'metadata.project_id'"
    ):
        Configuration.from_toml(toml_file)

    comment_key(toml_file, "creator")
    with pytest.raises(ValueError, match=r"missing required field: 'metadata.creator'"):
        Configuration.from_toml(toml_file)

    comment_key(toml_file, "publisher")
    with pytest.raises(
        ValueError, match=r"missing required field: 'metadata.publisher'"
    ):
        Configuration.from_toml(toml_file)


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

    set_value("metadata", "project_id", "")
    with pytest.raises(ValueError, match=r"value is too short: 'metadata.project_id'"):
        Configuration.from_toml(test_toml)

    set_value("metadata", "creator", "c")
    with pytest.raises(ValueError, match=r"value is too short: 'metadata.creator'"):
        Configuration.from_toml(test_toml)

    set_value("metadata", "publisher", "pu")
    with pytest.raises(ValueError, match=r"value is too short: 'metadata.publisher'"):
        Configuration.from_toml(test_toml)

    set_value("general", "dsid_keep_extension", 123)
    with pytest.raises(
        ValueError, match=r"value is not a boolean: 'general.dsid_keep_extension'"
    ):
        Configuration.from_toml(test_toml)

    set_value("general", "loglevel", "foo")

    with pytest.raises(
        ValueError,
        match=r"value is not allowed here: 'general.loglevel'",
    ):
        Configuration.from_toml(test_toml)


def test_configuration_make_readable_message():
    "Test the _make_readable_message function."

    cfgfile = Path("test.toml")

    assert Configuration._make_readable_message(
        cfgfile, "missing", ("metadata", "project_id")
    ) == (
        "Error in project TOML file 'test.toml'. missing required field: 'metadata.project_id'"
    )

    assert Configuration._make_readable_message(
        cfgfile, "string_too_short", ("metadata", "creator")
    ) == (
        "Error in project TOML file 'test.toml'. value is too short: 'metadata.creator'"
    )

    assert Configuration._make_readable_message(
        cfgfile, "bool_type", ("general", "dsid_keep_extension")
    ) == (
        "Error in project TOML file 'test.toml'. value is "
        "not a boolean: 'general.dsid_keep_extension'"
    )

    assert Configuration._make_readable_message(
        cfgfile, "bool_parsing", ("general", "dsid_keep_extension")
    ) == (
        "Error in project TOML file 'test.toml'. value is "
        "not a boolean: 'general.dsid_keep_extension'"
    )

    assert Configuration._make_readable_message(
        cfgfile, "literal_error", ("general", "loglevel")
    ) == (
        "Error in project TOML file 'test.toml'. value is "
        "not allowed here: 'general.loglevel'"
    )

    assert (
        Configuration._make_readable_message(cfgfile, "foo", ("general", "loglevel"))
        is None
    )


def test_load_configuration(datadir):
    "Loadconfig should return a Configuration object."
    cfg = load_configuration(datadir)
    assert cfg.metadata.project_id == "Test Project"
    assert cfg.metadata.creator == "GAMS Test Project"
    assert cfg.metadata.publisher == "GAMS"
    assert "commons" in cfg.metadata.rights
    assert cfg.toml_file == datadir / "project.toml"

    # now with an explict toml file (Path)
    cfg_file = datadir / "project.toml"
    cfg = load_configuration(datadir, cfg_file)
    assert cfg.metadata.project_id == "Test Project"

    # now with an explict toml file (str)
    cfg = load_configuration(datadir, cfg_file)
    assert cfg.metadata.project_id == "Test Project"


def tests_load_config_with_explicit_toml(datadir, tmp_path):
    "Test load_config with an explicit TOML file."
    old_toml = datadir / "project.toml"
    new_toml = tmp_path / "new.toml"
    shutil.move(old_toml, new_toml)

    cfg = load_configuration(datadir, new_toml)
    assert cfg.metadata.project_id == "Test Project"
    assert cfg.metadata.creator == "GAMS Test Project"
    assert cfg.metadata.publisher == "GAMS"
    assert cfg.metadata.rights == (
        "Creative Commons Attribution-NonCommercial 4.0 "
        "(https://creativecommons.org/licenses/by-nc/4.0/)"
    )
    assert cfg.general.dsid_keep_extension
    assert cfg.general.loglevel == "info"
    assert cfg.toml_file == new_toml


def test_load_config_toml_as_str(datadir):
    "Test load_config where TOML file is a string."
    toml_path = datadir / "project.toml"

    cfg = load_configuration(datadir, str(toml_path))
    assert cfg.metadata.project_id == "Test Project"
    assert cfg.metadata.creator == "GAMS Test Project"
    assert cfg.metadata.publisher == "GAMS"
    assert cfg.metadata.rights == (
        "Creative Commons Attribution-NonCommercial 4.0 "
        "(https://creativecommons.org/licenses/by-nc/4.0/)"
    )
    assert cfg.general.dsid_keep_extension
    assert cfg.toml_file == toml_path


def test_load_config_toml_invalid_toml(datadir):
    "An invalid TOML file should raise an error."
    with pytest.raises(tomllib.TOMLDecodeError):
        load_configuration(datadir, datadir / "invalid.toml")


def test_changin_values(datadir):
    """Can we assign values to the configuration object?

    Does validation work for those values?
    """
    cfg = Configuration.from_toml(datadir / "project.toml")
    cfg.general.loglevel = "error"
    assert cfg.general.loglevel == "error"

    # now an invalid value
    with pytest.raises(ValueError):
        cfg.general.loglevel = "foo"
