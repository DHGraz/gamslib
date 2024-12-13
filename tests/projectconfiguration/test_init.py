import pytest
from gamslib.projectconfiguration import create_configuration


def test_create_configuraton_skeleton(tmp_path):
    create_configuration(tmp_path)
    assert (tmp_path / "project.toml").exists()
    assert "publisher" in (tmp_path / "project.toml").read_text(encoding="utf-8") 

    # A we have created the toml file before, we should get None
    with pytest.warns(UserWarning):
        result = create_configuration(tmp_path) 
        assert result is None
