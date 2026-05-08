""" "Conftest for format detection tests."""

# import os
from dataclasses import dataclass
from pathlib import Path


from gamslib.formatdetect.formatinfo import SubType
# from gamslib.formatdetect.magikadetector import MagikaDetector
# from gamslib.formatdetect.minimaldetector import MinimalDetector

# from gamslib.formatdetect.magikadetector import MagikaDetector
# from gamslib.formatdetect.minimaldetector import MinimalDetector


@dataclass
class FormatFile:
    "Data about a file fom the data subdirectory."

    filepath: Path
    mimetype: str
    pronom_id: str | None = None
    subtype: SubType | None = None

    def __str__(self):
        return f"Testfile: {self.filepath.name}"


def get_testfiles() -> list[FormatFile]:
    """Return a list of test files for formatdetection.

    These files are located in the data dir of the test dire for formatdetect.
    """
    formatdatadir_ = Path(__file__).parent / "data"
    return [
        FormatFile(formatdatadir_ / "csv.csv", "text/csv", "x-fmt/18"),
        FormatFile(
            formatdatadir_ / "iiif_manifest.json",
            "application/ld+json",
            "fmt/880",
            SubType.JSONLD,
        ),
        FormatFile(formatdatadir_ / "image.bmp", "image/bmp", "fmt/119"),
        FormatFile(formatdatadir_ / "image.gif", "image/gif", "fmt/4"),
        FormatFile(formatdatadir_ / "image.jp2", "image/jp2", "x-fmt/392"),
        FormatFile(formatdatadir_ / "image.jpg", "image/jpeg", "fmt/43"),
        FormatFile(formatdatadir_ / "image.jpeg", "image/jpeg", "fmt/43"),
        FormatFile(formatdatadir_ / "image.png", "image/png", "fmt/11"),
        FormatFile(formatdatadir_ / "image.tif", "image/tiff", "fmt/353"),
        FormatFile(formatdatadir_ / "image.tiff", "image/tiff", "fmt/353"),
        FormatFile(formatdatadir_ / "image.webp", "image/webp", "fmt/566"),
        FormatFile(
            formatdatadir_ / "json_ld.json",
            "application/ld+json",
            "fmt/880",
            SubType.JSONLD,
        ),
        FormatFile(
            formatdatadir_ / "json_ld.jsonld",
            "application/ld+json",
            "fmt/880",
            SubType.JSONLD,
        ),
        FormatFile(
            formatdatadir_ / "json_schema.json",
            "application/json",
            "fmt/817",
            SubType.JSONSCHEMA,
        ),
        FormatFile(
            formatdatadir_ / "json.json", "application/json", "fmt/817", SubType.JSON
        ),
        FormatFile(
            formatdatadir_ / "jsonl.json", "application/json", "fmt/817", SubType.JSONL
        ),
        FormatFile(formatdatadir_ / "markdown.md", "text/markdown", "fmt/1149"),
        FormatFile(formatdatadir_ / "pdf.pdf", "application/pdf", "fmt/19"),
        FormatFile(formatdatadir_ / "pdf-a_3b.pdf", "application/pdf", "fmt/480"),
        FormatFile(formatdatadir_ / "tar_gz.tgz", "application/gzip", "x-fmt/266"),
        FormatFile(
            formatdatadir_ / "tar_bz2.tar.bz2", "application/x-bzip2", "x-fmt/268"
        ),
        FormatFile(formatdatadir_ / "tar_xz.tar.xz", "application/x-xz", "fmt/1098"),
        FormatFile(formatdatadir_ / "tar.tar", "application/x-tar", "x-fmt/265"),
        FormatFile(
            formatdatadir_ / "tar_lzma.tar.lzma", "application/x-tar", "x-fmt/265"
        ),
        FormatFile(formatdatadir_ / "text.txt", "text/plain", "x-fmt/111"),
        FormatFile(
            formatdatadir_ / "xml_dc.xml", "application/xml", "fmt/101", SubType.DCMI
        ),
        FormatFile(
            formatdatadir_ / "xml_dc_no_decl.xml",
            "application/xml",
            "fmt/101",
            SubType.DCMI,
        ),
        FormatFile(
            formatdatadir_ / "xml_lido.xml", "application/xml", "fmt/101", SubType.LIDO
        ),
        FormatFile(formatdatadir_ / "xml_no_ns.xml", "application/xml", "fmt/101"),
        FormatFile(
            formatdatadir_ / "xml_tei.xml",
            "application/tei+xml",
            "fmt/1476",
            SubType.TEIP5,
        ),
        FormatFile(
            formatdatadir_ / "xml_tei_missing_declaration.xml",
            "application/tei+xml",
            "fmt/1476",
            SubType.TEIP5,
        ),
        FormatFile(
            formatdatadir_ / "xml_tei_p4.xml",
            "application/tei+xml",
            "fmt/1474",
            SubType.TEIP4,
        ),
        FormatFile(
            formatdatadir_ / "xml_tei_with_rng.xml",
            "application/tei+xml",
            "fmt/1476",
            SubType.TEIP5,
        ),
        FormatFile(formatdatadir_ / "zip.zip", "application/zip", "x-fmt/263"),
    ]


def get_testfiles_from_validation() -> list[FormatFile]:
    """We have additional test files in the shared_datadir for validation tests.

    I'd like to re-use these for the format detection tests if those test files
    are available. This is, because running the validation tests showed, that
    format detection has issues with some of the test files.
    """

    validation_datadir = Path(__file__).parent.parent / "validation" / "data"
    return [
        FormatFile(
            validation_datadir / "DC.xml",
            "application/xml",
            "fmt/101",
            SubType.DCMI,
        ),
        FormatFile(
            validation_datadir / "lido.xml",
            "application/xml",
            "fmt/101",
            SubType.LIDO,
        ),
        FormatFile(
            validation_datadir / "mets.xml",
            "application/mets+xml",
            "fmt/101",
            SubType.METS,
        ),
        FormatFile(
            validation_datadir / "minimal_not_wellformed.xml",
            "application/xml",
            "fmt/101",
        ),
        FormatFile(
            validation_datadir / "minimal_wellformed.xml",
            "application/xml",
            "fmt/101",
        ),
        FormatFile(
            validation_datadir / "simple_with_external_dtd.xml",
            "application/xml",
            "fmt/101",
        ),
        FormatFile(
            validation_datadir / "simple_with_internal_dtd.xml",
            "application/xml",
            "fmt/101",
        ),
        FormatFile(
            validation_datadir / "tei_with_rng_and_schema.xml",
            "application/tei+xml",
            "fmt/1476",
            SubType.TEIP5,
        ),
        FormatFile(
            validation_datadir / "tei.xml",
            "application/tei+xml",
            "fmt/1476",
            SubType.TEIP5,
        ),
    ]
