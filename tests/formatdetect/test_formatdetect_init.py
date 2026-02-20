"""Tests for the __init__ module of the formatdetect sub package."""

from unittest.mock import MagicMock, patch

import pytest
import toml

from gamslib import formatdetect, projectconfiguration
from gamslib.formatdetect import (
    MagikaDetector,
    MinimalDetector,
    make_detector,
)
from gamslib.formatdetect.siegfrieddetector import SiegfriedDetector


@pytest.fixture(name="mock_config")
def mock_config_fixture():
    """Mock the gamslib.formatdetect.config module."""
    with patch("gamslib.formatdetect.config") as mock_cfg:  # pragma: no cover
        yield mock_cfg


@pytest.fixture(name="mock_detector")
def mock_detector_fixture():
    """Mock the gamslib.formatdetect.make_detector function."""
    with patch(
        "gamslib.formatdetect.make_detector"
    ) as mock_make_detector:  # pragma: no cover
        mock_detector_instance = MagicMock()
        mock_make_detector.return_value = mock_detector_instance
        yield mock_detector_instance


def test_make_detector():
    "Test if the correct detector is created based on the name."
    # create the default detector
    detector = make_detector("")
    assert isinstance(detector, SiegfriedDetector)

    detector = make_detector("base")
    assert isinstance(detector, MinimalDetector)

    detector = make_detector("magika")
    assert isinstance(detector, MagikaDetector)

    detector = make_detector("siegfried")
    assert isinstance(detector, SiegfriedDetector)

    # Add more tests when additional detectors are implemented


def test_make_detector_with_invalid_name():
    "If an invalid name is given, a NameError should be raised."
    with pytest.raises(ValueError):
        make_detector("invalid")


def test_detect_format_without_config(lazy_shared_datadir, monkeypatch):
    """If no config exists, the default detector should be used."""

    def mock_get_config():  # pragma: no cover
        raise projectconfiguration.MissingConfigurationException()

    monkeypatch.setattr(projectconfiguration, "get_configuration", mock_get_config)

    formatinfo = formatdetect.detect_format(lazy_shared_datadir / "image.jpg")
    assert formatinfo.detector.startswith("SiegfriedDetector")


def test_detect_format_with_config(lazy_shared_datadir, tmp_path, monkeypatch):
    "If config exists, the detector configured there should be used."
    toml_data = {
        "metadata": {"project_id": "foo", "creator": "bar", "publisher": "baz"},
        "general": {"format_detector": "magika", "format_detector_url": ""},
    }
    tomlfile = tmp_path / "project.toml"
    toml.dump(toml_data, tomlfile.open("w", encoding="utf-8"))
    monkeypatch.setenv("GAMSCFG_PROJECT_TOML", str(tomlfile))
    formatinfo = formatdetect.detect_format(lazy_shared_datadir / "image.jpg")
    assert formatinfo.detector == "MagikaDetector"
