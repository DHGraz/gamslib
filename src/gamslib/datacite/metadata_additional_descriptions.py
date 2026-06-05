"""Additional-description DataCite metadata models."""

from pydantic import BaseModel

from gamslib.datacite.common import (
    Iso639ThreeLanguage,
    LocalizedTitle,
)
from gamslib.datacite.vocabularies import AdditionalDescriptionTypeId

AdditionalDescriptionTitle = LocalizedTitle
AddtionalDescriptionLang = Iso639ThreeLanguage


class AdditionalDescriptionType(BaseModel):
    """Identifies the type of an additional description."""

    id: AdditionalDescriptionTypeId
    title: LocalizedTitle


class AdditionalDescription(BaseModel):
    """Represents an additional description for a record."""

    description: str
    type: AdditionalDescriptionType
    lang: AddtionalDescriptionLang | None = None
