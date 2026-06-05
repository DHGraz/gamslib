"""Additional-title DataCite metadata models."""

from pydantic import BaseModel

from gamslib.datacite.common import (
    Iso639ThreeLanguage,
    LocalizedTitle,
)
from gamslib.datacite.vocabularies import AdditionalTitleTypeId

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
