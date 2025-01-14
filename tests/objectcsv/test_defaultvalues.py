from gamslib.objectcsv import defaultvalues
from xml.etree import ElementTree as ET
from gamslib.objectcsv.defaultvalues import NAMESPACES

def test_extract_title_from_tei(datadir):
    "Ensure that the function returns the title"
    tei_file = datadir / "tei.xml"
    assert defaultvalues.extract_title_from_tei(tei_file) == "The TEI Title"

    # remove the title element and ensure that function return an empty string
    tei = ET.parse(tei_file)
    root = tei.getroot()
    title = root.find('tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:title', namespaces=NAMESPACES)
    root.find('tei:teiHeader/tei:fileDesc/tei:titleStmt', namespaces=NAMESPACES).remove(title)
    tei.write(tei_file)
    assert defaultvalues.extract_title_from_tei(tei_file) == ""


def test_extract_title_from_lido(datadir):
    "Ensure that the function returns the title"
    lido_file = datadir / "lido.xml"   
    assert defaultvalues.extract_title_from_lido(lido_file) == "Bratspieß" 


    # remove the titleSet element and ensure that function return an empty string
    tei = ET.parse(lido_file)
    root = tei.getroot()
    title = root.find('lido:descriptiveMetadata/lido:objectIdentificationWrap/lido:titleWrap/lido:titleSet', namespaces=NAMESPACES)
    root.find('lido:descriptiveMetadata/lido:objectIdentificationWrap/lido:titleWrap', namespaces=NAMESPACES).remove(title)
    tei.write(lido_file)
    assert defaultvalues.extract_title_from_tei(lido_file) == ""
