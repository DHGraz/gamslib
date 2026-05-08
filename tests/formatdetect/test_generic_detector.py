"""Runs detector against files to make sure, that formats are detected correctly.

These tests only use additional files from the validation tests, as the files
from the formatdetect package are already tested in the formatdetect.detector tests.

I added this to facilitate identifying problems with validation files.
"""

import pytest

from gamslib.formatdetect import FormatDetector, detect_format
from gamslib.formatdetect.magikadetector import MagikaDetector
from gamslib.formatdetect.minimaldetector import MinimalDetector
from gamslib.formatdetect.siegfrieddetector import SiegfriedDetector

from conftest import get_testfiles_from_validation

@pytest.mark.parametrize("detector", [
    SiegfriedDetector(),
    MagikaDetector(),
    MinimalDetector(),
    ], ids=lambda x: x.__class__.__name__)
@pytest.mark.parametrize("testfile", get_testfiles_from_validation(), ids=lambda x: x.filepath.name)
@pytest.mark.filterwarnings("ignore:Could not determine mimetype")
def test_with_validation_files(detector, testfile, monkeypatch):
    """Test format detection for the files in validation/data using siegfried."""
    monkeypatch.setattr("gamslib.formatdetect.make_detector", lambda *args: detector)
    if testfile.filepath.name == "minimal_not_wellformed.xml":
        # with pytest.warns(UserWarning), pytest.raises(Exception):
        with pytest.raises(Exception):
            detect_format(testfile.filepath)
    else:
        format_info = detect_format(testfile.filepath)
        assert format_info.mimetype == testfile.mimetype
        assert format_info.subtype == testfile.subtype
        if isinstance(detector, SiegfriedDetector): # only Siegfried sets pronom_id
            assert format_info.pronom_id == testfile.pronom_id


def test_has_xml_declaration(lazy_shared_datadir):
    "Test is missing xml declaration is correctly detected."
    assert FormatDetector.has_xml_declaration(lazy_shared_datadir / "xml_dc.xml")
    assert not FormatDetector.has_xml_declaration(lazy_shared_datadir / "xml_dc_no_decl.xml")


@pytest.mark.parametrize("testfile, expected", [
    ("xml_dc.xml", True),
    ("xml_dc_no_decl.xml", True),
    ("text.txt", False),
    ("tar_gz.tgz", False),
    ("pdf.pdf", False),
    ("json.json", False),
    ("image.jpeg", False),
])#, ids=lambda x: x.filepath.name)
def test_looks_like_xml(testfile, expected, lazy_shared_datadir):
    "Test if looks_like_xml works like expected."
    assert FormatDetector.looks_like_xml(lazy_shared_datadir / testfile) is expected
