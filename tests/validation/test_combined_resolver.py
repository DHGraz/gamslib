"""Unit tests for :class:`CombinedCatalogResolver`.
"""

import hashlib
from pathlib import Path

import pytest

import gamslib.validation.combined_resolver as combined_resolver_mod
from gamslib.validation.combined_resolver import CombinedCatalogResolver



def _make_resolver(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, allowed_hosts=None):
    """Create a resolver with a temporary cache directory."""
    # The implementation currently relies on a module-global hashlib symbol.
    monkeypatch.setattr(combined_resolver_mod, "hashlib", hashlib, raising=False)
    hosts = allowed_hosts if allowed_hosts is not None else ["example.org"]
    cache_dir = tmp_path / "schema_cache"
    resolver = CombinedCatalogResolver(hosts, cache_dir=str(cache_dir))
    return resolver, cache_dir


def test_regression_constructor_initializes_state(tmp_path, monkeypatch):
    """Regression: constructor initializes resolver state and creates cache directory."""
    monkeypatch.setattr(combined_resolver_mod, "hashlib", hashlib, raising=False)
    cache_dir = tmp_path / "schema_cache"
    resolver = CombinedCatalogResolver(["example.org"], cache_dir=str(cache_dir))

    assert resolver.allowed_hosts == ["example.org"]
    assert resolver.cache_dir == str(cache_dir)
    assert cache_dir.is_dir()


def test_constructor_sets_fields_and_creates_cache_dir(tmp_path, monkeypatch):
    """Constructor stores config and creates cache directory if missing."""
    resolver, cache_dir = _make_resolver(tmp_path, monkeypatch, ["host1", "host2"])

    assert resolver.allowed_hosts == ["host1", "host2"]
    assert resolver.cache_dir == str(cache_dir)
    assert cache_dir.is_dir()


@pytest.mark.parametrize(
    "url",
    [
        "https://example.org/schema.xsd",
        "https://example.org/schema",
        "https://example.org/schema.json",
    ],
)
def test_get_cache_path_uses_md5_and_file_extension(url, tmp_path, monkeypatch):
    """Cache file path uses URL md5 and preserves URL file extension."""
    resolver, cache_dir = _make_resolver(tmp_path, monkeypatch)

    expected_url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()
    expected_filename = f"cached{expected_url_hash}{Path(url).suffix}"
    expected_path = (cache_dir / expected_filename).as_posix()    

    result = resolver.get_cache_path(url)
    print(result)
    print(expected_path)
    assert result == expected_path



def test_resolve_prefers_catalog_result(tmp_path, monkeypatch):
    """Resolver returns catalog result immediately and skips network fetch."""
    resolver, _ = _make_resolver(tmp_path, monkeypatch)
    url = "https://example.org/schema/schema.xsd"

    monkeypatch.setattr(
        resolver,
        "resolve_filename",
        lambda filename, context: "CATALOG_RESULT" if filename == url else None,
    )

    def fail_get(*_args, **_kwargs):
        pytest.fail("requests.get should not be called when catalog resolution succeeds")

    monkeypatch.setattr(combined_resolver_mod.requests, "get", fail_get)

    assert resolver.resolve(url, None, None) == "CATALOG_RESULT"


def test_resolve_returns_none_for_disallowed_host(tmp_path, monkeypatch):
    """Resolver denies URLs outside the allowlist without performing HTTP requests."""
    resolver, _ = _make_resolver(tmp_path, monkeypatch, ["allowed.example"])
    url = "https://forbidden.example/schema.xsd"

    monkeypatch.setattr(resolver, "resolve_filename", lambda *_args, **_kwargs: None)

    def fail_get(*_args, **_kwargs):
        pytest.fail("requests.get should not be called for disallowed hosts")

    monkeypatch.setattr(combined_resolver_mod.requests, "get", fail_get)

    assert resolver.resolve(url, None, None) is None


def test_resolve_uses_cached_file_when_available(tmp_path, monkeypatch):
    """Resolver uses existing cache entry before attempting a download."""
    resolver, cache_dir = _make_resolver(tmp_path, monkeypatch)
    url = "https://example.org/schema/schema.xsd"

    cached_file = cache_dir / "cached_schema.xsd"
    cached_file.write_bytes(b"cached-content")

    monkeypatch.setattr(resolver, "get_cache_path", lambda _url: str(cached_file))

    def fake_resolve_filename(filename, _context):
        # First call is catalog attempt with URL, second call resolves cached file.
        if filename == url:
            return None
        if filename == str(cached_file):
            return "CACHED_RESULT"
        return None

    monkeypatch.setattr(resolver, "resolve_filename", fake_resolve_filename)

    def fail_get(*_args, **_kwargs):
        pytest.fail("requests.get should not be called when cache file exists")

    monkeypatch.setattr(combined_resolver_mod.requests, "get", fail_get)

    assert resolver.resolve(url, None, None) == "CACHED_RESULT"


def test_resolve_downloads_and_caches_when_not_in_catalog_or_cache(tmp_path, monkeypatch):
    """Resolver downloads missing schema, writes cache file, then resolves from it."""
    resolver, cache_dir = _make_resolver(tmp_path, monkeypatch)
    url = "https://example.org/schema/new-schema.xsd"

    cached_file = cache_dir / "cached_downloaded.xsd"
    monkeypatch.setattr(resolver, "get_cache_path", lambda _url: str(cached_file))

    def fake_resolve_filename(filename, _context):
        # Simulate catalog miss, then success when resolving downloaded cache file.
        if filename == url:
            return None
        if filename == str(cached_file):
            return "DOWNLOADED_RESULT"
        return None

    monkeypatch.setattr(resolver, "resolve_filename", fake_resolve_filename)

    class FakeResponse:
        content = b"<xsd:schema/>"

        @staticmethod
        def raise_for_status():
            return None

    monkeypatch.setattr(combined_resolver_mod.requests, "get", lambda *_args, **_kwargs: FakeResponse())

    result = resolver.resolve(url, None, None)

    assert result == "DOWNLOADED_RESULT"
    assert cached_file.is_file()
    assert cached_file.read_bytes() == b"<xsd:schema/>"


def test_resolve_returns_none_when_download_fails(tmp_path, monkeypatch):
    """Resolver returns ``None`` and leaves no cache artifact when HTTP fails."""
    resolver, cache_dir = _make_resolver(tmp_path, monkeypatch)
    url = "https://example.org/schema/broken.xsd"

    cached_file = cache_dir / "cached_broken.xsd"
    monkeypatch.setattr(resolver, "get_cache_path", lambda _url: str(cached_file))
    monkeypatch.setattr(resolver, "resolve_filename", lambda filename, _context: None if filename == url else "UNEXPECTED")

    def raise_error(*_args, **_kwargs):
        raise RuntimeError("network error")

    monkeypatch.setattr(combined_resolver_mod.requests, "get", raise_error)

    assert resolver.resolve(url, None, None) is None
    assert not cached_file.exists()
