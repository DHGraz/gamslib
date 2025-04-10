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
    assert dsdata.lang == "en de"


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
    assert dsdata.title == defaultvalues.FILENAME_MAP["DC.xml"]["title"]
    assert dsdata.description == defaultvalues.FILENAME_MAP["DC.xml"]["description"]

    dsdata = DSData(dspath="obj1/image.jpeg", dsid="image.jpeg")
    dsdata.guess_missing_values(shared_datadir / "obj1")
    assert dsdata.mimetype == "image/jpeg"
    assert dsdata.title == "Image: image.jpeg"

    dsdata = DSData(dspath="obj1/json.json", dsid="json.json")
    dsdata.guess_missing_values(shared_datadir / "obj1")
    assert dsdata.mimetype == "application/json"
    assert dsdata.title == ""

    dsdata = DSData(dspath="obj1/xml_tei.xml", dsid="xml_tei.xml")
    dsdata.guess_missing_values(shared_datadir / "obj1")
    assert dsdata.mimetype == "application/tei+xml"
    assert "Georg Hönel" in dsdata.title

    dsdata = DSData(dspath="obj1/xml_lido.xml", dsid="xml_lido.xml")
    dsdata.guess_missing_values(shared_datadir / "obj1")
    assert dsdata.mimetype == "application/xml"
    assert dsdata.title == "Bratspieß"

    dsdata = DSData(dspath="obj1/sound.mp3", dsid="sound.mp3")
    dsdata.guess_missing_values(shared_datadir / "obj1")
    assert dsdata.mimetype == "audio/mpeg"
    assert dsdata.title == "Audio: sound.mp3"

    dsdata = DSData(dspath="obj1/video.mp4", dsid="video.mp4")
    dsdata.guess_missing_values(shared_datadir / "obj1")
    assert dsdata.mimetype == "video/mp4"
    assert dsdata.title == "Video: video.mp4"

    dsdata = DSData(dspath="obj1/empty.foo", dsid="empty")
    with pytest.warns(UserWarning):
        dsdata.guess_missing_values(shared_datadir / "obj1")
        assert dsdata.mimetype == "application/octet-stream"
        assert dsdata.title == ""


def test_merge(dsdata):
    "Should merge two DSData objects."
    # add data which is normally added manually in the csv file
    dsdata.description = "The description"
    dsdata.tags = "tag1 tag2"
    dsdata.lang = "en de"

    # clone and change some values
    updated_dsdata = copy.deepcopy(dsdata)
    updated_dsdata.title = "Updated title"
    updated_dsdata.description = ""
    updated_dsdata.mimetype = "application/json"
    updated_dsdata.creator = "Updated creator"
    updated_dsdata.rights = "Updated rights"
    # lang an tags should not be changed as they are set manually
    updated_dsdata.lang = ""
    updated_dsdata.tags = ""

    dsdata.merge(updated_dsdata)

    assert dsdata.title == "Updated title"
    assert dsdata.description == "The description"
    assert dsdata.mimetype == "application/json"
    assert dsdata.creator == "Updated creator"
    assert dsdata.rights == "Updated rights"
    assert dsdata.lang == "en de"
    assert dsdata.tags == "tag1 tag2"
    assert dsdata.lang == "en de"


def test_merge_do_not_overwrite(dsdata):
    "If other_dsdata has empty values, do not overwrite the current values."
    # add data which is normally added manually in the csv file
    dsdata.description = "The description"
    dsdata.tags = "tag1 tag2"
    dsdata.lang = "en de"

    dsdata_original = copy.deepcopy(dsdata) # for comparision

    # clone and change some values
    updated_dsdata = copy.deepcopy(dsdata)
    updated_dsdata.title = ""
    updated_dsdata.description = ""
    updated_dsdata.mimetype = ""
    updated_dsdata.creator = ""
    updated_dsdata.rights = ""
    # lang an tags should not be changed as they are set manually
    updated_dsdata.lang = ""
    updated_dsdata.tags = ""

    dsdata.merge(updated_dsdata)

    assert dsdata.title == dsdata_original.title
    assert dsdata.description == dsdata_original.description
    assert dsdata.mimetype == dsdata_original.mimetype
    assert dsdata.creator == dsdata_original.creator
    assert dsdata.rights == dsdata_original.rights
    assert dsdata.lang == dsdata_original.lang
    assert dsdata.tags == dsdata_original.tags
    assert dsdata.lang == dsdata_original.lang

def test_merge_different_dspaths():
    "Should raise an exception if dspaths are different."
    dsdata = DSData(dspath="obj1", dsid="TEI.xml")
    updated_dsdata = DSData(dspath="obj2", dsid="TEI.xml")
    with pytest.raises(ValueError):
        dsdata.merge(updated_dsdata)

def test_merge_different_dsid():
    "Should raise an exception if dsids are different."
    dsdata = DSData(dspath="obj1", dsid="TEI.xml")
    updated_dsdata = DSData(dspath="obj1", dsid="TEI2.xml")
    with pytest.raises(ValueError):
        dsdata.merge(updated_dsdata)

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
