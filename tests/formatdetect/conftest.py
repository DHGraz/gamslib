import os
import pytest
from pathlib import Path
from dataclasses import dataclass

from gamslib.formatdetect.minimaldetector import MinimalDetector
from gamslib.formatdetect.magikadetector import MagikaDetector
from gamslib.formatdetect.formatinfo import SubType


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
    formatdatadir = Path(__file__).parent / "data"
    return [
        TestFormatFile(formatdatadir / "csv.csv", "text/csv"),
        TestFormatFile(formatdatadir / "iiif_manifest.json", "application/ld+json", SubType.JSONLD),
        TestFormatFile(formatdatadir / "image.bmp", "image/bmp"),
        TestFormatFile(formatdatadir / "image.gif", "image/gif"),
        TestFormatFile(formatdatadir / "image.jp2", "image/jp2"),  
        TestFormatFile(formatdatadir / "image.jpg", "image/jpeg"),
        TestFormatFile(formatdatadir / "image.jpeg", "image/jpeg"),
        TestFormatFile(formatdatadir / "image.png", "image/png"),
        TestFormatFile(formatdatadir / "image.tif", "image/tiff"),
        TestFormatFile(formatdatadir / "image.tiff", "image/tiff"),
        TestFormatFile(formatdatadir / "image.webp", "image/webp"),
        TestFormatFile(formatdatadir / "json_ld.json", "application/ld+json", SubType.JSONLD),
        TestFormatFile(formatdatadir / "json_ld.jsonld", "application/ld+json", SubType.JSONLD),
        TestFormatFile(formatdatadir / "json_schema.json", "application/json", SubType.JSONSCHEMA), 
        TestFormatFile(formatdatadir / "json.json", "application/json", SubType.JSON),
        TestFormatFile(formatdatadir / "jsonl.json", "application/json", SubType.JSONL),
        TestFormatFile(formatdatadir / "markdown.md", "text/markdown"),
        TestFormatFile(formatdatadir / "pdf.pdf", "application/pdf"),
        TestFormatFile(formatdatadir / "pdf-a_3b.pdf", "application/pdf"),
        TestFormatFile(formatdatadir / "text.txt", "text/plain"),
        TestFormatFile(formatdatadir / "xml_lido.xml", "application/xml", SubType.LIDO),
        TestFormatFile(formatdatadir / "xml_no_ns.xml", "application/xml"),        
        TestFormatFile(formatdatadir / "xml_tei.xml", "application/tei+xml", SubType.TEI),  
        TestFormatFile(formatdatadir / "xml_tei_with_rng.xml", "application/tei+xml", SubType.TEI),
    ]
