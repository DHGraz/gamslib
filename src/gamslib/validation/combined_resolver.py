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
import os

from lxml import etree as ET
import requests

import gams_xml_catalog


class CombinedCatalogResolver(ET.Resolver):
    """Custom resolver that combines XML CATALOG resolution with host filtering and local caching."""

    def __init__(self, allowed_hosts: list[str], cache_dir: str = ".schema_cache"):
        super().__init__()
        gams_xml_catalog.activate_catalog()
        self.allowed_hosts = allowed_hosts
        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def get_cache_path(self, url):
        """Generate a unique cache file path for the given URL.

        The cache filename is derived from a hash of the URL to ensure uniqueness and avoid
        issues with special characters.
        The cached file retains the original extension for clarity.

        Args:
            url (str): The URL of the file to be cached.

        Returns:
            str: The path to the cache file.
        """
        extension = os.path.splitext(url)[1]
        unique_id = hashlib.md5(url.encode("utf-8")).hexdigest()
        return os.path.join(self.cache_dir, f"cached{unique_id}{extension}")

    def resolve(self, url: str, pubid: str | None, context) -> str | None:
        """Resolve a URL to an (XML) document.

        The resolution process follows these steps:
        1. Attempt to resolve using the XML CATALOG. If successful, return the catalog result.
        2. If the URL does not match any of the allowed hosts, return None.
        3. Attempt to resolve from the local cache. If successful, return the cache result.
        4. Attempt to download the file and cache it. If successful, return the cache result.
        """
        # 1. try to load via XML CATALOG
        catalog_res = self.resolve_filename(url, context)
        if catalog_res is not None:
            return catalog_res

        # 2. host filter
        if not any(host in url for host in self.allowed_hosts):
            return None

        # 3. local cache
        cache_path = self.get_cache_path(url)
        if os.path.exists(cache_path):
            return self.resolve_filename(cache_path, context)

        # 4. download
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            with open(cache_path, "wb") as f:
                f.write(response.content)
            return self.resolve_filename(cache_path, context)
        except Exception:
            return None
