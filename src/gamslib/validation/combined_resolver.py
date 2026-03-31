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
from pathlib import Path
import re
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

from lxml import etree as ET
import requests

import gams_xml_catalog

from gamslib.projectconfiguration import (
    MissingConfigurationException,
    get_configuration,
)


class CombinedCatalogResolver(ET.Resolver):
    """Custom resolver that combines XML CATALOG resolution with host filtering and local caching."""

    def __init__(
        self,
        allowed_hosts: Optional[list[str]] = None,
        cache_dir: str | None = ".schema_cache",
    ):
        """
        Create a Resolver instance.

        Args:
            allowed_hosts (Optional[list[str]], optional): _description_. Defaults to None.
            cache_dir (str | None, optional): _description_. Defaults to ".schema_cache". Set to None to disable caching.
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
        catalog_res = self.resolve_filename(url, context)
        if catalog_res is not None:
            return catalog_res

        #uri = urlparse(url)
        #host = (uri.hostname or "").lower()
        #is_allowed = host in {entry.lower() for entry in self.allowed_hosts}

        # 2. host filter
        if not self._is_allowed_host(url):
            return None

        # 3. local cache
        cache_path = self.get_cache_path(url)
        if cache_path is not None and Path(cache_path).is_file():
            return self.resolve_filename(cache_path, context)

        # 4. download
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            if cache_path is not None:
                Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
                Path(cache_path).write_bytes(response.content)
                return self.resolve_filename(cache_path, context)
            return self.resolve_string(response.content, context)

        except Exception as exp:
            logger.warning("Something unexpected happened while loading schema %s: %s", url, exp)
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

        schema_uri = re.sub(r"^file://", "", schema_uri)
        if os.path.isfile(schema_uri):
            content = Path(schema_uri).read_bytes()
        elif self._is_allowed_host(schema_uri): # or self._is_allowed_remote_schema_uri(schema_uri):
            resp = requests.get(schema_uri, timeout=10)
            resp.raise_for_status()
            content = resp.content
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_bytes(content)
        else:
            # use the custom CatalogResolver to get the content of the rnc schema 
            path = gams_xml_catalog.resolve_uri_to_path(schema_uri)
            if path is None:
                raise FileNotFoundError(f"Cannot load schema '{schema_uri}'.")
            content = path.read_bytes()
        return content
        
        # # There seems to be no way to access the resolved content directly via lxml.   
        # if self._is_allowed_host(schema_url):
        #     cache_path = self.get_cache_path(schema_url)
        #     if cache_path is not None and Path(cache_path).is_file():
        #         return Path(cache_path).read_bytes()
        #     try:
        #         response = requests.get(schema_url, timeout=10)
        #         response.raise_for_status()
        #         if cache_path is not None:
        #             Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
        #             Path(cache_path).write_bytes(response.content)
        #         return response.content
        #     except Exception as exp:
        #         logger.warning("Something unexpected happened while loading schema %s: %s", schema_url, exp)
        #         raise exp from exp
        # else:
        #     raise ValueError(f"Host of URL '{schema_url}' is not in the allowed list.")



          #  ---
        # try:
        #     # normally, we should have a project configuration 
        #     config = get_configuration(os.environ.get("GAMSCFG_PROJECT_TOML"))
        #     safe_hosts = config.general.safe_xml_hosts
        # except  MissingConfigurationException:
        #     # if no configuration file was found we try to extract hosts from the from the environment
        #     safe_hosts = re.split(r'\s*,\s*',os.environ.get("GAMSLIB_SAFE_XML_HOSTS", ""))

        # uri = urlparse(schema_uri)
        # return (
        #     uri.scheme in ("http", "https")
        #     and uri.hostname in safe_hosts
        # )


        
    # def get_content(self, schema_url: str) -> bytes:
    #     """Return content of URL by using the resolver. 
        
    #     This works like resolve(), but returns the raw content instead of 
    #     a file path or file-like object.
    #     """
    #     # We cannot relay on libxml2 here, because we need access to the resolved content directly
    #     # So we have to do the catalog lookup by hand
    #     catalog_path = gams_xml_catalog.get_catalog_path()
    #     catalog = ET.XMLCatalog(catalog_path.as_posix())
    #     actual_path = catalog.resolve(schema_url)
    #     # is uri in catalog?
    #     if actual_path is not None:
    #         with open(actual_path, 'rb') as f:
    #             return f.read()
    #     # is host allowed?
    #     if not self._is_allowed_host(schema_url):
    #         raise ValueError(f"Host of URL '{schema_url}' is not in the allowed list.")
    #     # is content in cache?
    #     cache_path = self.get_cache_path(schema_url)
    #     if cache_path is not None and Path(cache_path).is_file():
    #         with open(cache_path, 'rb') as f:
    #             return f.read()
    #     # try to download content
    #     try:
    #         response = requests.get(schema_url, timeout=10)
    #         response.raise_for_status()
    #         return response.content
    #     except Exception as exp:
    #         logger.warning("Something unexpected happened while loading schema %s: %s", schema_url, exp)
    #         raise exp from exp    


    def _is_allowed_host(self, url: str) -> bool:
        """Check if the host of the given URL is in the allowed list."""
        uri = urlparse(url)
        host = (uri.hostname or "").lower()
        return host in {entry.lower() for entry in self.allowed_hosts}

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
