from pathlib import Path

import pytest

from gamslib.projectconfiguration.utils import (
    create_project_toml,
    find_project_toml,
    get_config_file_from_env,
    initialize_project_dir,
    read_path_from_dotenv,
)


def test_create_configuraton_skeleton(tmp_path):
    create_project_toml(tmp_path)
    assert (tmp_path / "project.toml").exists()
    assert "publisher" in (tmp_path / "project.toml").read_text(encoding="utf-8")

    # A we have created the toml file before, we should get None
    with pytest.warns(UserWarning):
        result = create_project_toml(tmp_path)
        assert result is None


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


def test_read_path_from_dotenv(datadir):
    """Test the read_path_from_dotenv function.

    This functio should create a Path object from a path string in a dotenv file,
    independet of the notation of the path expressed in .env.
    """
    dotenv_file = datadir / "windotenv"

    # a posix path (/foo/bar)
    result = read_path_from_dotenv(dotenv_file, "posix_path")
    assert result == Path("/foo/bar/project.toml")

    # a posix path with drive letter (c:/foo/bar)
    result = read_path_from_dotenv(dotenv_file, "posix_win_path")
    assert result == Path("c:/foo/bar/project.toml")

    # an escaped windows path (c:\\foo\\bar)
    result = read_path_from_dotenv(dotenv_file, "escaped_win_path")
    assert result == Path("c:/foo/bar/project.toml")

    # a windows path (c:\foo\bar)
    result = read_path_from_dotenv(dotenv_file, "win_path")
    assert result == Path("c:/foo/bar/project.toml")

    # a non existing field
    result = read_path_from_dotenv(dotenv_file, "not_existing")
    assert result is None


def test_initialize_project_dir(tmp_path):
    "Test the initialize_project_dir function."
    initialize_project_dir(tmp_path)
    assert (tmp_path / "project.toml").exists()
    assert (tmp_path / ".gitignore").exists()
    assert (tmp_path / "objects").exists() and (tmp_path / "objects").is_dir()

def test_initialize_project_dir_existing_toml_file(tmp_path):
    "If the project.toml file exists, a warning should be raised."
    (tmp_path / "project.toml").touch()
    with pytest.warns(UserWarning, match="project.toml"):
        initialize_project_dir(tmp_path)

def test_initialize_project_dir_existing_gitignore_file(tmp_path):
    "If the .gitignore file exists, a warning should be raised."
    (tmp_path / ".gitignore").touch()
    with pytest.warns(UserWarning, match=".gitignore"):
        initialize_project_dir(tmp_path)

def test_initialize_project_dir_existing_objects_folder(tmp_path):
    "If the objects folder exists, a warning should be raised."
    (tmp_path / "objects").mkdir()
    with pytest.warns(UserWarning, match="objects"):
        initialize_project_dir(tmp_path)


def test_get_config_file_from_env_environ(monkeypatch, tmp_path):
    "Test the get_config_file_from_env function with path specified in environment."
    config_path = tmp_path / "project.toml"
    monkeypatch.setenv("GAMSCFG_PROJECT_TOML", f"{config_path!s}")
    assert get_config_file_from_env() == config_path

def test_get_config_file_from_env_dotenv(monkeypatch, tmp_path):
    "Test the get_config_file_from_env function with path specified in .env."
    project_path = tmp_path / "project.toml"
    (tmp_path / ".env").write_text(f'project_toml = "{project_path!s}"')
    monkeypatch.chdir(tmp_path)
    assert get_config_file_from_env() == project_path