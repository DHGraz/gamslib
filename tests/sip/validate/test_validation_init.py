"Test the validate_bag function with various scenarios"

from unittest.mock import patch

import pytest
from gamslib.sip.validation import validate_bag
from gamslib.sip import BagValidationError

@pytest.fixture(name="bag_dir")
def bag_dir_fixture(tmp_path):
    "Create a temporary directory to act as the bag_dir"
    return tmp_path

def test_validate_bag_success(bag_dir):
    "Patch all validation functions to succeed"
    with patch("gamslib.sip.validation.validate_structure") as mock_structure, \
         patch("gamslib.sip.validation.validate_bagit_txt") as mock_bagit_txt, \
         patch("gamslib.sip.validation.validate_manifest_md5") as mock_md5, \
         patch("gamslib.sip.validation.validate_manifest_sha512") as mock_sha512, \
         patch("gamslib.sip.validation.validate_sip_json") as mock_sip_json, \
         patch("gamslib.sip.validation.validate_baginfo_text") as mock_baginfo:
        # All mocks do nothing (success)
        validate_bag(bag_dir)
        mock_structure.assert_called_once_with(bag_dir)
        mock_bagit_txt.assert_called_once_with(bag_dir)
        mock_md5.assert_called_once_with(bag_dir)
        mock_sha512.assert_called_once_with(bag_dir)
        mock_sip_json.assert_called_once_with(bag_dir)
        mock_baginfo.assert_called_once_with(bag_dir)

def test_validate_bag_dir_not_exists(tmp_path):
    "Test that validate_bag raises if the directory does not exist"
    non_existent = tmp_path / "does_not_exist"
    with pytest.raises(BagValidationError) as excinfo:
        validate_bag(non_existent)
    assert "does not exist" in str(excinfo.value)

@pytest.mark.parametrize(
    "fail_func,fail_exception",
    [
        ("gamslib.sip.validation.validate_structure", BagValidationError("structure failed")),
        ("gamslib.sip.validation.validate_bagit_txt", BagValidationError("bagit.txt failed")),
        ("gamslib.sip.validation.validate_manifest_md5", BagValidationError("md5 failed")),
        ("gamslib.sip.validation.validate_manifest_sha512", BagValidationError("sha512 failed")),
        ("gamslib.sip.validation.validate_sip_json", BagValidationError("sip json failed")),
        ("gamslib.sip.validation.validate_baginfo_text", BagValidationError("baginfo failed")),
    ]
)
def test_validate_bag_raises_on_validation_failure(bag_dir, fail_func, fail_exception):
    "Patch all validation functions to succeed except one, which raises"
    patches = {
        "gamslib.sip.validation.validate_structure": patch("gamslib.sip.validation.validate_structure"),
        "gamslib.sip.validation.validate_bagit_txt": patch("gamslib.sip.validation.validate_bagit_txt"),
        "gamslib.sip.validation.validate_manifest_md5": patch("gamslib.sip.validation.validate_manifest_md5"),
        "gamslib.sip.validation.validate_manifest_sha512": patch("gamslib.sip.validation.validate_manifest_sha512"),
        "gamslib.sip.validation.validate_sip_json": patch("gamslib.sip.validation.validate_sip_json"),
        "gamslib.sip.validation.validate_baginfo_text": patch("gamslib.sip.validation.validate_baginfo_text"),
    }
    with patches["gamslib.sip.validation.validate_structure"] as mock_structure, \
         patches["gamslib.sip.validation.validate_bagit_txt"] as mock_bagit_txt, \
         patches["gamslib.sip.validation.validate_manifest_md5"] as mock_md5, \
         patches["gamslib.sip.validation.validate_manifest_sha512"] as mock_sha512, \
         patches["gamslib.sip.validation.validate_sip_json"] as mock_sip_json, \
         patches["gamslib.sip.validation.validate_baginfo_text"] as mock_baginfo:
        # Set all to succeed
        for m in [mock_structure, mock_bagit_txt, mock_md5, mock_sha512, mock_sip_json, mock_baginfo]:
            m.side_effect = None
        # Set the one to fail
        failing_mock = {
            "gamslib.sip.validation.validate_structure": mock_structure,
            "gamslib.sip.validation.validate_bagit_txt": mock_bagit_txt,
            "gamslib.sip.validation.validate_manifest_md5": mock_md5,
            "gamslib.sip.validation.validate_manifest_sha512": mock_sha512,
            "gamslib.sip.validation.validate_sip_json": mock_sip_json,
            "gamslib.sip.validation.validate_baginfo_text": mock_baginfo,
        }[fail_func]
        failing_mock.side_effect = fail_exception
        with pytest.raises(BagValidationError) as excinfo:
            validate_bag(bag_dir)
        assert str(fail_exception) in str(excinfo.value)