import shutil
from importlib import resources as impresources
from pathlib import Path

import pytest
from tomlkit import toml_file

from gamslib.projectconfiguration.utils import (
    configuration_needs_update,
    create_project_toml,
    find_project_toml,
    get_config_file_from_env,
    initialize_project_dir,
    read_path_from_dotenv,
    update_configuration,
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


def test_config_needs_update_no_update_needed(tmp_path):
    "Test the config_needs_update function."

    # first we try an identical file
    template_path = (
        impresources.files("gamslib")
        / "projectconfiguration"
        / "resources"
        / "project.toml"
    )
    config_path = tmp_path / "project.toml"
    shutil.copy(template_path, config_path)
    assert not configuration_needs_update(config_path)

    # now we change the order of the keys
    new_lines = []
    buffered = ""
    with open(config_path, "r") as f:
        for line in f.readlines():
            if line.lstrip().startswith("project_id"):
                buffered = line
            elif line.lstrip().startswith("rights"):
                new_lines.append(line)
                new_lines.append(buffered)
            else:
                new_lines.append(line)
    with open(config_path, "w") as f:
        f.writelines(new_lines)
    assert not configuration_needs_update(config_path)


def test_config_needs_update_update_needed(tmp_path):
    """Test the config_needs_update function with different files.

    This means that config_needs_update should always return True.
    """

    template_path = (
        impresources.files("gamslib")
        / "projectconfiguration"
        / "resources"
        / "project.toml"
    )

    # remove the "publisher" key from the template data and store as project.toml
    toml_doc = toml_file.TOMLFile(template_path).read()
    toml_doc["metadata"].remove("publisher")
    config_path = tmp_path / "project.toml"
    toml_file.TOMLFile(config_path).write(toml_doc)
    assert configuration_needs_update(config_path)

    # Now the same with a full table
    toml_doc = toml_file.TOMLFile(template_path).read()
    toml_doc.remove("metadata")
    toml_file.TOMLFile(config_path).write(toml_doc)
    assert configuration_needs_update(config_path)


def test_config_needs_update_no_cfg_file(tmp_path):
    """Test the config_needs_update function with non existing config file.

    This means that config_needs_update should False.
    """
    non_existting_cfg = tmp_path / "project.toml"
    assert not configuration_needs_update(non_existting_cfg)

def test_update_configuration_no_changes(tmp_path):
    """Test the update_configuration function.
    without a need to update the configuration.
    """
    template_path = (
        impresources.files("gamslib")
        / "projectconfiguration"
        / "resources"
        / "project.toml"
    )
    config_path = tmp_path / "project.toml"
    shutil.copy(template_path, config_path)
    update_configuration(config_path)

    template_doc = toml_file.TOMLFile(template_path).read()
    config_doc = toml_file.TOMLFile(config_path).read()
    for key in template_doc:
        assert key in config_doc
        if isinstance(template_doc[key], dict):
            for subkey in template_doc[key]:
                assert subkey in config_doc[key]


def test_update_configuration_with_changes(tmp_path):
    """Test the update_configuration function.
    With a need to update the configuration.
    """
    template_path = (
        impresources.files("gamslib")
        / "projectconfiguration"
        / "resources"
        / "project.toml"
    )
    config_path = tmp_path / "project.toml"
    template_doc = toml_file.TOMLFile(template_path).read()

    # remove some fields and a table from the template
    template_doc["metadata"].remove("publisher")
    template_doc["metadata"].remove("creator")
    template_doc.remove("general")
    # save changed template to config and update
    toml_file.TOMLFile(config_path).write(template_doc)
    update_configuration(config_path)

    # check if the missing fields were added again
    config_doc = toml_file.TOMLFile(config_path).read()
    for key in template_doc:
        assert key in config_doc
        if isinstance(template_doc[key], dict):
            for subkey in template_doc[key]:
                assert subkey in config_doc[key]
