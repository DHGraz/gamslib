"""Dublin Core metadata access for GAMS objects.

Provides the DublinCore class for parsing DC.xml files and accessing metadata elements
with language preference and fallback logic. Includes utility methods for retrieving
element values as lists or strings, and for removing linebreaks from text.

Features:
    - Parse DC.xml and extract Dublin Core elements with language support.
    - Retrieve metadata values in preferred language, with fallback to alternatives.
    - Utility for joining multiple values and formatting rights statements.
    - Configurable lookup order for language fallback.
"""

import logging
from pathlib import Path
import re
from typing import Any
from lxml import etree as ET

logger = logging.getLogger(__name__)

# DC_ELEMENTS: List of supported Dublin Core elements.
DC_ELEMENTS = [
    "contributor",
    "coverage",
    "creator",
    "date",
    "description",
    "format",
    "identifier",
    "language",
    "publisher",
    "relation",
    "rights",
    "source",
    "subject",
    "title",
    "type",
]


# DCMI_TYPES: List of DCMI type values.
DCMI_TYPES = [
    "Collection",
    "Dataset",
    "Event",
    "Image",
    "InteractiveResource",
    "MovingImage",
    "PhysicalObject",
    "Service",
    "Software",
    "Sound",
    "StillImage",
    "Text",
]

NAMESPACES = {
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
    "dcmitype": "http://purl.org/dc/dcmitype/",
    "rdf": "http://www.w3.org/1999/02/22-rdf",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xml": "http://www.w3.org/XML/1998/namespace",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
}

# The following elements are required by GAMS we add the namespace to avoid confusion
REQUIRED_GAMS_ELEMENTS = ["identifier", "title", "rights"]


