"""Additional-title DataCite metadata models."""

from pydantic import BaseModel

from gamslib.datacite.metadata_common import (
    AdditionalTitleTypeId,
    Iso639ThreeLanguage,
    LocalizedTitle,
)


AdditionalTitleLang = Iso639ThreeLanguage


class AdditionalTitleType(BaseModel):
    """Identifies the type of an additional title."""

    id: AdditionalTitleTypeId
    title: LocalizedTitle


class AdditionalTitle(BaseModel):
    """Represents an additional title for a record."""

    title: str
    type: AdditionalTitleType
    lang: str | None = None