"""Tests for the Dublin Core module."""

# pylint: disable=W0212 # access to ._data
import pytest
from lxml import etree as ET

from gamslib.objectcsv.dublincore import DublinCore


def test_init(datadir):
    """Test the GamsObject initializer."""
    path = datadir / "DC.xml"
    dc = DublinCore(path)
    assert dc.path == path
    assert dc.lookup_order == ["en", "de", "fr", "es", "it"]
    assert dc._data["title"]["en"] == ["Person description 1"]
    assert dc._data["title"]["de"] == ["Personenbeschreibung 1"]
    assert dc._data["publisher"]["de"] == ["Person 1, Karl-Franzens-Universität Graz"]

    assert dc._data["creator"]["unspecified"] == ["Foo, Bar"]
    assert dc._data["date"]["unspecified"] == ["2015"]
    assert dc._data["format"]["unspecified"] == ["text/xml"]
    assert dc._data["identifier"]["unspecified"] == ["o:hsa.person.2037"]
    assert dc._data["language"]["unspecified"] == ["de"]
    assert dc._data["relation"]["unspecified"] == [
        "Hugo Schuchardt Archiv",
        "http://schuchardt.uni-graz.at",
    ]
    assert dc._data["rights"]["unspecified"] == [
        "Creative Commons BY-NC 4.0",
        "https://creativecommons.org/licenses/by-nc/4.0",
    ]


def test_get_element(datadir):
    "Test get_element wiithout preferred language"
    path = datadir / "DC.xml"
    dc = DublinCore(path)

    # as in default lookup order 'en' is first, we get the english title
    assert dc.get_element("title") == ["Person description 1"]
    assert dc.get_element("title") == ["Person description 1"]

    # test fields without an explicit lang (lang='unspecified')
    assert dc.get_element("creator") == ["Foo, Bar"]
    assert dc.get_element("date") == ["2015"]


def test_get_element_with_changed_preferred_order(datadir):
    "Whwn we change the order of lookup, the result should change accordingly."
    path = datadir / "DC.xml"
    dc = DublinCore(path, ("de", "en", "fr"))

    # we changed lookup order to 'de' first. As we do not have an entry for 'fr',
    # the german title should be returned
    assert dc.get_element("title", "fr") == ["Personenbeschreibung 1"]


def test_get_element_with_preferred_lang(datadir):
    "Test get_element with preferred language"
    path = datadir / "DC.xml"
    dc = DublinCore(path)
    assert dc.get_element("title", "de") == ["Personenbeschreibung 1"]
    assert dc.get_element("title", "fr") == ["Person description 1"]
    assert dc.get_element("date", "de") == ["2015"]


def test_get_non_dc_element(datadir):
    "Accessing an element that is not a Dublin Core element should raise an ValueError."
    path = datadir / "DC.xml"
    dc = DublinCore(path)

    with pytest.raises(ValueError):
        dc.get_element("foo")


def test_get_element_with_linebreaks(datadir, tmp_path):
    "Test get_element with linebreaks in the text: all linebreaks should be removed."
    path = datadir / "DC.xml"
    xml = path.read_text(encoding="utf-8")
    xml = xml.replace("Foo, Bar", "Foo,\nBar\r\nFoobar")
    new_path = tmp_path / "DC.xml"
    new_path.write_text(xml, encoding="utf-8")
    dc = DublinCore(new_path)
    assert dc.get_element("creator") == ["Foo, Bar Foobar"]


def test_get_missing_element(datadir):
    "Try to access an element that is not set. Should return a list with an empty string."
    path = datadir / "DC.xml"
    dc = DublinCore(path)
    del dc._data["creator"]
    assert dc.get_element("creator") == [""]


def test_get_missing_element_with_explicit_default(datadir):
    "Test get_element with non existing element and an explicitely set default value."
    path = datadir / "DC.xml"
    dc = DublinCore(path)
    del dc._data["creator"]
    assert dc.get_element("creator", default="not set") == ["not set"]


def test_get_element_as_str(datadir):
    "This special method returns the element data as a string."
    path = datadir / "DC.xml"
    data = {
        "contributor": {"unspecified": ["contributor 1", "contributor 2"]},
        "coverage": {"unspecified": ["coverage1", "coverage 2"]},
        "creator": {"unspecified": ["creator 1", "creator 2"]},
        "date": {"unspecified": ["2015", "2016"]},
        "description": {"unspecified": ["description 1", "description 2"]},
        "format": {"unspecified": ["format 1", "format 2"]},
        "identifier": {"unspecified": ["identifier 1", "identifier 2"]},
        "language": {"unspecified": ["language 1", "language 2"]},
        "publisher": {"unspecified": ["publisher 1", "publisher 2"]},
        "relation": {"unspecified": ["relation 1", "relation 2"]},
        "rights": {"unspecified": ["rights 1", "rights 2"]},
        "source": {"unspecified": ["source 1", "source 2"]},
        "subject": {"unspecified": ["subject 1", "subject 2"]},
        "title": {"unspecified": ["title 1", "title 2"]},
        "type": {"unspecified": ["type 1", "type 2"]},
    }
    dc = DublinCore(path)
    dc._data = data
    assert dc.get_element_as_str("contributor") == "contributor 1; contributor 2"
    assert dc.get_element_as_str("coverage") == "coverage1; coverage 2"
    assert dc.get_element_as_str("creator") == "creator 1; creator 2"
    assert dc.get_element_as_str("date") == "2015; 2016"
    assert dc.get_element_as_str("description") == "description 1; description 2"
    assert dc.get_element_as_str("format") == "format 1; format 2"
    assert dc.get_element_as_str("identifier") == "identifier 1; identifier 2"
    assert dc.get_element_as_str("language") == "language 1; language 2"
    assert dc.get_element_as_str("publisher") == "publisher 1; publisher 2"
    assert dc.get_element_as_str("relation") == "relation 1; relation 2"
    assert dc.get_element_as_str("rights") == "rights 1 (rights 2)"
    assert dc.get_element_as_str("source") == "source 1; source 2"
    assert dc.get_element_as_str("subject") == "subject 1; subject 2"
    assert dc.get_element_as_str("title") == "title 1; title 2"
    assert dc.get_element_as_str("type") == "type 1; type 2"


