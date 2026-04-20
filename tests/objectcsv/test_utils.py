"""Tests for utility helpers in objectcsv.utils."""

from pathlib import Path

import pytest

from gamslib.objectcsv.utils import (
        extract_title_from_lido,
        extract_title_from_tei,
        find_object_root,
        split_entry,
)


def test_split_entry():
        """Split semicolon-delimited values and trim whitespace."""
        assert split_entry("foo; bar ;baz") == ["foo", "bar", "baz"]
        assert split_entry("foo,bar") == ["foo,bar"]
        assert split_entry("") == []
        assert split_entry(" ;  ; ") == []


def test_extract_title_from_tei(tmp_path: Path):
        """Return title text from a TEI document when the node exists."""
        tei_file = tmp_path / "TEI.xml"
        tei_file.write_text(
                """
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <teiHeader>
        <fileDesc>
            <titleStmt>
                <title>The TEI Title</title>
            </titleStmt>
        </fileDesc>
    </teiHeader>
</TEI>
""".strip(),
                encoding="utf-8",
        )

        assert extract_title_from_tei(tei_file) == "The TEI Title"


def test_extract_title_from_tei_missing_title_returns_empty_string(tmp_path: Path):
        """Return empty string when no TEI title node is present."""
        tei_file = tmp_path / "TEI.xml"
        tei_file.write_text(
                """
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <teiHeader>
        <fileDesc>
            <titleStmt />
        </fileDesc>
    </teiHeader>
</TEI>
""".strip(),
                encoding="utf-8",
        )

        assert extract_title_from_tei(tei_file) == ""


def test_extract_title_from_lido(tmp_path: Path):
        """Return title text from a LIDO document when the node exists."""
        lido_file = tmp_path / "LIDO.xml"
        lido_file.write_text(
                """
<lido:lido xmlns:lido="http://www.lido-schema.org">
    <lido:descriptiveMetadata>
        <lido:objectIdentificationWrap>
            <lido:titleWrap>
                <lido:titleSet>
                    <lido:appellationValue>LIDO title</lido:appellationValue>
                </lido:titleSet>
            </lido:titleWrap>
        </lido:objectIdentificationWrap>
    </lido:descriptiveMetadata>
</lido:lido>
""".strip(),
                encoding="utf-8",
        )

        assert extract_title_from_lido(lido_file) == "LIDO title"


def test_extract_title_from_lido_missing_title_returns_empty_string(tmp_path: Path):
        """Return empty string when no LIDO title node is present."""
        lido_file = tmp_path / "LIDO.xml"
        lido_file.write_text(
                """
<lido:lido xmlns:lido="http://www.lido-schema.org">
    <lido:descriptiveMetadata>
        <lido:objectIdentificationWrap>
            <lido:titleWrap />
        </lido:objectIdentificationWrap>
    </lido:descriptiveMetadata>
</lido:lido>
""".strip(),
                encoding="utf-8",
        )

        assert extract_title_from_lido(lido_file) == ""


def test_find_object_root_finds_parent_with_dc_xml(tmp_path: Path):
    """Return the nearest parent directory that contains DC.XML."""
    object_root = tmp_path / "obj1"
    nested_dir = object_root / "content" / "images"
    nested_dir.mkdir(parents=True)
    (object_root / "DC.XML").write_text("<dc/>", encoding="utf-8")

    assert find_object_root(nested_dir) == object_root


def test_find_object_root_raises_if_dc_xml_not_found(tmp_path: Path):
    """Raise FileNotFoundError when no DC.XML exists up the path chain."""
    start_path = tmp_path / "obj2" / "content"
    start_path.mkdir(parents=True)

    with pytest.raises(FileNotFoundError):
        find_object_root(start_path)
