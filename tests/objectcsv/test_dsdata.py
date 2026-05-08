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
    assert dsdata.dspath == "TEI.xml"
    assert dsdata.dsid == "TEI.xml"
    assert dsdata.title == "The TEI file with üßÄ"
    assert dsdata.description == "A TEI"
    assert dsdata.mimetype == "application/xml"
    assert dsdata.creator == "Foo Bar"
    assert dsdata.rights == "GPLv3"
    assert dsdata.lang == "en; de"
    assert dsdata.tags == "tag1; tag_2; tag-3"


@pytest.mark.parametrize("detector", [MinimalDetector(), MagikaDetector()])
def test_ds_data_guess_missing_values(detector, shared_datadir, monkeypatch):
    "Optional missing values should be added automatically."

    def fake_detect_format(filepath: Path) -> FormatInfo:
        "This fake function allows us to use any format detector."
        nonlocal detector
        return detector.guess_file_type(filepath)

    monkeypatch.setattr(formatdetect, "detect_format", fake_detect_format)
    dsdata = DSData(
        dspath="DC.xml",
        dsid="DC.xml",
        mimetype="application/octet-stream",
        rights="GPLv3",
    )
    dsdata.guess_missing_values(shared_datadir / "obj1")
    assert dsdata.mimetype == "application/octet-stream"
    assert dsdata.title == "XML Dublin Core metadata: DC.xml"
    assert dsdata.description == defaultvalues.FILENAME_MAP["DC.xml"]["description"]

    dsdata = DSData(
        dspath="image.jpeg",
        dsid="image.jpeg",
        mimetype="application/octet-stream",
        rights="GPLv3",
    )
    dsdata.guess_missing_values(shared_datadir / "obj1")
    assert dsdata.mimetype == "application/octet-stream"
    assert dsdata.title == "Image document: image.jpeg"

    dsdata = DSData(
        dspath="json.json",
        dsid="json.json",
        mimetype="application/octet-stream",
        rights="GPLv3",
    )
    dsdata.guess_missing_values(shared_datadir / "obj1")
    assert dsdata.mimetype == "application/octet-stream"
    assert dsdata.title == "JSON document: json.json"

    dsdata = DSData(
        dspath="xml_tei.xml",
        dsid="xml_tei.xml",
        mimetype="application/octet-stream",
        rights="GPLv3",
    )
    dsdata.guess_missing_values(shared_datadir / "obj1")
    assert dsdata.mimetype == "application/octet-stream"
    assert "XML TEI P5 document" in dsdata.title

    dsdata = DSData(
        dspath="xml_lido.xml",
        dsid="xml_lido.xml",
        mimetype="application/octet-stream",
        rights="GPLv3",
    )
    dsdata.guess_missing_values(shared_datadir / "obj1")
    assert dsdata.mimetype == "application/octet-stream"
    assert dsdata.title == "XML LIDO document: xml_lido.xml"

    dsdata = DSData(
        dspath="sound.mp3",
        dsid="sound.mp3",
        mimetype="application/octet-stream",
        rights="GPLv3",
    )
    dsdata.guess_missing_values(shared_datadir / "obj1")
    assert dsdata.mimetype == "application/octet-stream"
    assert dsdata.title == "Audio document: sound.mp3"

    dsdata = DSData(
        dspath="video.mp4",
        dsid="video.mp4",
        mimetype="application/octet-stream",
        rights="GPLv3",
    )
    dsdata.guess_missing_values(shared_datadir / "obj1")
    assert dsdata.mimetype == "application/octet-stream"
    assert dsdata.title == "Video document: video.mp4"

    dsdata = DSData(
        dspath="empty.foo",
        dsid="empty",
        mimetype="application/octet-stream",
        rights="GPLv3",
    )
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
        ("creator", "Old creator", "New creator", "New creator"),
        ("creator", "", "New creator", "New creator"),
        ("creator", "Old creator", "", "Old creator"),
        ("rights", "Old rights", "New rights", "New rights"),
        # description should not be touched
        ("description", "Old description", "New description", "Old description"),
        ("description", "", "New description", ""),
        ("description", "Old description", "", "Old description"),
        # lang should not be touched
        ("lang", "en de", "", "en de"),
        ("lang", "", "en de", ""),
        ("lang", "en de", "de en", "en de"),
        # tags should not be touched
        ("tags", "tag1; tag2", "", "tag1; tag2"),
        ("tags", "", "tag1; tag2", ""),
        ("tags", "tag1; tag2", "tag3; tag4", "tag1; tag2"),
        # dspath and dsid must not change
        ("dspath", "TEI.xml", "TEI2.xml", "ValueError"),
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
    "Should raise immediately if required fields are set to invalid values."
    with pytest.raises(ValueError):
        dsdata.dspath = ""
    assert dsdata.dspath == "TEI.xml"

    with pytest.raises(ValueError):
        dsdata.dsid = ""
    assert dsdata.dsid == "TEI.xml"

    with pytest.raises(ValueError):
        dsdata.mimetype = ""
    assert dsdata.mimetype == "application/xml"

    with pytest.raises(ValueError):
        dsdata.rights = ""
    assert dsdata.rights == "GPLv3"


def test_dsdata_validate_invalid_dspath(dsdata):
    "Should raise immediately if dspath is invalid."
    with pytest.raises(ValueError):
        dsdata.dspath = "../secret.txt"
    assert dsdata.dspath == "TEI.xml"

    with pytest.raises(ValueError):
        dsdata.dspath = "/absolute/path/to/file.txt"
    assert dsdata.dspath == "TEI.xml"

    with pytest.raises(ValueError):
        dsdata.dspath = "C:\\absolute\\windows\\path.txt"
    assert dsdata.dspath == "TEI.xml"

    with pytest.raises(ValueError):
        dsdata.dspath = "\\absolute\\windows\\path.txt"
    assert dsdata.dspath == "TEI.xml"

    with pytest.raises(ValueError):
        dsdata.dspath = "~/file.txt"
    assert dsdata.dspath == "TEI.xml"


def test_dsdata_validate_valid_tags(dsdata):
    "Test tagswith valid tag values"
    dsdata.tags = "tag1; tag_2; tag-3; tag~3; tag.4"
    assert dsdata.validate() is None


@pytest.mark.parametrize(
    "value, msg",
    [
        ("a", "short"),
        ("a" * 51, "exceeds maximum length"),
        ("foo bar", "invalid character"),
        ("foo:bar", "invalid character"),
        ("foo#bar", "invalid character"),
        ("foo/bar", "invalid character"),
        ("foo\\bar", "invalid character"),
    ],
)
def test_dsdata_validate_invalid_tag(value, msg, dsdata):
    "Should raise if tag is invalid."
    with pytest.raises(ValueError, match=msg):
        dsdata.tags = value
        dsdata.validate()
