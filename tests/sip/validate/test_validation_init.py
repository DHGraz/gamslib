"Test the validate_bag function with various scenarios"

from unittest.mock import patch

import pytest

from gamslib.sip import BagValidationError
from gamslib.sip.validation import (
    validate_project_name,
    _validate_type_prefix,
    validate_bag,
    validate_datastream_id,
    validate_pid,
    _split_id,
)


@pytest.fixture(name="bag_dir")
def bag_dir_fixture(tmp_path):
    "Create a temporary directory to act as the bag_dir"
    return tmp_path


def test_validate_bag_success(bag_dir):
    "Patch all validation functions to succeed"
    with (
        patch("gamslib.sip.validation.validate_structure") as mock_structure,
        patch("gamslib.sip.validation.validate_bagit_txt") as mock_bagit_txt,
        patch("gamslib.sip.validation.validate_manifest_md5") as mock_md5,
        patch("gamslib.sip.validation.validate_manifest_sha512") as mock_sha512,
        patch("gamslib.sip.validation.validate_sip_json") as mock_sip_json,
        patch("gamslib.sip.validation.validate_baginfo_text") as mock_baginfo,
    ):
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
        (
            "gamslib.sip.validation.validate_structure",
            BagValidationError("structure failed"),
        ),
        (
            "gamslib.sip.validation.validate_bagit_txt",
            BagValidationError("bagit.txt failed"),
        ),
        (
            "gamslib.sip.validation.validate_manifest_md5",
            BagValidationError("md5 failed"),
        ),
        (
            "gamslib.sip.validation.validate_manifest_sha512",
            BagValidationError("sha512 failed"),
        ),
        (
            "gamslib.sip.validation.validate_sip_json",
            BagValidationError("sip json failed"),
        ),
        (
            "gamslib.sip.validation.validate_baginfo_text",
            BagValidationError("baginfo failed"),
        ),
    ],
)
def test_validate_bag_raises_on_validation_failure(bag_dir, fail_func, fail_exception):
    "Patch all validation functions to succeed except one, which raises"
    patches = {
        "gamslib.sip.validation.validate_structure": patch(
            "gamslib.sip.validation.validate_structure"
        ),
        "gamslib.sip.validation.validate_bagit_txt": patch(
            "gamslib.sip.validation.validate_bagit_txt"
        ),
        "gamslib.sip.validation.validate_manifest_md5": patch(
            "gamslib.sip.validation.validate_manifest_md5"
        ),
        "gamslib.sip.validation.validate_manifest_sha512": patch(
            "gamslib.sip.validation.validate_manifest_sha512"
        ),
        "gamslib.sip.validation.validate_sip_json": patch(
            "gamslib.sip.validation.validate_sip_json"
        ),
        "gamslib.sip.validation.validate_baginfo_text": patch(
            "gamslib.sip.validation.validate_baginfo_text"
        ),
    }
    with (
        patches["gamslib.sip.validation.validate_structure"] as mock_structure,
        patches["gamslib.sip.validation.validate_bagit_txt"] as mock_bagit_txt,
        patches["gamslib.sip.validation.validate_manifest_md5"] as mock_md5,
        patches["gamslib.sip.validation.validate_manifest_sha512"] as mock_sha512,
        patches["gamslib.sip.validation.validate_sip_json"] as mock_sip_json,
        patches["gamslib.sip.validation.validate_baginfo_text"] as mock_baginfo,
    ):
        # Set all to succeed
        for m in [
            mock_structure,
            mock_bagit_txt,
            mock_md5,
            mock_sha512,
            mock_sip_json,
            mock_baginfo,
        ]:
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


def test_split_id_no_dot():
    "Test split_id raises ValueError if no dot present"
    with pytest.raises(ValueError):
        _split_id("abcdef")


def test_split_id_empty_string():
    "Test_split_id raises ValueError on empty string"
    with pytest.raises(ValueError):
        _split_id("")


def test_split_id_dot_at_start():
    "Test split_id with dot at start"
    # leading dots should be preserved in object id
    result = _split_id(".abc")
    assert result == ("", "", ".abc")


