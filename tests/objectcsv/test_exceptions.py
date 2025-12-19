import pytest
from gamslib.objectcsv.exceptions import ValidationError

def test_validation_error_is_subclass_of_valueerror():
    assert issubclass(ValidationError, ValueError)

def test_validation_error_message():
    msg = "Invalid metadata"
    err = ValidationError(msg)
    assert str(err) == msg

def test_validation_error_can_be_raised_and_caught():
    with pytest.raises(ValidationError) as excinfo:
        raise ValidationError("Test error")
    assert "Test error" in str(excinfo.value)