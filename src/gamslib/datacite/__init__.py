"""Compatibility facade for the top-level DataCite record model."""

from gamslib.datacite import datacite_record


DataCite = datacite_record.DataCite


__all__ = ["DataCite"]
