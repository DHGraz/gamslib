"""Tests for the alwaysvalidvalidator module.
"""
from pathlib import Path

import pytest
from gamslib.validation.alwaysvalidvalidator import AlwaysValidValidator


def test_alwaysvalidvalidator():
    "Test the AlwaysValidValidator class."
    assert isinstance(AlwaysValidValidator(), AlwaysValidValidator) 


def test_validate():
    "Test the validate method of the AlwaysValidValidator."
    validator = AlwaysValidValidator()
    result = validator.validate(Path("foo/bar.xml"))
    assert result.is_valid
    subresults = list(result.get_subresults())
    assert len(subresults) == 1
    assert subresults[0].validator_name == "AlwaysValidValidator"
    assert result.get_errors() == []
    assert result.get_warnings()[0] == "This file type has no validator registered."
    assert "Did not validate file" in result.get_messages()[0]

def test_add_subresult():
    "Test that the add_subresult method of the AlwaysValidValidator raises a NotImplementedError."
    validator = AlwaysValidValidator()
    with pytest.raises(NotImplementedError):
        validator.add_subresult(None)
