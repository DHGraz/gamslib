"""Represents data from DC.xml and provides some methods to access it."""

import logging
from pathlib import Path
import re
from typing import Any
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)

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

## DC_TERMS and DCMI_TYPES are not used in the current implementation,
## but are kept here for future reference.
# DC_TERMS = [
#     "abstract",
#     "accessRights",
#     "accrualMethod",
#     "accrualPeriodicity",
#     "accrualPolicy",
#     "alternative",
#     "audience",
#     "available",
#     "bibliographicCitation",
#     "conformsTo",
#     "created",
#     "dateAccepted",
#     "dateCopyrighted",
#     "dateSubmitted",
#     "educationLevel",
#     "extent",
#     "hasFormat",
#     "hasPart",
#     "hasVersion",
#     "instructionalMethod",
#     "isFormatOf",
#     "isPartOf",
#     "isReferencedBy",
#     "isReplacedBy",
#     "isRequiredBy",
#     "issued",
#     "isVersionOf",
#     "license",
#     "mediator",
#     "medium",
#     "modified",
#     "provenance",
#     "references",
#     "replaces",
#     "requires",
#     "rightsHolder",
#     "spatial",
#     "tableOfContents",
#     "temporal",
#     "valid",
# ]

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


# class DublinCoreWarning(UserWarning):
#     """Warning for missing Dublin Core elements.

#     This warning is raised when a requested element is not found
#     in the Dublin Core data and a default value is used instead.
#     """

# class MissingLangWarning(DublinCoreWarning):
#     """Warning for missing language in Dublin Core elements.

#     This warning is raised when a requested language (xml:lang) is not
#     found in the Dublin Core data.
#     """


class DublinCore:
    """Represents data from DC.xml and provides some methods to access it."""

    UNSPECIFIED_LANG = "unspecified"

    def __init__(
        self, path: Path, lookup_order: tuple = ("en", "de", "fr", "es", "it")
    ):
        self.path: Path = path
        self.lookup_order: list[str] = list(lookup_order)
        self._data: dict[str, Any] = {}  # [element][lang] = text
        self._parse(path)

    def _parse(self, path: Path):
        tree = ET.parse(path)
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
        # TODO: Add DC_TERMS and DCMI_TYPES?

    @classmethod
    def remove_linebreaks(cls, text: str) -> str:
        """Remove linebreaks from a string.

        :param str text: The string to remove linebreaks from.
        :return: The string without linebreaks.
        """
        return re.sub(r"[\r\n]+", " ", text).strip()

    def get_en_element(self, name: str, default="") -> list[str]:
        """Return the value of a Dublin Core element in English.

        It always returns a list of strings, even if only one value or no element is available.

        :param str name: The name of the element without namespace (e.g. "title").
        :return: The value(s) of the element as list of strings.
        :raises ValueError: If the element name is not a valid Dublin Core element.
        """
        if name not in DC_ELEMENTS:
            raise ValueError(f"Element {name} is not a Dublin Core element.")

        values = self._data[name].get("en", [])
        if not values and default != "":
            values = [default]
        return [self.remove_linebreaks(value) for value in values]

    def get_en_element_as_str(self, name: str, default="") -> str:
        """Return the joint values of a Dublin Core element in English.

        :param str name: The name of the element without namespace (e.g. "title").
        :return: The joint value(s) of the element as string. Multiple values are separated by ';'.
        :raises ValueError: If the element name is not a valid Dublin Core element.
        """

        return "; ".join(self.get_en_element(name, default=default))

    def get_element(
        self, name: str, preferred_lang: str = "en", default: str = ""
    ) -> list[str]:
        """Return the value of a Dublin Core element as list of strings.

        This method is able to deal with multiple values of the same element in different languages.
        Returns always a list of strings, because in DC an element can have multiple values.

        :param str name: The name of the element without namespace (e.g. "title").
        :param str preferred_lang: The preferred language of the element (eg. "de").
            * Default value is "en".
            * If no entry in this language is available, the function will search
              for entries in another language, depending on the lookup_order, set during
              object creation. If no entry is found with a specified language, the function
              checks for an entry with no 'xml:lang' attribute.
              If still no value is found, the default value will be returned (als list!)
        :param str default: The default value to return if no value is found. Be aware, that this
            value will be returned as list element, even if it is a string.
        :return: The value(s) of the element as list of strings.
        :raises ValueError: If the element name is not a valid Dublin Core element.
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
        """Return the value(s) of a Dublin Core element as string.

        This is a wrapper around get_element() which returns a single
        string instead of a list.

        It is able to distinguish between different elements
        (eg. rights is handled differently than title).
        """
        values = self.get_element(name, preferred_lang, default)
        if name == "rights":
            # we expect the licence name first, followed by the url in brackets
            str_value = values[0] if len(values) == 1 else f"{values[0]} ({values[1]})"
        else:
            str_value = "; ".join(values)
        return str_value
