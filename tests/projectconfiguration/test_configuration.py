"""Tests for the configuration package."""

# pylint: disable=protected-access

import copy
import os
import re
import shutil
import tomllib
from pathlib import Path

import pytest
import toml

from gamslib.projectconfiguration.configuration import Configuration, General, Metadata


@pytest.fixture(name="configobj")
def fixture_configobj(datadir):
    "Return a Configuration object."
    toml_path = datadir / "project.toml"
    general = General(loglevel="error", dsid_keep_extension=False)
    metadata = Metadata(
        project_id="Test Project",
        creator="GAMS Test Project",
        publisher="GAMS",
        rights="commons",
    )
    return Configuration(toml_file=toml_path, metadata=metadata, general=general)


def test_metadata_class():
    "Test the Project class."

    metadata = Metadata(
        project_id="Test Project",
        creator="GAMS Test Project",
        publisher="GAMS",
        rights="commons",
        funder="FUNDER"
    )

    assert metadata.project_id == "Test Project"
    assert metadata.creator == "GAMS Test Project"
    assert metadata.publisher == "GAMS"
    assert metadata.rights == "commons"
    assert metadata.funder == "FUNDER"


def test_general_class():
    "Test cleation of a General object."

    general = General(loglevel="error", dsid_keep_extension=False)
    assert general.dsid_keep_extension is False
    assert general.loglevel == "error"
    assert general.format_detector == "magika"
    assert general.format_detector_url == ""
    assert general.ds_ignore_files == []


def test_configuration_class_creation(configobj, datadir):
    "Test creation of a Configuration object."
    assert configobj.toml_file == datadir / "project.toml"


def test_configclass_update_from_dotenv(datadir, tmp_path, monkeypatch):
    "Test creation of a Configuration object with existing dotenv file."
    dotenv_file = tmp_path / ".env"
    dotenv_file.write_text("general.loglevel = 'debug'\nmetadata.project_id = 'foo'\n")
    monkeypatch.chdir(tmp_path)
    configobj = Configuration.from_toml(datadir / "project.toml")

    assert configobj.general.loglevel == "debug"
    assert configobj.metadata.project_id == "foo"


def test_configclass_update_from_env(datadir, tmp_path, monkeypatch):
    """Test creation of a Configuration object using environment variables.

    We also check if ENV values override .env values
    """
    monkeypatch.setenv("GAMSCFG_GENERAL_LOGLEVEL", "info")
    monkeypatch.setenv("GAMSCFG_METADATA_PROJECT_ID", "bar")

    dotenv_file = tmp_path / ".env"
    dotenv_file.write_text("general.loglevel = 'debug'\nmetadata.project_id = 'foo'\n")
    monkeypatch.chdir(tmp_path)

    configobj = Configuration.from_toml(datadir / "project.toml")

    assert configobj.general.loglevel == "info"
    assert configobj.metadata.project_id == "bar"


def test_configobject_update_value(datadir, tmp_path, monkeypatch):
    "Make sure we cannot circumvent the pydantic validation"
    dotenv_file = tmp_path / ".env"
    dotenv_file.write_text("general.loglevel = 'foo'\nmetadata.project_id = ''\n")
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError):
        configobj = Configuration.from_toml(datadir / "project.toml")


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
    assert cfg.metadata.funder == "DFG"
    assert "commons" in cfg.metadata.rights

    assert cfg.general.loglevel == "info"
    assert cfg.general.dsid_keep_extension


def test_configuration_from_toml_cfg_file_not_found(tmp_path):
    "Customized FileNotFoundError is raised if TOML file does not exist."
    toml_file = tmp_path / "project.toml"
    with pytest.raises(FileNotFoundError, match=r"Configuration file .* not found"):
        Configuration.from_toml(toml_file)


def test_configuration_from_toml_invalid_toml_value(datadir):
    "An invalid TOML file value should raise an ValueError."
    with pytest.raises(ValueError, match=r"Error in project TOML file .*"):
        Configuration.from_toml(datadir / "invalid_value.toml")


def test_configuration_from_toml_invalid_toml(datadir):
    "An invalid TOML file should raise an error."
    with pytest.raises(tomllib.TOMLDecodeError, match=r"Error in project TOML file .*"):
        Configuration.from_toml(datadir / "invalid.toml")

def test_configuration_missing_required_keys(datadir):
    "Check if missing required keys are detected."

    def comment_key(toml_file: Path, key: str):
        "Comment out a key in a TOML file."
        new_lines = []
        with toml_file.open("r", encoding="utf-8", newline="") as f:
            for line in f:
                # remove existing comment
                clean_line = re.sub(r"^#\s*", "", line)
                # add comment if key matches
                if re.match(r"^" + key + r"\s*=", clean_line):
                    clean_line = "#" + line
                new_lines.append(clean_line)
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


def test_changing_values(datadir):
    """Can we assign values to the configuration object?

    Does validation work for those values?
    """
    cfg = Configuration.from_toml(datadir / "project.toml")
    cfg.general.loglevel = "error"
    assert cfg.general.loglevel == "error"

    # now an invalid value
    with pytest.raises(ValueError):
        cfg.general.loglevel = "foo"
