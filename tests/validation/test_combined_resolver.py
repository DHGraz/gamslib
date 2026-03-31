"""Unit tests for :class:`CombinedCatalogResolver`."""

import hashlib
from pathlib import Path

import pytest
import requests

import gamslib.validation.combined_resolver as combined_resolver_mod
from gamslib.validation.combined_resolver import CombinedCatalogResolver


class FakeResponse:
    "Mock a requests.Response object for testing purposes."

    def __init__(self, **kwargs):
        self.content = kwargs.get("content", b"")
        self.status_code = kwargs.get("status_code", 200)

    def raise_for_status(self):
        """Simulate the behavior of requests.Response.raise_for_status() by raising an exception for HTTP error status codes."""
        if self.status_code >= 400:
            raise requests.exceptions.RequestException(f"HTTP error {self.status_code}")


def test_init_no_args():
    """Test that the constructor initializes the resolver state and creates the cache directory."""
    resolver = CombinedCatalogResolver()
    assert resolver.allowed_hosts == []
    assert resolver.cache_dir == ".schema_cache"
    assert Path(resolver.cache_dir).is_dir()


def test_init_with_args(tmp_path):
    """Test initialization with arguments."""
    cache_dir = tmp_path / "custom_cache"
    resolver = CombinedCatalogResolver(["host1", "host2"], cache_dir.as_posix())
    assert resolver.allowed_hosts == ["host1", "host2"]

    assert resolver.cache_dir == cache_dir.as_posix()
    assert cache_dir.is_dir()


def test_init_with_caching_disabled():
    """Test initialization with caching disabled."""
    resolver = CombinedCatalogResolver(["host1"], cache_dir=None)
    assert resolver.allowed_hosts == ["host1"]
    assert resolver.cache_dir is None


def test_init_with_allowed_hosts_from_config(monkeypatch):
    """Check if the allowed hosts are properly initialized from the configuration"""

    class DummyConfig:
        class General:
            safe_xml_hosts = ["config.example", "foo.uni-graz.at"]

        general = General()

    def dummy_get_configuration(*_args, **_kwargs):
        return DummyConfig()

    monkeypatch.setattr(
        combined_resolver_mod, "get_configuration", dummy_get_configuration
    )
    resolver = CombinedCatalogResolver()
    assert resolver.allowed_hosts == ["config.example", "foo.uni-graz.at"]


def test_init_with_allowed_hosts_from_env(monkeypatch):
    """Check if the allowed hosts are properly initialized from 'GAMSLIB_SAFE_XML_HOSTS'."""
    # this should be used if no config file is available
    monkeypatch.setenv("GAMSLIB_SAFE_XML_HOSTS", "foo.com, bar.com,foobar.org")
    resolver = CombinedCatalogResolver()
    assert resolver.allowed_hosts == ["foo.com", "bar.com", "foobar.org"]


@pytest.mark.parametrize(
    "url",
    [
        "https://example.org/schema.xsd",
        "https://example.org/schema",
        "https://example.org/schema.sch",
    ],
)
def test_get_cache_path(url, tmp_path, monkeypatch):
    """get_cache_path should return a path based on the URL hash and extension."""
    resolver = CombinedCatalogResolver(cache_dir=str(tmp_path))
    cache_file = resolver.get_cache_path(
        url
    )  # we just want to make sure the cache dir is created and hashlib is set up
    expected_hash = hashlib.md5(url.encode("utf-8")).hexdigest()
    expected_extension = Path(url).suffix
    expected_filename = f"cached{expected_hash}{expected_extension}"
    expected_path = (tmp_path / expected_filename).as_posix()
    assert cache_file == expected_path


def test_get_cache_path_returns_none_when_caching_disabled():
    """get_cache_path should return None when caching is disabled."""
    resolver = CombinedCatalogResolver(cache_dir=None)
    url = "https://example.org/schema.xsd"
    assert resolver.get_cache_path(url) is None


def test_resolve_prefers_catalog_result(tmp_path, monkeypatch):
    """Resolver returns catalog result immediately and skips network fetch."""
    resolver = CombinedCatalogResolver(["example.org"], cache_dir=str(tmp_path))
    url = "http://example.org/schema/schema.xsd"

    monkeypatch.setattr(
        resolver,
        "resolve_filename",
        lambda filename, context: "CATALOG_RESULT" if filename == url else None,
    )

    def fail_get(*_args, **_kwargs):
        pytest.fail(
            "requests.get should not be called when catalog resolution succeeds"
        )

    monkeypatch.setattr(combined_resolver_mod.requests, "get", fail_get)

    assert resolver.resolve(url, None, None) == "CATALOG_RESULT"


def test_resolve_returns_none_for_disallowed_host(tmp_path, monkeypatch):
    """Resolver denies URLs outside the allowlist without performing HTTP requests."""
    resolver = CombinedCatalogResolver(cache_dir=str(tmp_path))
    url = "https://forbidden.example/schema.xsd"

    monkeypatch.setattr(resolver, "resolve_filename", lambda *_args, **_kwargs: None)

    def fail_get(*_args, **_kwargs):
        pytest.fail("requests.get should not be called for disallowed hosts")

    monkeypatch.setattr(combined_resolver_mod.requests, "get", fail_get)

    assert resolver.resolve(url, None, None) is None


