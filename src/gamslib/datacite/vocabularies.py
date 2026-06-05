"""Vocabularies for DataCite metadata fields."""

from enum import StrEnum
from typing import Literal

IdentifierScheme = Literal["orcid", "gnd", "isni", "ror"]
PersonOrOrganizationType = Literal["personal", "organizational"]
AffiliationId = Literal["isni", "ror"]
CreatorRole = Literal["creator", "contributor"]
AdditionalTitleTypeId = Literal[
    "subtitle",
    "alternative-title",
    "translated-title",
    "other",
]
AdditionalDescriptionTypeId = Literal[
    "abstract",
    "methods",
    "series-information",
    "table-of-contents",
    "technical-info",
    "other",
]
ContributorRole = Literal[
    "editor",
    "funder",
    "project_leader",
    "project_manager",
    "other",
]
DateTypeId = Literal[
    "accepted",
    "available",
    "collected",
    "copyrighted",
    "created",
    "issued",
    "other",
    "submitted",
    "updated",
    "valid",
    "withdrawn",
]
Format = Literal[
    "application/json",
    "application/xml",
    "text/csv",
    "application/pdf",
    "application/zip",
    "image/jpeg",
    "image/png",
    "text/plain",
    "image/tiff",
]


class MetadataIdentifier(StrEnum):
    """Identifies a metadata identifier as type-subtype."""

    # TODO: Add other identifier types when decidesd on a final set.
    IMAGE_PHOTO = "image-photo"


class AlternateIdentifierSchema(StrEnum):
    """Identifies an alternate identifier as type-subtype."""

    # these are the values allowed for the alternateIdentifierType field
    # in the DataCite schema.
    ARK = "ark"
    ARXIV = "arxiv"
    ADS = "ads"
    CROSSREFFUNDERID = "crossreffunderid"
    DOI = "doi"
    EAN13 = "ean13"
    EISSN = "eissn"
    GRID = "grid"
    HANDLE = "handle"
    IGSN = "igsn"
    ISBN = "isbn"
    ISNI = "isni"
    ISSN = "issn"
    ISTC = "istc"
    LISSN = "lissn"
    LSID = "lsid"
    PMID = "pmid"
    PURL = "purl"
    UPC = "upc"
    URL = "url"
    URN = "urn"
    W3ID = "w3id"
    OTHER = "other"


class RelatedIdentifierSchema(StrEnum):
    """Identifies a related identifier."""

    # these are the values allowed for the relatedIdentifierType field
    # in the DataCite schema.
    ARK = "ark"
    ARXIV = "arxiv"
    BIBCODE = "bibcode"
    DOI = "doi"
    EAN13 = "ean13"
    EISSN = "eissn"
    HANDLE = "handle"
    IGSN = "igsn"
    ISBN = "isbn"
    ISSN = "issn"
    ISTC = "istc"
    LISSN = "lissn"
    LSID = "lsid"
    PUBMED = "pubmed"
    ID = "id"
    PURL = "purl"
    UPC = "upc"
    URL = "url"
    URN = "urn"
    W3ID = "w3id"


class RelationTypeVocabulary(StrEnum):
    """A catalog of defined relation types.

    See https://github.com/inveniosoftware/invenio-rdm-records/blob/master/invenio_rdm_records/fixtures/data/vocabularies/relation_types.yaml
    """

    ISCITEDBY = "iscitedby"
    CITES = "cites"
    ISSUPPLEMENTTO = "issupplementTo"
    ISSUPPLEMENTEDBY = "issupplementedBy"
    ISCONTINUEDBY = "iscontinuedBy"
    CONTINUES = "continues"
    ISDESCRIBEDBY = "isdescribedby"
    DESCIBES = "describes"
    HASMETADATA = "hasmetadata"
    ISMETADATAFOR = "ismetadatafor"
    HASVERSION = "hasversion"
    ISVERSIONOF = "isversionOf"
    ISNEWVERSIONOF = "isnewversionof"
    ISPREVIOUSVERSIONOF = "ispreviousversionof"
    ISPARTOF = "ispartOf"
    HASPART = "haspart"
    ISPUBLISHEDIN = "ispublishedIn"
    ISREFERENCEDBY = "isreferencedby"
    REFERENCES = "references"
    ISDOCUMENTEDBY = "isdocumentedby"
    DOCUMENTS = "documents"
    ISCOMPILEDBY = "iscompiledby"
    COMPILES = "compiles"
    ISVARIANTFORMOF = "isvariantformof"
    ISORIGINALFORMOF = "isoriginalformof"
    ISIDENTICALTO = "isidenticalto"
    ISREVIEWEDBY = "isreviewedby"
    REVIEWS = "reviews"
    ISDERIVEDFROM = "isderivedfrom"
    ISSOURCEOF = "issourceof"
    ISREQUIREDBY = "isrequiredby"
    REQUIRES = "requires"
    ISOBSOLETEDBY = "isobsoletedby"
    OBSOLETES = "obsoletes"
    ISCOLLECTEDBY = "iscollectedby"
    COLLECTS = "collects"
    ISTRANSLATIONOF = "istranslationof"
    HASTRANSLATION = "hastranslation"
    OTHER = "other"
