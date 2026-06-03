"""Additional-description DataCite metadata models."""

from pydantic import BaseModel

from gamslib.datacite.metadata_common import (
    AdditionalDescriptionTypeId,
    Iso639ThreeLanguage,
    LocalizedTitle,
)

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
