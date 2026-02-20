"""Tests for the ValidationResult and ValidationSubResult classes from the validationresult module."""
import copy
import pytest

from gamslib.validation.validationresult import ValidationResult, ValidationSubResult


@pytest.fixture(name="subresult")
def make_subresult():
    "Return a ValidationSubResult object for use in tests."
    return ValidationSubResult(
        True, "TestValidator", "file:///foo/bar", "msg1", [], ["Warning 1", "Warning 2"]
    )

def test_validationresult_str(monkeypatch):
    "Test the __str__ method of a ValidationResult object."
    result = ValidationResult("foo/bar.xml")
    assert str(result) == "ValidationResult for file 'foo/bar.xml': valid."

    # is_valid is a property, so we need to monkeypatch it to test the invalid case
    monkeypatch.setattr(type(result), "is_valid", 
                        property(lambda self: False))
    assert str(result) == "ValidationResult for file 'foo/bar.xml': invalid."

def test_validationsubresult(subresult):
    "Test creation of a ValidationSubResult object."
    assert subresult.is_valid
    assert subresult.validator_name == "TestValidator"
    assert subresult.message == "msg1"
    assert subresult.schema_uri == "file:///foo/bar"
    assert not subresult.errors
    assert subresult.warnings == ["Warning 1", "Warning 2"]


def test_empty_validationresult():
    "Test creation of a ValidationResult object."
    result = ValidationResult("foo/bar.xml")
    assert result.is_valid  # TODO: is this correct if not a single subresult was added?
    assert result.file_path == "foo/bar.xml"
    assert not list(result.get_subresults()) # no subresults
    assert result.get_errors() == []
    assert result.get_warnings() == []


def test_valid_validationresult(subresult):
    "Test creation of a ValidationResult object with only valid subresults."
    subresult2 = copy.deepcopy(subresult)
    subresult2.message = "msg2"
    subresult2.schema_uri = "file:///foo/baz"
    subresult2.warnings = ["Warning 3"]

    result = ValidationResult("foo/bar.xml")

    result.add_subresult(subresult)
    result.add_subresult(subresult2)

    assert result.is_valid
    assert len(list(result.get_subresults())) == 2
    assert result.get_errors() == []
    assert result.get_warnings() == ["Warning 1", "Warning 2", "Warning 3"]
    assert result.get_messages() == ["msg1", "msg2"]
    assert list(result.get_subresults()) == [subresult, subresult2]


def test_invalid_validationresult(subresult):
    "Test creation of a ValidationResult object with only invalid subresults."
    subresult2 = copy.deepcopy(subresult)
    subresult2.is_valid = False
    subresult2.message = "msg2"
    subresult2.errors = ["Error 1"]
    subresult2.warnings = ["Warning 3"]
    subresult2.schema_uri = "file:///foo/baz"

    result = ValidationResult("foo/bar.xml")

    result.add_subresult(subresult)
    result.add_subresult(subresult2)

    assert not result.is_valid
    assert len(list(result.get_subresults())) == 2
    assert result.get_errors() == ["Error 1"]
    assert result.get_warnings() == ["Warning 1", "Warning 2", "Warning 3"]
    assert result.get_messages() == ["msg1", "msg2"]
    assert list(result.get_subresults()) == [subresult, subresult2]
