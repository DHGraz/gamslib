from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import coverage
import toml
from unittest import mock as mocker

from gamslib import formatdetect, projectconfiguration
from gamslib.formatdetect import (
    FormatDetector,
    FormatInfo,
    MinimalDetector,
    MagikaDetector,
    detect_format,
    make_detector,
)
from gamslib.formatdetect.magikadetector import MagikaDetector


@pytest.fixture
def mock_config():
    with patch("gamslib.formatdetect.config") as mock_config:  # pragma: no cover
        yield mock_config


@pytest.fixture
def mock_detector():
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
    assert isinstance(detector, MagikaDetector)

    detector = make_detector("base")
    assert isinstance(detector, MinimalDetector)

    detector = make_detector("magika")
    assert isinstance(detector, MagikaDetector)

    # Add more tests when additional detectors are implemented


def test_make_detector_with_invalid_name():
    "If an invalid name is given, a NameError should be raised."
    with pytest.raises(ValueError):
        make_detector("invalid")


def test_detect_format_without_config(formatdatadir, monkeypatch):
    """If no config exists, the default detector should be used."""

    def mock_get_config():  # pragma: no cover
        raise projectconfiguration.MissingConfigurationException()

    monkeypatch.setattr(projectconfiguration, "get_configuration", mock_get_config)

    formatinfo = formatdetect.detect_format(formatdatadir / "image.jpg")
    assert formatinfo.detector == "MagikaDetector"


def test_detect_format_with_config(formatdatadir, tmp_path, monkeypatch):
    "If config exists, the detector configured there should be used."
    toml_data = {
        "metadata": {"project_id": "foo", "creator": "bar", "publisher": "baz"},
        "general": {"format_detector": "magika", "format_detector_url": ""},
    }
    tomlfile = tmp_path / "project.toml"
    toml.dump(toml_data, tomlfile.open("w", encoding="utf-8"))
    monkeypatch.setenv("GAMSCFG_PROJECT_TOML", str(tomlfile))
    formatinfo = formatdetect.detect_format(formatdatadir / "image.jpg")
    assert formatinfo.detector == "MagikaDetector"
