import pytest
from gamslib.projectconfiguration.utils import create_configuration, find_project_toml


def test_create_configuraton_skeleton(tmp_path):
    create_configuration(tmp_path)
    assert (tmp_path / "project.toml").exists()
    assert "publisher" in (tmp_path / "project.toml").read_text(encoding="utf-8") 

    # A we have created the toml file before, we should get None
    with pytest.warns(UserWarning):
        result = create_configuration(tmp_path) 
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
