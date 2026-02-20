"Tests for the schemadetector module."

import lxml.etree as ET
import pytest

# from gamslib.validation.xml import schemadetector
# from gamslib.validation.xml.schemainfo import SchemaInfo, XMLSchemaType
from gamslib.formatdetect.formatinfo import FormatInfo, SubType
from gamslib.validation import xmlschemadetector
from gamslib.validation.schemainfo import SchemaType
from unittest.mock import Mock

# pylint: disable=c-extension-no-member


def test_join_reference_same_dir(tmp_path):
    """join_reference resolves a relative schema reference.
    Test if it works if the xml file and schema file are in the same directory.
    """

    xml_file = tmp_path / "simple_with_rng_and_sch.xml"
    schema_reference = "simple.rng"
    schema_path = xml_file.parent / schema_reference
    schema_path.touch()
    new_path = xmlschemadetector.join_reference_path(xml_file, schema_reference)
    assert new_path == (xml_file.parent / schema_reference).as_uri()


def test_join_reference_relative_dir(tmp_path):
    "Test join_reference if xml file and schema are in different subdirectories."
    xml_file = tmp_path / "foo" / "simple_with_rng_and_sch.xml"
    schema_reference = "../bar/simple.rng"
    schema_path = tmp_path / "bar" / "simple.rng"
    schema_path.parent.mkdir(parents=True)
    xml_file.parent.mkdir()
    schema_path.touch()
    new_path = xmlschemadetector.join_reference_path(xml_file, schema_reference)
    assert new_path == schema_path.as_uri()


def test_join_reference_non_existing_schema(tmp_path):
    """Test join_reference if referenced schema does not exist."
    Should return the original reference. (to be handled somewere else).
    """
    xml_file = tmp_path / "minimal_with_sch.xml"
    schema_reference = "missing.rng"
    schema_path = tmp_path / schema_reference
    new_path = xmlschemadetector.join_reference_path(xml_file, schema_reference)
    assert new_path == schema_path.as_uri()


def test_join_reference_absolute_path(tmp_path):
    "Test join_reference if schema is reference by URL."
    xml_file = tmp_path / "simple_with_rng_and_sch.xml"
    schema_reference = "http://example.com/simple.rng"
    new_path = xmlschemadetector.join_reference_path(xml_file, schema_reference)
    assert new_path == schema_reference


## -------------- test the single find_schema_in_xx functions -----------------------------


def test_find_schema_in_processing_instructions(shared_datadir):
    "Test if local schemas are detected in processing instructions."
    xml_file = shared_datadir / "simple_with_rng_and_sch_in_pi.xml"
    root = ET.parse(xml_file)  # pylint: disable=c-extension-no-member
    schemata = xmlschemadetector.find_schemata_in_processing_instructions(
        root, xml_file
    )

    assert len(schemata) == len(["rng", "sch", "rng2"])

    assert schemata[0].schema_type == SchemaType.SCH
    assert schemata[0].charset == "utf-8"
    assert (
        schemata[0].schema_uri == (shared_datadir / "schemas" / "simple.sch").as_uri()
    )

    assert schemata[1].schema_type == SchemaType.RNG
    assert schemata[1].charset == "utf-8"
    assert (
        schemata[1].schema_uri == (shared_datadir / "schemas" / "simple.rng").as_uri()
    )

    assert schemata[2].schema_type == SchemaType.RNG
    assert schemata[2].charset == "utf-8"
    assert (
        schemata[2].schema_uri == (shared_datadir / "schemas" / "simple2.rng").as_uri()
    )


