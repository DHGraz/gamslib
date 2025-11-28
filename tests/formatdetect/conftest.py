""""Conftest for format detection tests."""
#import os
from dataclasses import dataclass
from pathlib import Path

import pytest

from gamslib.formatdetect.formatinfo import SubType
#from gamslib.formatdetect.magikadetector import MagikaDetector
#from gamslib.formatdetect.minimaldetector import MinimalDetector


@dataclass
class TestFormatFile():
    "Data about a file fom the data subdirectory."
    filepath: Path
    mimetype: str
    subtype: SubType|None = None


@pytest.fixture
def formatdatadir(request):
    return Path(request.module.__file__).parent / "data"

def get_testfiles():
    "Return a list of test files for formatdetection."
    formatdatadir_ = Path(__file__).parent / "data"
    return [
        TestFormatFile(formatdatadir_ / "csv.csv", "text/csv"),
        TestFormatFile(formatdatadir_ / "iiif_manifest.json", "application/ld+json", SubType.JSONLD),
        TestFormatFile(formatdatadir_ / "image.bmp", "image/bmp"),
        TestFormatFile(formatdatadir_ / "image.gif", "image/gif"),
        TestFormatFile(formatdatadir_ / "image.jp2", "image/jp2"),  
        TestFormatFile(formatdatadir_ / "image.jpg", "image/jpeg"),
        TestFormatFile(formatdatadir_ / "image.jpeg", "image/jpeg"),
        TestFormatFile(formatdatadir_ / "image.png", "image/png"),
        TestFormatFile(formatdatadir_ / "image.tif", "image/tiff"),
        TestFormatFile(formatdatadir_ / "image.tiff", "image/tiff"),
        TestFormatFile(formatdatadir_ / "image.webp", "image/webp"),
        TestFormatFile(formatdatadir_ / "json_ld.json", "application/ld+json", SubType.JSONLD),
        TestFormatFile(formatdatadir_ / "json_ld.jsonld", "application/ld+json", SubType.JSONLD),
        TestFormatFile(formatdatadir_ / "json_schema.json", "application/json", SubType.JSONSCHEMA), 
        TestFormatFile(formatdatadir_ / "json.json", "application/json", SubType.JSON),
        TestFormatFile(formatdatadir_ / "jsonl.json", "application/json", SubType.JSONL),
        TestFormatFile(formatdatadir_ / "markdown.md", "text/markdown"),
        TestFormatFile(formatdatadir_ / "pdf.pdf", "application/pdf"),
        TestFormatFile(formatdatadir_ / "pdf-a_3b.pdf", "application/pdf"),
        TestFormatFile(formatdatadir_ / "text.txt", "text/plain"),
        TestFormatFile(formatdatadir_ / "xml_lido.xml", "application/xml", SubType.LIDO),
        TestFormatFile(formatdatadir_ / "xml_no_ns.xml", "application/xml"),        
        TestFormatFile(formatdatadir_ / "xml_tei.xml", "application/tei+xml", SubType.TEI),  
        TestFormatFile(formatdatadir_ / "xml_tei_with_rng.xml", "application/tei+xml", SubType.TEI),
    ]
