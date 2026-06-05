"""Location models for DataCite metadata.location field."""

from pydantic import BaseModel, Field


class GeoLocationIdentifier(BaseModel):
    """A geolocation identifier.

    Compatible with the DataCite schema for GeoLocation.
    """

    # TODO: validate against a controlled vocabulary of schemes,
    # e.g. "geonames", "geopoint", etc.
    # I did not find an official list of valid schemes in the DataCite
    # documentation, but it would be good to have some validation here.
    scheme: str
    identifier: str


class Geometry(BaseModel):
    """A a GeoJSON geometry.

    Compatible with the DataCite schema for GeoLocation.
    """

    # TODO: this should be one of "Point", "LineString", "Polygon", etc.
    # according to the GeoJSON specification, but the DataCite schema
    # does not seem to enforce this.
    type: str
    coordinates: list[float] | list[list[float]] | list[list[list[float]]]


class GeoJSONFeature(BaseModel):
    """A class representing a GeoJSON feature.
    
    Compatible with the DataCite schema for GeoLocation.
    """

    geometry: Geometry | None = None
    identifiers: list[GeoLocationIdentifier] = Field(default_factory=list)
    place: str | None = None
    description: str | None = None


class Location(BaseModel):
    """A location class compatible with the DataCite schema for GeoLocation."""

    features: GeoJSONFeature
