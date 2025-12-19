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
    pronom_id: str|None = None
    subtype: SubType|None = None


@pytest.fixture
def formatdatadir(request):
    return Path(request.module.__file__).parent / "data"

def get_testfiles():
    "Return a list of test files for formatdetection."
    formatdatadir_ = Path(__file__).parent / "data"
    return [
        TestFormatFile(formatdatadir_ / "csv.csv", "text/csv", "x-fmt/18"),
        TestFormatFile(formatdatadir_ / "iiif_manifest.json", "application/ld+json", "fmt/880", SubType.JSONLD),
        TestFormatFile(formatdatadir_ / "image.bmp", "image/bmp", "fmt/119"),
        TestFormatFile(formatdatadir_ / "image.gif", "image/gif", "fmt/4"),
        TestFormatFile(formatdatadir_ / "image.jp2", "image/jp2", "x-fmt/392"),
        TestFormatFile(formatdatadir_ / "image.jpg", "image/jpeg", "fmt/43"),
        TestFormatFile(formatdatadir_ / "image.jpeg", "image/jpeg", "fmt/43"),
        TestFormatFile(formatdatadir_ / "image.png", "image/png", "fmt/11"),
        TestFormatFile(formatdatadir_ / "image.tif", "image/tiff", "fmt/353"),
        TestFormatFile(formatdatadir_ / "image.tiff", "image/tiff", "fmt/353"),
        TestFormatFile(formatdatadir_ / "image.webp", "image/webp", "fmt/566"),
        TestFormatFile(formatdatadir_ / "json_ld.json", "application/ld+json", "fmt/880", SubType.JSONLD),
        TestFormatFile(formatdatadir_ / "json_ld.jsonld", "application/ld+json", "fmt/880", SubType.JSONLD),
        TestFormatFile(formatdatadir_ / "json_schema.json", "application/json", "fmt/817", SubType.JSONSCHEMA), 
        TestFormatFile(formatdatadir_ / "json.json", "application/json", "fmt/817", SubType.JSON),
        TestFormatFile(formatdatadir_ / "jsonl.json", "application/json", "fmt/817", SubType.JSONL),
        TestFormatFile(formatdatadir_ / "markdown.md", "text/markdown", "fmt/1149"),
        TestFormatFile(formatdatadir_ / "pdf.pdf", "application/pdf", "fmt/19"),
        TestFormatFile(formatdatadir_ / "pdf-a_3b.pdf", "application/pdf", "fmt/480"),
        TestFormatFile(formatdatadir_ / "tar_gz.tgz", "application/gzip", "x-fmt/266"),
        TestFormatFile(formatdatadir_ / "tar_bz2.tar.bz2", "application/x-bzip2", "x-fmt/268"),
        TestFormatFile(formatdatadir_ / "tar_xz.tar.xz", "application/x-xz", "fmt/1098"),
        TestFormatFile(formatdatadir_ / "tar.tar", "application/x-tar", "x-fmt/265"),
        TestFormatFile(formatdatadir_ / "tar_lzma.tar.lzma", "application/x-tar", "x-fmt/265"),    
        TestFormatFile(formatdatadir_ / "text.txt", "text/plain", "x-fmt/111"),
        TestFormatFile(formatdatadir_ / "xml_lido.xml", "application/xml", "fmt/101",SubType.LIDO),
        TestFormatFile(formatdatadir_ / "xml_no_ns.xml", "application/xml", "fmt/101"),        
        TestFormatFile(formatdatadir_ / "xml_tei.xml", "application/tei+xml", "fmt/1476",SubType.TEIP5),  
        TestFormatFile(formatdatadir_ / "xml_tei_p4.xml", "application/tei+xml", "fmt/1474",SubType.TEIP4),  
        TestFormatFile(formatdatadir_ / "xml_tei_with_rng.xml", "application/tei+xml", "fmt/1476",SubType.TEIP5),
        TestFormatFile(formatdatadir_ / "zip.zip", "application/zip", "x-fmt/263"),
    ]
