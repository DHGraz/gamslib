from gamslib.validation.xml.xmlvalidator import XMLValidator
from lxml import etree as ET


def test_has_subschemas():
    "Test if has_subschemas returns True if schemaLocation is in root element."
    xml = '<root xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://example.com schema.xsd"></root>'
    tree = ET.ElementTree(ET.fromstring(xml))
    assert not XMLValidator.has_subschemas(tree)

def test_has_subschemas_with_sub_schemalocation():
    "Here we have a child element with a schemaLocation attribute."
    xml = '''<root xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://example.com schema.xsd">" 
    <foo>
    <child xsi:schemaLocation="http://example.com schema2.xsd"></child>
       </foo></root>'''
    tree = ET.ElementTree(ET.fromstring(xml))
    assert XMLValidator.has_subschemas(tree)

def test_has_subschemas_with_sub_noNamespaceSchemaLocation():
    "Here we have a child element with a noNamespaceSchemaLocation attribute."
    xml = """<root xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xsi:schemaLocation='http://example.com schema.xsd'>" 
    <foo><child xsi:noNamespaceSchemaLocation='schema2.xsd'></child></foo>
       </root>"""
    tree = ET.ElementTree(ET.fromstring(xml))
    assert XMLValidator.has_subschemas(tree)


def test_validate_subschemas_document_valid(shared_datadir):
    """For validating a document with subschemas we use a special method."""
    xml_file = shared_datadir / "mets.xml"
    validator = XMLValidator(xml_file)  
    result = validator._validate_subschema_document(ET.parse(xml_file))
    assert result.valid

def test_validate_subschemas_document_invalid(shared_datadir):
    """For validating a document with subschemas we use a special method."""
    xml_file = shared_datadir / "mets_invalid.xml"
    validator = XMLValidator(xml_file)  
    result = validator._validate_subschema_document(ET.parse(xml_file))
    assert result.valid is False
    assert len(result.errors) == 1
    assert "invalidAttribute" in " ".join([logentry.message for logentry in result.errors])


def test_validate_is_wellformed(shared_datadir):
    "Test a well-formed XML without associated schema."
    xml_file = shared_datadir / "minimal_wellformed.xml"
    validator = XMLValidator(xml_file)
    result = validator.validate()
    assert result.valid
   # assert result.validated
    assert not result.errors
    assert result.validator == "XMLValidator"
    assert result.schema == ""



def test_validate_not_wellformed(shared_datadir):
    "Test a not well-formed XML."
    xml_file = shared_datadir / "minimal_not_wellformed.xml"
    validator = XMLValidator(xml_file)
    result = validator.validate()
    assert result.valid is False    
    assert len(result.errors) == 1
    assert "tag mismatch" in result.errors[0]
    assert result.validator == "XMLValidator"
    assert result.schema == ""
