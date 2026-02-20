#import pytest
#from gamslib.validation import utils
from pathlib import Path

import pytest
from gamslib.validation.schemainfo import SchemaInfo, SchemaType
#from gamslib.validation.xml.schemainfo import SchemaInfo, XMLSchemaType


def test_schemainfo_init_with_defaults():
    "Test the SchemaInfo constructor with default values."
    schema_file = "dummy.xsd"
    schemainfo = SchemaInfo(schema_file)
    assert schemainfo.schema_type == SchemaType.XSD
    assert schemainfo.schema_uri == Path(schema_file).resolve().as_uri()

def test_schemainfo_init_with_explicit_values():
    "Test the SchemaInfo constructor with explicit values."
    schema_url = "https://gams.uni-graz.at/lido/1.0/lido.xsd"
    schematypens="http://www.w3.org/2001/XMLSchema"
    mimetype="application/xml"
    schematype = SchemaType.XSD
    charset="latin-1"
    schemainfo = SchemaInfo(schema_url, mimetype, schematypens, charset, schematype)
    assert schemainfo.schema_uri == schema_url
    assert schemainfo.mimetype == mimetype
    assert schemainfo.schematypens == schematypens
    assert schemainfo.charset == charset
    assert schemainfo.schema_type == SchemaType.XSD

def test_init_with_file(shared_datadir):
    "The post_init method of the SchemaInfo class should convert a file path to an uri like format."
    schema_file = shared_datadir / "schemas" / "simple.xsd"
    schemainfo = SchemaInfo(str(schema_file))   
    assert schemainfo.schema_uri.startswith("file://")


# # def test_schema_exists(shared_datadir, monkeypatch):
# #     "Test the schema_exists function."

# #     # schema is a local file which exists
# #     schema_file = (shared_datadir / "schemas" / "simple.xsd").as_posix()
# #     assert SchemaInfo.schema_exists(schema_file)

# #     # schema is a local file which does not exist
# #     schema_file = (shared_datadir / "schemas" / "does_not_exist.xsd").as_posix()
# #     assert not SchemaInfo.schema_exists(schema_file)

# #     # schema is a URL which exists
# #     # monkeypatch the utils.load_schema to always return a string
# #     monkeypatch.setattr(
# #         utils, "load_schema", lambda schema_location: b"dummy schema content"
# #     )
# #     schema_url = "https://gams.uni-graz.at/lido/1.0/lido.xsd"
# #     assert SchemaInfo.schema_exists(schema_url)

# #     # schema is a URL which does not exist
# #     # monkeypatch the utils.load_schema to raise a ValueError 
# #     monkeypatch.setattr(
# #         utils, "load_schema", lambda schema_location: (_ for _ in ()).throw(ValueError)
# #     )
# #     schema_url = "https://gams.uni-graz.at/foo/bar.xsd"
# #     assert not SchemaInfo.schema_exists(schema_url)


# Test schema type detection if only the schema location is known
# This will mostly use the last resort: detect by extension
@pytest.mark.parametrize("schema_file, expected_type", [
    ("simple.xsd", SchemaType.XSD),
    ("simple.sch", SchemaType.SCH),
    ("simple.rng", SchemaType.RNG),
    ("simple.rnc", SchemaType.RNC),
    ("simple.dtd", SchemaType.DTD)
    ])
def test_schema_only_dtd(schema_file, expected_type, shared_datadir):
    "Test if an external schema is detected, if only the path to the schema file is given."
    schema_path = shared_datadir / "schemas" / schema_file  
    schemainfo = SchemaInfo(str(schema_path))
    assert schemainfo.schema_type == expected_type
    assert schemainfo.schema_uri == schema_path.resolve().as_uri()
    assert schemainfo.charset == "utf-8"

def test_schema_only_unknown(shared_datadir):
    "If we cannot detect the schema type, we should raise an error."
    schema_file = (shared_datadir / "schemas" / "simple.unknown").as_posix()
    with pytest.raises(ValueError, match="Unknown"):
        SchemaInfo(schema_file)


@pytest.mark.parametrize("schematypens, expected_type", [
    ("http://www.w3.org/2001/XMLSchema", SchemaType.XSD),
    ("http://relaxng.org/ns/structure/1.0", SchemaType.RNG),
    ("http://purl.oclc.org/dsdl/schematron", SchemaType.SCH)
])
def tests_type_detection_from_schematypens(schematypens, expected_type, shared_datadir):
    "Test if the schema type is detected by the schematypens attribute."
    # as the schema file is ignored when a schemtypens is given, we can use a dummy file
    schema_path = (shared_datadir / "schemas" / "simple.xsd")
    schemainfo = SchemaInfo(str(schema_path), schematypens=schematypens)
    assert schemainfo.schema_type == expected_type
    assert schemainfo.schema_uri == schema_path.resolve().as_uri()
    assert schemainfo.charset == "utf-8"

@pytest.mark.parametrize("mimetype, expected_type", [
    ("application/xml-dtd", SchemaType.DTD),
    ("application/relax-ng-compact-syntax", SchemaType.RNC)
])
def test_type_detection_frome_mimetype(mimetype, expected_type):
    "Test if the schema type is detected by the mimetype."
    # as the schema file is ignored when a mimetype is given, we can use a dummy file
    schema_file = "dummy.file"  # can be any string here 
    schemainfo = SchemaInfo(schema_file, mimetype=mimetype)
    assert schemainfo.schema_type == expected_type