def test_find_schema_in_processing_instructions_url(shared_datadir):
    "Test find_schema_in_processing_instructions with URL referenced schemas."
    xml_file = shared_datadir / "simple_with_rng_and_sch_in_pi.xml"
    # lxml does not allow to change PI attributes. So we have to change the PI attributes in the xml source
    xml = xml_file.read_text()
    xml = xml.replace(
        'href="schemas/simple.sch"', 'href="http://example.com/simple.sch"'
    )
    xml = xml.replace(
        'href="./schemas/simple.rng"', 'href="http://example.com/simple.rng"'
    )
    xml = xml.replace(
        'href="./schemas/simple2.rng"', 'href="http://example.com/simple2.rng"'
    )
    root = ET.fromstring(xml)
    schemata = xmlschemadetector.find_schemata_in_processing_instructions(
        root, xml_file
    )
    assert len(schemata) == len(["sch", "rng", "rng2"])
    assert schemata[0].schema_type == SchemaType.SCH
    assert schemata[0].schema_uri == "http://example.com/simple.sch"
    assert schemata[1].schema_type == SchemaType.RNG
    assert schemata[1].schema_uri == "http://example.com/simple.rng"
    assert schemata[2].schema_type == SchemaType.RNG
    assert schemata[2].schema_uri == "http://example.com/simple2.rng"


def test_find_schema_in_root_element(shared_datadir):
    "Test if local schemas are detected in root element."
    xml_file = shared_datadir / "simple_with_xsd_in_root.xml"
    root = ET.parse(xml_file)
    schemata = xmlschemadetector.find_schemata_in_root_element(root, xml_file)
    assert len(schemata) == 1
    assert schemata[0].schema_type == SchemaType.XSD
    assert schemata[0].charset == "utf-8"
    assert (
        schemata[0].schema_uri == (shared_datadir / "schemas" / "simple.xsd").as_uri()
    )


def test_find_schema_in_root_element_with_no_namespace_schema_location(shared_datadir):
    "Test if local schemas are detected in root element if the noSchemaLocation attribute is set."
    xml_file = shared_datadir / "simple_with_xsd_in_root.xml"
    xml = xml_file.read_text()
    xml = xml.replace('schemaLocation="', 'noNamespaceSchemaLocation="')
    xml_file.write_text(xml)

    root = ET.parse(xml_file)
    schemata = xmlschemadetector.find_schemata_in_root_element(root, xml_file)
    assert len(schemata) == 1
    assert schemata[0].schema_type == SchemaType.XSD
    assert schemata[0].charset == "utf-8"
    assert (
        schemata[0].schema_uri == (shared_datadir / "schemas" / "simple.xsd").as_uri()
    )


def test_find_schemas_external_dtd(shared_datadir):
    "Test if external DTDs are detected."
    xml_file = shared_datadir / "simple_with_external_dtd.xml"
    schema_file = shared_datadir / "schemas" / "simple.dtd"
    root = ET.parse(xml_file)
    schemata = xmlschemadetector.find_dtd_in_tree(root, xml_file)
    assert len(schemata) == 1
    assert schemata[0].schema_uri == schema_file.as_uri()
    assert schemata[0].schema_type == SchemaType.DTD
    assert schemata[0].charset == "utf-8"


@pytest.mark.parametrize(
    "subtype, expected_schema_uri, expected_schema_type",
    [
        (
            SubType.TEIP5,
            "http://www.tei-c.org/release/xml/tei/custom/schema/xsd/tei_all.xsd",
            SchemaType.XSD,
        ),
        (
            SubType.TEIP4,
            "http://tei-c.org/Vault/P4/xml/schema/dtd/tei2.dtd",
            SchemaType.DTD,
        ),
        (
            SubType.LIDO,
            "http://www.lido-schema.org/schema/v1.1/lido-v1.1.xsd",
            SchemaType.XSD,
        ),
    ],
)
def test_find_schemas_apply_default_schema(
    subtype: SubType,
    expected_schema_uri: str,
    expected_schema_type: SchemaType,
    lazy_shared_datadir,
):
    """Test setting default schemas for specific formats.

    If schemadetctor cannot find any schema, it should
    return a generic schema for specific types like TEI.
    """
    xml_file = lazy_shared_datadir / "simple.xml"
    format_info = Mock()
    format_info.subtype = subtype
    schemata = xmlschemadetector.detect_schemata(xml_file, format_info)
    assert len(schemata) == 1
    assert schemata[0].schema_uri == expected_schema_uri
    assert schemata[0].schema_type == expected_schema_type
