"""Shared pytest fixtures for SIP tests."""

import pytest

from gamslib.sip.utils import fetch_json_schema


@pytest.fixture(autouse=True)
def clear_sip_schema_cache():
    """Avoid cross-test pollution from fetch_json_schema lru_cache."""
    fetch_json_schema.cache_clear()
    yield
    fetch_json_schema.cache_clear()