@pytest.mark.parametrize(
    "pid,expected",
    [
        # No type prefix
        ("abc.def123", ("", "abc", "def123")),
        ("project.123", ("", "project", "123")),
        # With type prefix
        ("o:abc.def", ("o", "abc", "def")),
        ("type:proj.456", ("type", "proj", "456")),
        # Percent-encoded colon
        ("%3Aabc.def", ("", ":abc", "def")),
        ("o%3Aabc.def", ("o", "abc", "def")),
        # Complex project prefix
        ("o:foo-bar.123_baz", ("o", "foo-bar", "123_baz")),
        # Multiple colons in prefix
        ("x:y:z.oid", ("x", "y:z", "oid")),
        # Edge case: no dot
        # This should raise ValueError
    ],
)
def test_split_id(pid, expected):
    "Test split_id with valid IDs"
    assert _split_id(pid) == expected


@pytest.mark.parametrize(
    "pid",
    [
        "abc.def123",
        "abc.123-def",
        "abc.1",
        "abc.1.2",
        "abc.def",
        "abc.123",
        "abc.123-456.789",
        "o:abc.123",
        "o%3Aabc.def",  # encoded colon, should decode to valid
        ## some more complex but valid IDs, provided by Sebis AI
        "test.1",
        "test.123",
        "test.test1",
        "test.abc",
        "test.a1b2c3",
        # With numbers, dots, dashes, underscores after the dot
        "test.object-1",
        "test.object.sub",
        "test.doc-2024-001",
        "test.item.1.2.3",
        # Legacy format with type prefix (discouraged but valid)
        "o:test.1",
        "o:hsa.manuscript-001",
        "o:gams.doc123",
        # Complex valid IDs
        "hsa.collection.subcol.item-001",
        # Edge cases (valid)
        "a.1",  # shortest project prefix (1 letter)
        "abcdefghij.1",  # 10-char project prefix
        "test.a",  # single letter after dot
        "test.1a",  # starts with number after dot (valid)
        "test.123abc",  # number start after dot
        "test.a-b-c-d-e",  # multiple dashes
        "test.a.b.c.d.e",  # multiple dots
        # Real-world examples based on your test data
        "test.test",
        "test.manifest",
        "test.dc-metadata",
        "hsa.manuscript-01",
        "gams.tei-document-2024",
    ],
)
def test_validate_pid_valid(pid):
    "Test valid IDs"
    if ":" in pid or "%3A" in pid:
        with pytest.warns(UserWarning, match="discouraged"):
            validate_pid(pid)
    else:
        validate_pid(pid)


@pytest.mark.parametrize(
    "pid,reason",
    [
        ("abc.A", "lowercase"),  # contains uppercase letter
        ("foo:abc.def", "Allowed prefixes"),  # O: instead of o:
        (".abcdef", "dot"),  # starts with dot
        ("1abcdef", "dot"),  # starts with number
        (
            "abc/def",
            "must contain a dot",
        ),  # contains invalid character #("abc@def",  "contain only"),  # contains invalid character
        (
            "abc@def",
            "must contain a dot",
        ),  # contains invalid character #("abc@def",  "contain only"),  # contains invalid character
        ("abcdef", "must contain a dot"),  # no dot
        ("abc..def", "must start with a letter"),
        ("abc.-def", "must start with a letter"),  # dot followed by dash
        ("abc._def", "must start with a letter"),  # dot followed by underscore
        ("abc.def/", "contain only"),  # ends with slash
        ("abc.def@", "contain only"),  # ends with @
        ("abc.def#", "contain only"),  # ends with #
        ("abc.def$", "contain only"),  # ends with $
        ("abc.def%", "contain only"),  # ends with %
        ("abc.def:ghi", "contain only"),  # extra colon after dot
        ("abc.d..ef", "consecutive"),  # double dot
        ("abc", "must contain a dot"),  # no dot
        ("ab--cd.ef_gh-ij", "contain only"),  # double dash
        ("test-proj.item1", "contain only"),
        (
            "test-proj.123abc",
            "contain only",
        ),  # ("test-proj.123abc", "Allowed prefixes")
        ("abc." + "x" * 61, "longer than 64 characters"),  # too long
    ],
)
def test_validate_pid_invalid(pid, reason):
    "Test invalid PIDs"
    if "O:" in pid:
        with (
            pytest.warns(UserWarning, match="discouraged"),
            pytest.raises(ValueError, match=reason),
        ):
            validate_pid(pid)
    with pytest.raises(ValueError, match=reason):
        validate_pid(pid)