class DublinCore:
    """Represents data from DC.xml.

    Provides methods to access DC data with language support, and to validate the minimal
    GAMS requirements for the DX.XML file.
    """

    UNSPECIFIED_LANG = "unspecified"

    def __init__(
        self, path: Path, lookup_order: tuple = ("en", "de", "fr", "es", "it")
    ):
        """
        Initialize and parse the DC.xml file.

        Args:
            path (Path): Path to the DC.xml file.
            lookup_order (tuple): Preferred language order for fallback.
        """
        self.path: Path = path
        self.lookup_order: list[str] = list(lookup_order)
        self._data: dict[str, Any] = {}  # [element][lang] = text
        self._parse(path)

    def _parse(self, path: Path):
        try:
            tree = ET.parse(path)  # pylint: disable=c-extension-no-member
            root = tree.getroot()

            for elem in DC_ELEMENTS:
                for child in root.findall(f"dc:{elem}", namespaces=NAMESPACES):
                    lang = child.attrib.get(
                        f"{{{NAMESPACES['xml']}}}lang", self.UNSPECIFIED_LANG
                    )
                    element = self._data.get(elem, {})
                    values = element.get(lang, [])
                    if child.text is not None:
                        values.append(child.text)
                    element[lang] = values
                    self._data[elem] = element
        except ET.ParseError as e:  # pylint: disable=c-extension-no-member
            logger.error("Error parsing XML file %s: %s", self.path, e)
            raise ValueError(f"Error parsing {self.path}: {e}") from e

    @classmethod
    def remove_linebreaks(cls, text: str) -> str:
        """
        Remove linebreaks from a string.

        Args:
            text (str): The string to remove linebreaks from.

        Returns:
            str: The string without linebreaks.
        """
        return re.sub(r"[\r\n]+", " ", text).strip()

    def get_en_element(self, name: str, default="") -> list[str]:
        """
        Return the value(s) of a Dublin Core element in English.
        If no English value is found, return the default value.

        Args:
            name (str): The name of the element without namespace (e.g. "title").
            default (str): Default value if element is missing.

        Returns:
            list[str]: The value(s) of the element as a list of strings.

        Raises:
            ValueError: If the element name is not a valid Dublin Core element.
        """
        if name not in DC_ELEMENTS:
            raise ValueError(f"Element {name} is not a Dublin Core element.")

        values = self._data[name].get("en", [])
        if not values and default != "":
            values = [default]
        return [self.remove_linebreaks(value) for value in values]

    def get_en_element_as_str(self, name: str, default="") -> str:
        """
        Return all entries of a Dublin Core element in English as string.

        Entries are separated by '; '.

        Delimi

        Args:
            name (str): The name of the element without namespace (e.g. "title").
            default (str): Default value if element is missing.

        Returns:
            str: The joined value(s) of the element as a string. Multiple values 
            are separated by ';'.

        Raises:
            ValueError: If the element name is not a valid Dublin Core element.
        """
        return "; ".join(self.get_en_element(name, default=default))

    def get_element(
        self, name: str, preferred_lang: str = "en", default: str = ""
    ) -> list[str]:
        """
        Return the value(s) of a Dublin Core element as a list of strings.

        If no entry in the preferred language is available, the function will search
        for entries in another language, depending on the lookup_order set during
        object creation. If no entry is found with a specified language, the function
        checks for an entry with no 'xml:lang' attribute. If still no value is found,
        the default value will be returned (as a list).

        Args:
            name (str): The name of the element without namespace (e.g. "title").
            preferred_lang (str): The preferred language of the element (e.g. "de").
            default (str): The default value to return if no value is found.

        Returns:
            list[str]: The value(s) of the element as a list of strings.

        Raises:
            ValueError: If the element name is not a valid Dublin Core element.

        """
        if name not in DC_ELEMENTS:
            raise ValueError(f"Element {name} is not a Dublin Core element.")
        # element not in DC.xml
        if name not in self._data:
            logger.debug(
                "Element '%s{name}' not found in %s{self.path}. Returning default value: [%s]",
                name,
                self.path,
                default,
            )
            return [default]

        # search for an entry in desired language
        if preferred_lang not in self._data[name]:
            # search for another language in defined lookup order
            alternative_lang = self.UNSPECIFIED_LANG
            for lang in self.lookup_order:
                if lang in self._data[name]:
                    alternative_lang = lang
                    break
            if alternative_lang == self.UNSPECIFIED_LANG:
                # no entry for any lang in lookup_order, so we use the first entry without lang
                logger.debug(
                    "Preferred language '%s{preferred_lang}' not found in %s{self.path}. "
                    "Using first entry without xml:lang attribute instead.",
                    preferred_lang,
                    self.path,
                )
            # we found an alternative lang
            else:
                logger.debug(
                    "Preferred language '%s{preferred_lang}' not found in %s{self.path}. "
                    "Using value for language '%s{alternative_lang}' instead.",
                    preferred_lang,
                    self.path,
                    alternative_lang,
                )
            preferred_lang = alternative_lang

        return [
            self.remove_linebreaks(value) for value in self._data[name][preferred_lang]
        ]

    def get_element_as_str(
        self, name: str, preferred_lang: str = "en", default: str = ""
    ) -> str:
        """
        Return the value(s) of a Dublin Core element as a string.

        Args:
            name (str): The name of the element without namespace.
            preferred_lang (str): The preferred language of the element.
            default (str): The default value to return if no value is found.

        Returns:
            str: The value(s) as a single string. For 'rights', formats as "name (url)" 
            if two values are present; otherwise, values are joined with ';'.
        """
        values = self.get_element(name, preferred_lang, default)
        if name == "rights":
            # we expect the licence name first, followed by the url in brackets
            str_value = values[0] if len(values) == 1 else f"{values[0]} ({values[1]})"
        else:
            str_value = "; ".join(values)
        return str_value

    def get_element_all_langs(self, name: str) -> list[str]:
        """
        Return all values of a Dublin Core element for all languages.

        This includes unspecified languages.

        Args:
            name (str): The name of the element without namespace (e.g. "title").

        Returns:
            list[str]: A list of all values for the element in all available 
            languages (including unspecified).
            If the element is not found, an empty list is returned.

        Raises:
            ValueError: If the element name is not a valid Dublin Core element.
        """
        if name not in DC_ELEMENTS:
            raise ValueError(f"Element {name} is not a Dublin Core element.")

        result: list[str] = []
        for values in self._data.get(name, {}).values():
            result.extend([self.remove_linebreaks(value) for value in values])
        return result

    def _check_for_unkown_elements(self):
        """
        Check if any unknown elements are present in the Dublin Core file.

        Raises:
            ValueError: If an unknown element is found.
        """
        dc_elements_with_ns = [
            f"{{{NAMESPACES['dc']}}}{element}" for element in DC_ELEMENTS
        ]
        root = ET.parse(self.path).getroot()  # pylint: disable=c-extension-no-member
        for child in root:
            if child.tag not in dc_elements_with_ns:
                # replace the clark notation by the common ns prefix for better readability
                short_ns_prefix = child.tag.replace(f"{{{NAMESPACES['dc']}}}", "dc:")
                logger.error(
                    "Unknown Dublin Core element '%s' found in %s.",
                    short_ns_prefix,
                    self.path,
                )
                raise ValueError(
                    f"Unknown Dublin Core element '{short_ns_prefix}' found in {self.path}"
                )

    def validate(self):
        """
        Validate the Dublin Core file.

        Raises:
            ValueError: If the Dublin Core file is invalid.
        """
        self._check_for_unkown_elements()
        for name in REQUIRED_GAMS_ELEMENTS:
            if name not in self._data:
                raise ValueError(
                    f"{self.path}: Required Dublin Core element '{name}' is missing in DC.xml."
                )
            if not self.get_element_all_langs(name):
                raise ValueError(
                    f"{self.path}: Required Dublin Core element '{name}' has no value in DC.xml."
                )
        if self.get_en_element("title") == []:
            raise ValueError(
                f'{self.path}: A <title xml:lang="en"> element is required in DC.xml.'
            )