def test_get_element_as_str_single_values(datadir):
    """This special method returns the element data as a string.
    Check if it also works for single values"""
    path = datadir / "DC.xml"
    data = {
        "contributor": {"unspecified": ["contributor 1"]},
        "coverage": {"unspecified": ["coverage1"]},
        "creator": {"unspecified": ["creator 1"]},
        "date": {"unspecified": ["2015"]},
        "description": {"unspecified": ["description 1"]},
        "format": {"unspecified": ["format 1"]},
        "identifier": {"unspecified": ["identifier 1"]},
        "language": {"unspecified": ["language 1"]},
        "publisher": {"unspecified": ["publisher 1"]},
        "relation": {"unspecified": ["relation 1"]},
        "rights": {"unspecified": ["rights 1"]},
        "source": {"unspecified": ["source 1"]},
        "subject": {"unspecified": ["subject 1"]},
        "title": {"unspecified": ["title 1"]},
        "type": {"unspecified": ["type 1"]},
    }
    dc = DublinCore(path)
    dc._data = data
    assert dc.get_element_as_str("contributor") == "contributor 1"
    assert dc.get_element_as_str("coverage") == "coverage1"
    assert dc.get_element_as_str("creator") == "creator 1"
    assert dc.get_element_as_str("date") == "2015"
    assert dc.get_element_as_str("description") == "description 1"
    assert dc.get_element_as_str("format") == "format 1"
    assert dc.get_element_as_str("identifier") == "identifier 1"
    assert dc.get_element_as_str("language") == "language 1"
    assert dc.get_element_as_str("publisher") == "publisher 1"
    assert dc.get_element_as_str("relation") == "relation 1"
    assert dc.get_element_as_str("rights") == "rights 1"
    assert dc.get_element_as_str("source") == "source 1"
    assert dc.get_element_as_str("subject") == "subject 1"
    assert dc.get_element_as_str("title") == "title 1"
    assert dc.get_element_as_str("type") == "type 1"


def test_get_en_element(datadir):
    "Test get_en_element"
    path = datadir / "DC.xml"
    dc = DublinCore(path)
    # we have an english title and a german title
    assert dc.get_en_element("title") == ["Person description 1"]
    # we have a date, but no date with lang='en'
    assert dc.get_en_element("date") == []
    with pytest.raises(ValueError):
        dc.get_en_element("foo")

    # test with a non empty default value
    assert dc.get_en_element("publisher", default="foo") == ["foo"]


def test_get_en_element_with_linebreaks(datadir, tmp_path):
    "Test get_en_element with linebreaks in the text: all linebreaks should be removed."
    path = datadir / "DC.xml"
    xml = path.read_text(encoding="utf-8")
    xml = xml.replace(
        "<dc:creator>Foo, Bar</dc:creator>",
        '<dc:creator xml:lang="en">Foo,\nBar\r\nFoobar</dc:creator>',
    )
    new_path = tmp_path / "DC.xml"
    new_path.write_text(xml, encoding="utf-8")
    dc = DublinCore(new_path)
    assert dc.get_en_element("creator") == ["Foo, Bar Foobar"]


def test_get_en_element_as_str(datadir, tmp_path):
    "Test get_en_element"
    path = datadir / "DC.xml"
    dc = DublinCore(path)
    # we have an english title and a german title
    assert dc.get_en_element_as_str("title") == "Person description 1"
    # we have a date, but no date with lang='en'
    assert dc.get_en_element_as_str("date") == ""
    with pytest.raises(ValueError):
        dc.get_en_element_as_str("foo")
    assert dc.get_en_element_as_str("publisher", default="foo") == "foo"

    # Let's add a second title in english
    # and check if we get both titles back
    # we have an english title and a german title
    # we should have 2 english titles and a german title
    ET.register_namespace("xml", "http://www.w3.org/XML/1998/namespace")
    new_dcpath = tmp_path / "DC.xml"
    tree = ET.parse(path)
    root = tree.getroot()
    root.append(ET.Element("{http://purl.org/dc/elements/1.1/}title", {"{http://www.w3.org/XML/1998/namespace}lang": "en"}))
    root[-1].text = "pd2"   
    tree.write(new_dcpath, encoding="utf-8", xml_declaration=True)

    dc = DublinCore(new_dcpath)
    # we should have 2 english titles and a german title
    assert dc.get_en_element_as_str("title") == "Person description 1; pd2"
