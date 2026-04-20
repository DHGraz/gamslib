"Minimal tests for the custom exceptions in the objectcsv module."

import pytest
from gamslib.objectcsv.exceptions import ValidationError


def test_validation_error_is_subclass_of_valueerror():
    """
    Test that ValidationError is a subclass of ValueError.

    This test case ensures that the ValidationError class is correctly
    defined as a subclass of ValueError. This is important for
    proper error handling and propagation in the code.
    """
    assert issubclass(ValidationError, ValueError)


def test_validation_error_message():
    """Test that ValidationError message is correctly preserved."""
    msg = "Invalid metadata"
    err = ValidationError(msg)
    assert str(err) == msg


def test_validation_error_can_be_raised_and_caught():
    """Test that ValidationError can be raised and caught correctly."""
    with pytest.raises(ValidationError) as excinfo:
        raise ValidationError("Test error")
    assert "Test error" in str(excinfo.value)