def test_validate_pid_percent_encoded_colon():
    "Test IDs with percent-encoded colon"
    # a valid ID with percent-encoded colon
    with pytest.warns(Warning, match="discouraged"):
        validate_pid("o%3Aabc.def")

    # an invalid ID with percent-encoded colon in project id
    with pytest.raises(ValueError, match="Allowed prefixes"):
        validate_pid("ab1%3Aabc.def")
    # an invalid ID with percent-encoded colon in object id
    with pytest.raises(ValueError):
        validate_pid("abc.def%3A123")


@pytest.mark.parametrize(
    "datastream_id",
    [
        "abc123",
        "a123.1",
        "1abc.foo",
        "abc.def",
        "abc-def",
        "a.b.c",
    ],
)
def test_validate_datastream_id_valid(datastream_id):
    "Test valid datastream IDs"
    assert validate_datastream_id(datastream_id) is None
    assert validate_datastream_id(datastream_id.upper()) is None


@pytest.mark.parametrize(
    "datastream_id,reason",
    [
        ("", "empty"),  # empty string
        ("..abc", "consecutive dots"),  # starts with consecutive dots
        ("abc..def", "consecutive dots"),  # consecutive dots
        ("abc__def", "letters, numbers"),  # consecutive underscores
        ("abc--def", "consecutive dashes"),  # consecutive dashes
        (".abc", "contain only"),  # starts with dot
        ("_abc", "contain only"),  # starts with underscore
        ("-abc", "contain only"),  # starts with dash
        ("abc/def", "contain only"),  # invalid character
        ("abc@def", "contain only"),  # invalid character
        ("abc def", "contain only"),  # space
        ("abc$def", "contain only"),  # invalid character
    ],
)
def test_validate_datastream_id_invalid(datastream_id, reason):
    "Test invalid datastream IDs"
    with pytest.raises(ValueError, match=reason):
        validate_datastream_id(datastream_id)


@pytest.mark.parametrize("project_name", ["a", "abc", "abc123", "a567"])
def test_validate_project_name_valid(project_name):
    "Test valid project prefixes"
    # Should not raise for valid lowercase prefixes
    validate_project_name(project_name)


@pytest.mark.parametrize(
    "project_prefix",
    [
        "",
        "1abc",
        "-abc",
        "abc--def",
        "abc_def",
        "abc.def",
        "abc@def",
        "abc/def",
        "abc--",
        "abc--def--ghi",
        "1Abc",
        "-Abc",
        "Abc--Def",
        "Abc_Def",
        "Abc.Def",
        "Abc@Def",
        "Abc/Def",
    ],
)
def test_validate_project_name_invalid(project_prefix):
    "Test invalid project prefixes"
    with pytest.raises(ValueError):
        validate_project_name(project_prefix)


@pytest.mark.parametrize(
    "type_prefix",
    [
        "",
        "collection",
        "container",
        "context",
        "corpus",
        "o",
        "podcast",
        "query",
    ],
)
def test_validate_type_prefix_valid(type_prefix):
    "Test valid type prefixes"
    # Should not raise for allowed type prefixes
    _validate_type_prefix(type_prefix)


@pytest.mark.parametrize(
    "type_prefix",
    [
        "O",  # uppercase
        "Collection",  # uppercase
        "unknown",  # not in allowed list
        "fedorasystem",  # legacy, not allowed
        "sdef",  # commented out legacy
        "cm",  # commented out legacy
        "cirilo",  # commented out legacy
        "FgsConfig",  # commented out legacy
        "fedora-system",  # commented out legacy
        "sdep",  # commented out legacy
        "container1",  # not in allowed list
        "contextual",  # not in allowed list
        "podcast123",  # not in allowed list
        "query!",  # invalid character
    ],
)
def test_validate_type_prefix_invalid(type_prefix):
    "Test invalid type prefixes"
    with pytest.raises(ValueError):
        _validate_type_prefix(type_prefix)