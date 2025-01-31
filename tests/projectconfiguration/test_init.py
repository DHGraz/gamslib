import pytest
from gamslib.projectconfiguration import MissingConfigurationException, get_configuration
import os


def test_get_configuration_no_toml():
    "Calling get_configuration without a TOML file should raise an error."
    get_configuration.cache_clear()  # otherwise w might have side effects from other tests
    with pytest.raises(MissingConfigurationException):
        get_configuration()


def test_get_configuration(datadir):
    "Now we set the toml file via parameter."
    config = get_configuration(datadir / "project.toml")
    assert config.metadata.project_id == "Test Project"
    assert config.general.dsid_keep_extension


def test_get_configuration_env(datadir, monkeypatch):
    "Now we set the toml file via environment variable."
    monkeypatch.setenv("GAMSCFG_PROJECT_TOML", str(datadir / "project.toml"))
    get_configuration.cache_clear()  # otherwise w might have side effects from other tests
    config = get_configuration()
    assert config.metadata.project_id == "Test Project"
    assert config.general.dsid_keep_extension


def test_get_configuration_dotenv(datadir, tmp_path, monkeypatch):
    "Now we set the path to project.toml file via .env value."
    dotenv_file = tmp_path / ".env"
    toml_file = (datadir / "project.toml")
    dotenv_file.write_text(f'project_toml = "{toml_file}"\n')
    monkeypatch.chdir(tmp_path)
    get_configuration.cache_clear()  # otherwise we might have side effects from other tests
    config = get_configuration()
    assert config.metadata.project_id == "Test Project"
    assert config.general.dsid_keep_extension


def test_get_configuration_is_cached(datadir):
    "Check if multiple calls to get_configuration return the same object."
    config1 = get_configuration(datadir / "project.toml")
    config2 = get_configuration(datadir / "project.toml")
    assert config1 is config2

