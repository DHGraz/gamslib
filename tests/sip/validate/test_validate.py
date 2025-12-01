from pathlib import Path
import pytest
from gamslib.sip.validation import validate_bag
from gamslib.sip import BagValidationError


def test_validate_no_dir():
    "Test if exception is raised when directory does not exist."
    with pytest.raises(BagValidationError, match="does not exist"):
        validate_bag(Path("nonexistent_dir"))