def test_resolve_uses_cached_file_when_available(tmp_path, monkeypatch):
    """Resolver uses existing cache entry before attempting a download."""
    cache_dir = tmp_path / "schema_cache"
    resolver = CombinedCatalogResolver(["example.org"], cache_dir=str(cache_dir))
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


def test_resolve_downloads_and_caches_when_not_in_catalog_or_cache(
    tmp_path, monkeypatch
):
    """Resolve should download the missing schema, write it to the cache, and then resolve from the cached file."""
    cache_dir = tmp_path / "schema_cache"
    resolver = CombinedCatalogResolver(["example.org"], cache_dir=str(cache_dir))
    url = "https://example.org/schema/new-schema.xsd"

    # we fake the cache path to circumvent the hashing and ensure a predictable location for the test
    cached_file = cache_dir / "cached_downloaded.xsd"
    monkeypatch.setattr(resolver, "get_cache_path", lambda _url: str(cached_file))

    # The lxml resolver class, where CombinedCatalogResolver inherits from, will first call
    # resolve_filename to attempt to resolve the file  # with the original URL, and then
    # with the cached file path. We need to fake both calls to simulate the expected behavior.
    def fake_resolve_filename(filename, _context):
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

    monkeypatch.setattr(
        combined_resolver_mod.requests, "get", lambda *_args, **_kwargs: FakeResponse()
    )

    result = resolver.resolve(url, None, None)

    assert result == "DOWNLOADED_RESULT"
    assert cached_file.is_file()
    assert cached_file.read_bytes() == b"<xsd:schema/>"


def test_resolve_returns_none_when_download_fails(tmp_path, monkeypatch):
    """Resolver returns ``None`` when an allowed URL yields no useful downloadable content."""
    cache_dir = tmp_path / "schema_cache"
    resolver = CombinedCatalogResolver(["example.org"], cache_dir=str(cache_dir))
    url = "https://example.org/schema/broken.xsd"

    monkeypatch.setattr(resolver, "resolve_filename", lambda *_args, **_kwargs: None)

    monkeypatch.setattr(
        combined_resolver_mod.requests, "get", lambda *_args, **_kwargs: FakeResponse()
    )

    assert resolver.resolve(url, None, None) is None


def test_get_content_from_file(tmp_path, lazy_shared_datadir):
    "Test the get_content method with a local file path and URI."
    cache_dir = tmp_path / "schema_cache"
    resolver = CombinedCatalogResolver(cache_dir=str(cache_dir))
    file = lazy_shared_datadir / "schemas" / "simple.xsd"

    # a normal path
    content = resolver.get_content(file.as_posix())
    assert content == file.read_bytes()


def test_get_content_from_allowed_uri(tmp_path, lazy_shared_datadir, monkeypatch):
    "Test the get_content method with an allowed http URI."
    cache_dir = tmp_path / "schema_cache"
    resolver = CombinedCatalogResolver(["foo.com"], cache_dir=str(cache_dir))
    # monkeypatch the requests.get method to return a fake response with the content of the test schema,
    # since we cannot rely on external network access in tests
    expected_content = (lazy_shared_datadir / "schemas" / "simple.xsd").read_bytes()
    monkeypatch.setattr(
        combined_resolver_mod.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(content=expected_content),
    )

    content = resolver.get_content("http://foo.com/schema/simple.xsd")
    assert content == expected_content

    # the second call should use the cached file instead of making another HTTP request
    # we only test if this succeeds
    content = resolver.get_content("http://foo.com/schema/simple.xsd")
    assert content == expected_content


def test_get_content_from_allowed_uri_404(tmp_path, lazy_shared_datadir, monkeypatch):
    "Test the get_content method with an allowed http URI which returns a 404 error."
    cache_dir = tmp_path / "schema_cache"
    resolver = CombinedCatalogResolver(["foo.com"], cache_dir=str(cache_dir))
    # monkeypatch the requests.get method to return a fake response with the content of the test schema,
    # since we cannot rely on external network access in tests
    monkeypatch.setattr(
        combined_resolver_mod.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(status_code=404),
    )
    with pytest.raises(Exception):
        resolver.get_content("http://foo.com/schema/simple.xsd")


def test_get_content_from_catalog_uri(tmp_path, lazy_shared_datadir):
    "Test the get_content method with a URI that can be resolved via the catalog."
    cache_dir = tmp_path / "schema_cache"
    resolver = CombinedCatalogResolver(cache_dir=str(cache_dir))
    content = resolver.get_content(
        "http://www.tei-c.org/release/xml/tei/custom/schema/xsd/tei_all.xsd"
    )
    assert content


def test_get_content_from_disallowed_uri(tmp_path, lazy_shared_datadir):
    "Test the get_content method with a URI that is not allowed and cannot be resolved via the catalog."
    cache_dir = tmp_path / "schema_cache"
    resolver = CombinedCatalogResolver(cache_dir=str(cache_dir))
    with pytest.raises(Exception):
        resolver.get_content("http://unallowed.example.org/schema.xsd")
