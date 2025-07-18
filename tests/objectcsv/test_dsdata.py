"""
Test the DSData class."""

import copy
from pathlib import Path

import pytest

from gamslib import formatdetect
from gamslib.formatdetect.formatinfo import FormatInfo
from gamslib.formatdetect.magikadetector import MagikaDetector
from gamslib.formatdetect.minimaldetector import MinimalDetector
from gamslib.objectcsv import defaultvalues
from gamslib.objectcsv.dsdata import DSData


def test_dsdata_creation(dsdata):
    "Should create a DSData object."
    assert dsdata.dspath == "obj1/TEI.xml"
    assert dsdata.dsid == "TEI.xml"
    assert dsdata.title == "The TEI file with üßÄ"
    assert dsdata.description == "A TEI"
    assert dsdata.mimetype == "application/xml"
    assert dsdata.creator == "Foo Bar"
    assert dsdata.rights == "GPLv3"
    assert dsdata.lang == "en; de"
    assert dsdata.tags == "tag 1, tag 2, tag 3"

    assert dsdata.object_id == "obj1"


@pytest.mark.parametrize("detector", [MinimalDetector(), MagikaDetector()])
def test_ds_data_guess_missing_values(detector, shared_datadir, monkeypatch):
    "Missing values should be added automatically."

    def fake_detect_format(filepath: Path) -> FormatInfo:
        "This fake function allows us to use any format detector."
        nonlocal detector
        return detector.guess_file_type(filepath)

    monkeypatch.setattr(formatdetect, "detect_format", fake_detect_format)
    dsdata = DSData(dspath="obj1/DC.xml", dsid="DC.xml")
    dsdata.guess_missing_values(shared_datadir / "obj1")
    assert dsdata.mimetype == "application/xml"
    assert dsdata.title == "XML Dublin Core metadata: DC.xml"
    assert dsdata.description == defaultvalues.FILENAME_MAP["DC.xml"]["description"]

    dsdata = DSData(dspath="obj1/image.jpeg", dsid="image.jpeg")
    dsdata.guess_missing_values(shared_datadir / "obj1")
    assert dsdata.mimetype == "image/jpeg"
    assert dsdata.title == "Image document: image.jpeg"

    dsdata = DSData(dspath="obj1/json.json", dsid="json.json")
    dsdata.guess_missing_values(shared_datadir / "obj1")
    assert dsdata.mimetype == "application/json"
    assert dsdata.title == "JSON document: json.json"

    dsdata = DSData(dspath="obj1/xml_tei.xml", dsid="xml_tei.xml")
    dsdata.guess_missing_values(shared_datadir / "obj1")
    assert dsdata.mimetype == "application/tei+xml"
    assert "XML TEI document" in dsdata.title

    dsdata = DSData(dspath="obj1/xml_lido.xml", dsid="xml_lido.xml")
    dsdata.guess_missing_values(shared_datadir / "obj1")
    assert dsdata.mimetype == "application/xml"
    assert dsdata.title == "XML LIDO document: xml_lido.xml"

    dsdata = DSData(dspath="obj1/sound.mp3", dsid="sound.mp3")
    dsdata.guess_missing_values(shared_datadir / "obj1")
    assert dsdata.mimetype == "audio/mpeg"
    assert dsdata.title == "Audio document: sound.mp3"

    dsdata = DSData(dspath="obj1/video.mp4", dsid="video.mp4")
    dsdata.guess_missing_values(shared_datadir / "obj1")
    assert dsdata.mimetype == "video/mp4"
    assert dsdata.title == "Video document: video.mp4"

    dsdata = DSData(dspath="obj1/empty.foo", dsid="empty")
    with pytest.warns(UserWarning):
        dsdata.guess_missing_values(shared_datadir / "obj1")
        assert dsdata.mimetype == "application/octet-stream"
        assert dsdata.title == "Binary document: empty"


@pytest.mark.parametrize(
    "fieldname, old_value, new_value, expected_value",
    [
        ("title", "Old title", "New title", "New title"),
        ("title", "", "New title", "New title"),
        ("title", "Old title", "", "Old title"),
        ("mimetype", "Old mimetype", "New mimetype", "New mimetype"),
        ("mimetype", "", "New mimetype", "New mimetype"),
        ("mimetype", "Old mimetype", "", "Old mimetype"),
        ("creator", "Old creator", "New creator", "New creator"),
        ("creator", "", "New creator", "New creator"),
        ("creator", "Old creator", "", "Old creator"),
        ("rights", "Old rights", "New rights", "New rights"),
        ("rights", "", "New rights", "New rights"),
        ("rights", "Old rights", "", "Old rights"),
        # description should not be touched
        ("description", "Old description", "New description", "Old description"),
        ("description", "", "New description", ""),
        ("description", "Old description", "", "Old description"),
        # lang should not be touched
        ("lang", "en de", "", "en de"),
        ("lang", "", "en de", ""),
        ("lang", "en de", "de en", "en de"),
        # tags should not be touched
        ("tags", "tag1 tag2", "", "tag1 tag2"),
        ("tags", "", "tag1 tag2", ""),
        ("tags", "tag1 tag2", "tag3 tag4", "tag1 tag2"),
        # dspath and dsid must not change
        ("dspath", "obj1/TEI.xml", "obj2/TEI.xml", "ValueError"),
        ("dsid", "TEI.xml", "TEI2.xml", "ValueError"),
    ],
)
def test_merge(dsdata, fieldname, old_value, new_value, expected_value):
    "Test merge with many combinations of values"

    new_dsdata = copy.deepcopy(dsdata)
    setattr(dsdata, fieldname, old_value)
    setattr(new_dsdata, fieldname, new_value)
    if expected_value == "ValueError":
        with pytest.raises(ValueError):
            dsdata.merge(new_dsdata)
    else:
        dsdata.merge(new_dsdata)
        assert getattr(dsdata, fieldname) == expected_value


def test_dsdata_validate(dsdata):
    "Should raise an exception if required fields are missing."
    dsdata.dspath = ""
    with pytest.raises(ValueError):
        dsdata.validate()
    dsdata.dspath = "obj1/TEI.xml"
    dsdata.dsid = ""
    with pytest.raises(ValueError):
        dsdata.validate()
    dsdata.dsid = "TEI.xml"
    dsdata.mimetype = ""
    with pytest.raises(ValueError):
        dsdata.validate()
    dsdata.mimetype = "application/xml"
    dsdata.rights = ""
    with pytest.raises(ValueError):
        dsdata.validate()
