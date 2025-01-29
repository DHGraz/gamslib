from dataclasses import dataclass


@dataclass
class FormatInfo:

    detector: str  # name of the detector that detected the format
    mimetype: str  # text/xml
    subtype: str | None = None  # e.g. tei or json-ld
    