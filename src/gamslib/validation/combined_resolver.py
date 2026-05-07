"""Custom resolver that combines XML CATALOG resolution with host filtering and local caching.

This resolver extends the `lxml.etree.Resolver` class to provide custom resolution of
external XML entities using a local catalog. It intercepts requests for external
resources (such as DTDs or schemas) and attempts to resolve them to local files,
improving performance and reliability.

The `CombinedCatalogResolver` class extends the `lxml.etree.Resolver` class and overrides
the `resolve` method to implement the custom resolution logic.

The `resolve` method intercepts requests for external resources and attempts to resolve
them to local files. If a local file is found, it returns the local file path. If no
local file is found, the original request is made to the XML CATALOG and the result is
returned.

The `get_cache_path` method generates a unique cache file path for the given URL. The cache
filename is derived from a hash of the URL to ensure uniqueness and avoid issues with special
characters.
"""

import hashlib
import logging
import os
import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from urllib.request import url2pathname

import gams_xml_catalog
import requests
from lxml import etree as ET

from gamslib.projectconfiguration import (
    MissingConfigurationException,
    get_configuration,
)

# ruff: noqa: PLR0911

logger = logging.getLogger(__name__)


class CombinedCatalogResolver(ET.Resolver):
    """Custom XML resource resolver.
     
    This resolver extends the `lxml.etree.Resolver` class and provides custom resolution logic 
    for external XML resources that combines XML CATALOG resolution with host filtering 
    and local caching.
    """

    def __init__(
        self,
        allowed_hosts: Optional[list[str]] = None,
        cache_dir: str | None = ".schema_cache",
    ):
        """
        Create a Resolver instance.

        Args:
            allowed_hosts (Optional[list[str]], optional): _description_. Defaults to None.
            cache_dir (str | None, optional): _description_. 
                    Defaults to ".schema_cache". Set to None to disable caching.
        """
        gams_xml_catalog.activate_catalog()
        self._set_allowed_hosts(allowed_hosts)
        self.cache_dir = cache_dir
        if cache_dir is not None:
            os.makedirs(self.cache_dir, exist_ok=True)

    def get_cache_path(self, url: str) -> str | None:
        """Generate a unique cache file path for the given URL.

        The cache filename is derived from a hash of the URL to ensure uniqueness and avoid
        issues with special characters.
        The cached file retains the original extension for clarity.

        Args:
            url (str): The URL of the file to be cached.

        Returns:
            str: The path to the cache file or None if caching is disabled.
        """
        if self.cache_dir is None:
            return None
        extension = os.path.splitext(url)[1]
        unique_id = hashlib.md5(url.encode("utf-8")).hexdigest()
        return os.path.join(self.cache_dir, f"cached{unique_id}{extension}")

    
    def resolve(self, url: str, pubid: str | None, context):
        """Resolve a URL to an (XML) document.

        The resolution process follows these steps:
        1. Attempt to resolve using the XML CATALOG. If successful, return the catalog result.
        2. If the URL does not match any of the allowed hosts, return None.
        3. Attempt to resolve from the local cache. If successful, return the cache result.
        4. Attempt to download the file and cache it. If successful, return the cache result.
        """

        # 1. try to load via XML CATALOG
        # resolve_filename(url, ...) is not a reliable existence check and may return
        # a resolver object even when URL is unresolved. Therefore we first ask the
        # catalog explicitly for a mapped local path.
        catalog_path = self._resolve_catalog_path(url)
        if catalog_path is not None:
            # Keep base_url=url so downstream relative imports remain URL-based
            # and avoid duplicate imports caused by mixed URL/file identities.
            return self.resolve_string(catalog_path.read_bytes(), context, base_url=url)

        # Resolve local file paths/URIs directly.
        parsed = urlparse(url)
        local_path = url2pathname(parsed.path) if parsed.scheme == "file" else url
        if os.path.isfile(local_path):
            return self.resolve_filename(local_path, context)

        # 2. host filter
        if not self._is_allowed_host(url):
            return None

        # 3. local cache
        cache_path = self.get_cache_path(url)
        if cache_path is not None and Path(cache_path).is_file():
            return self.resolve_string(
                Path(cache_path).read_bytes(), context, base_url=url
            )

        # 4. download
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            if cache_path is not None:
                Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
                Path(cache_path).write_bytes(response.content)
                return self.resolve_string(response.content, context, base_url=url)
            return self.resolve_string(response.content, context, base_url=url)

        except Exception as exp:
            logger.warning(
                "Something unexpected happened while loading schema %s: %s", url, exp
            )
            return None

    def get_content(self, schema_uri: str) -> bytes:
        """Return content of URL.

        Works like resolve(), but returns the raw content instead of
        a file path or file-like object.

        This is a hack for non XML based schema formats (eg. RNC), where we cannot use the
        resolver.resolve mechanism directly, but still want to benefit from the catalog and caching.
        """
        cache_path = Path(self.get_cache_path(schema_uri))
        if cache_path is not None and cache_path.is_file():
            return cache_path.read_bytes()

        parsed = urlparse(schema_uri)
        if parsed.scheme == "file":
            schema_uri = url2pathname(parsed.path)

        if os.path.isfile(schema_uri):
            return Path(schema_uri).read_bytes()

        catalog_path = self._resolve_catalog_path(schema_uri)
        if catalog_path is not None:
            return catalog_path.read_bytes()

        if self._is_allowed_host(
            schema_uri
        ):  # or self._is_allowed_remote_schema_uri(schema_uri):
            resp = requests.get(schema_uri, timeout=10)
            resp.raise_for_status()
            content = resp.content
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_bytes(content)
            return content

        raise FileNotFoundError(f"Cannot load schema '{schema_uri}'.")

    def _is_allowed_host(self, url: str) -> bool:
        """Check if the host of the given URL is in the allowed list."""
        uri = urlparse(url)
        host = (uri.hostname or "").lower()
        return host in {entry.lower() for entry in self.allowed_hosts}

    def _resolve_catalog_path(self, url: str) -> Path | None:
        """Resolve URL via gams_xml_catalog and return an existing local file path."""
        path = gams_xml_catalog.resolve_uri_to_path(url)
        if path is None:
            return None

        if path.is_file():
            return path

        # Some catalog entries point to .../3.x.y/<name>.xsd while files live in
        # .../3.x.y/base/<name>.xsd. Try this fallback before giving up.
        candidate = path.parent / "base" / path.name
        if candidate.is_file():
            return candidate

        return None

    def _set_allowed_hosts(self, allowed_hosts: Optional[list[str]] = None) -> None:
        """Set the list of allowed hosts from the project configuration or environment variable.

        The method first attempts to read the allowed hosts from the project configuration. If the
        configuration is not found, it falls back to reading from the environment variable
        `GAMSLIB_SAFE_XML_HOSTS`, which should contain a comma-separated list of hosts.
        If this environment variable is also not set, an empty list is returned, effectively
        blocking all remote hosts.

        Returns:
            list[str]: A list of allowed hostnames.
        """
        if allowed_hosts is not None:
            self.allowed_hosts = allowed_hosts
        else:
            try:
                # normally, we should have a project configuration
                config = get_configuration(os.environ.get("GAMSCFG_PROJECT_TOML"))
                self.allowed_hosts = config.general.safe_xml_hosts
            except MissingConfigurationException:
                # if no cfg file: use env variable or empty list
                allowed_hosts = re.split(
                    r"\s*,\s*", os.environ.get("GAMSLIB_SAFE_XML_HOSTS", "")
                )
                self.allowed_hosts = [entry for entry in allowed_hosts if entry]
