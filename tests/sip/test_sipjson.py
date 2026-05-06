"""Test for the sipjson module."""

import json
import shutil
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from freezegun import freeze_time
import requests

from gamslib.objectcsv.create_csv import DSData, ObjectCSVManager, ObjectData
from gamslib.sip import BagValidationError, sipjson
import gamslib.sip
from gamslib.sip.sipjson import ContentFile, SipJson

from gamslib.sip.utils import fetch_json_schema
from gamslib.sip.utils import read_sip_schema_from_package

@pytest.fixture(name="dummyobjectcsv")
def get_dummyobjectcsv(tmpdir, datadir):
    "Return a dummy Metadata object."
    objdir = Path(tmpdir) / "project.object1"
    objdir.mkdir()
    shutil.copy(datadir / "obj.1" / "img.1.png", objdir / "img1.png")
    shutil.copy(datadir / "obj.1" / "img.2.jpg", objdir / "img2.jpg")

    csv_mgr = ObjectCSVManager(objdir)
    csv_mgr.set_object(
        ObjectData(
            recid="project.object1",
            title="title",
            project="project",
            description="description",
            creator="creator",
            rights="rights",
            publisher="publisher",
            source="source",
            objectType="objectType",
            mainResource="img1.png",
            funder="funder",
            tags="tag1; tag2",
        )
    )
    csv_mgr.add_datastream(
        DSData(
            dspath="img1.png",
            dsid="img1.png",
            mimetype="image/png",
            title="title1",
            description="description1",
            creator="creator1",
            rights="rights1",
            lang="en; fr",
            tags="footag; bartag"
        )
    )
    csv_mgr.add_datastream(
        DSData(
            dspath="img2.jpg",
            dsid="img2.jpg",
            mimetype="image/jpg",
            title="title2",
            description="description2",
            creator="creator2",
            rights="rights2",
            lang="de",
            tags="tagfoo"
        )
    )
    return csv_mgr

@pytest.fixture(name="sipjson_obj")
def get_sipjson_obj():
    "Return a populated SipJson object."
    data = SipJson(
        title="title",
        project="project",
        description="description",
        creator="creator",
        rights="rights",
        publisher="publisher",
        created_by="Test Creator",
        source="source",
        recid="recid",
        objectType="objectType",
        mainResource="mainResource",
        lang = ["fr", "de"],
        tags = ["tag1", "tag2"],
        funder = "The project funder",
        sip_creation_timestamp = 1777282176.7894132
    )
    data.contentFiles.append(
        ContentFile(
            dsid="img1.png",
            bagpath="data/content/bagpath1",
            mimetype="image/png",
            title="title1",
            description="description1",
            creator="creator1",
            rights="rights1",
            lang=["en", "fr"],
            tags=["footag", "bartag"],
            puid="fmt/11",
            size=123,
            checksums=[
                "md5 8f7b2b4b4b4b4b4b4b4b4b4b4b4b4b",
                "sha512 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855c0d16a5daee1436adad79d6c14c1b6a5fb5319723aabd7b7a7ef51ad7f8fa6e7",
            ],
        )
    )
    data.contentFiles.append(
        ContentFile(
            dsid="img2.jpg",
            bagpath="data/content/bagpath2",
            mimetype="image/jpg",
            title="title2",
            description="description2",                
            creator="creator2",
            rights="rights2",
            lang=["de"],
            tags=["tagfoo"],
            puid="fmt/22",
            size=456,
            checksums=[
                "md5 8f7b2b4b4b4b4b4b4b4b4b4b4b4b4b",
                "sha512 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855c0d16a5daee1436adad79d6c14c1b6a5fb5319723aabd7b7a7ef51ad7f8fa6e7",
            ],
        )
    )                   
    return data

def test_contentfile():
    "Test creation of a ContentFile object."
    cf = ContentFile(
        dsid="dsid",
        mimetype="mimetype",
        title="title",
        size=123,
        bagpath="data/content/dsid",
        description="description",
        creator="creator",
        rights="rights",
        lang=["en", "fr"],
        tags=["tag1", "tag2"],
        puid="fmt/123",
        checksums=[
            "md5 8f7b2b4b4b4b4b4b4b4b4b4b4b4b4b4b",
            "sha512 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855c0d16a5daee1436adad79d6c14c1b6a5fb5319723aabd7b7a7ef51ad7f8fa6e7",
        ],
    )
    assert cf.dsid == "dsid"
    assert cf.mimetype == "mimetype"
    assert cf.title == "title"
    assert cf.description == "description"
    assert cf.creator == "creator"
    assert cf.rights == "rights"
    assert cf.lang == ["en", "fr"]
    assert cf.tags == ["tag1", "tag2"]
    assert cf.puid == "fmt/123"
    assert cf.size == 123
    assert cf.bagpath == "data/content/dsid"
    assert cf.checksums[0] == "md5 8f7b2b4b4b4b4b4b4b4b4b4b4b4b4b4b"
    assert cf.checksums[1] == "sha512 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855c0d16a5daee1436adad79d6c14c1b6a5fb5319723aabd7b7a7ef51ad7f8fa6e7"


def test_sipjson_init_explicit_values():
    "Test creation of a SIPJSON object with some values set automatically."
    sip = SipJson(
        title="title",
        project="project",
        description="description",
        creator="creator",
        rights="rights",
        publisher="publisher",
        created_by="created_by",
        source="source",
        recid="recid",
        objectType="objectType",
        mainResource="mainResource",
        lang = ["fr", "de"],
        tags = ["tag1", "tag2"],
        funder = "The project funder",
        sip_creation_timestamp = 1777282176.7894132
    )   
    assert sip.title == "title"
    assert sip.project == "project"
    assert sip.description == "description"
    assert sip.creator == "creator"
    assert sip.rights == "rights"
    assert sip.publisher == "publisher"
    assert sip.source == "source"
    assert sip.recid == "recid"
    assert sip.objectType == "objectType"
    assert sip.created_by == "created_by"
    assert sip.mainResource == "mainResource"
    assert sip.lang == ["fr", "de"]
    assert sip.tags == ["tag1", "tag2"]
    assert sip.funder == "The project funder"
    assert sip.sip_creation_timestamp == 1777282176.7894132

@freeze_time("2026-01-14 12:01:02")
def test_sipjson_init_default_values():
    "Test creation of a SIPJSON object with all values set explicitly."

    sip = SipJson(
        title="title",
        project="project",
        description="description",
        creator="creator",
        rights="rights",
        publisher="publisher",
        created_by="created_by",
        source="source",
        recid="recid",
        objectType="objectType",
    )

    expected_timestamp = int(datetime(2026, 1, 14, 12, 1, 2).timestamp())
    assert sip.sip_creation_timestamp == expected_timestamp
    assert sip.mainResource == ""
    assert sip.lang == []
    assert sip.tags == []
    assert sip.funder == ""


def test_from_metadata(dummyobjectcsv):
    "Test the from_metadata class method, which creates a SIPJSON object from a Metadata object."
    sip = SipJson.from_objectcsvmanager("Test Creator", dummyobjectcsv)

    objectdata = dummyobjectcsv.get_object()
    assert sip.title == objectdata.title
    assert sip.project == objectdata.project
    assert sip.description == objectdata.description
    assert sip.creator == objectdata.creator
    assert sip.rights == objectdata.rights
    assert sip.publisher == objectdata.publisher
    assert sip.source == objectdata.source
    assert sip.recid == objectdata.recid
    assert sip.objectType == objectdata.objectType
    assert sip.created_by == "Test Creator"
    assert sip.mainResource == "img1.png"
    assert len(sip.contentFiles) == dummyobjectcsv.count_datastreams()
    assert sip.lang == ["en", "fr", "de"]
    assert sip.tags == ["tag1", "tag2"]
    assert sip.funder == "funder"

    assert sip.contentFiles[0].dsid == "img1.png" 
    assert sip.contentFiles[0].mimetype == "image/png"
    assert sip.contentFiles[0].title == "title1"
    assert sip.contentFiles[0].description == "description1"
    assert sip.contentFiles[0].creator == "creator1"
    assert sip.contentFiles[0].rights == "rights1"
    assert sip.contentFiles[0].size == 0
    assert sip.contentFiles[0].bagpath == ""
    assert sip.contentFiles[0].lang == ["en", "fr"]
    assert sip.contentFiles[0].tags == ["footag", "bartag"]
    assert sip.contentFiles[0].puid == "fmt/11"
    assert "md5" in sip.contentFiles[0].checksums[0]
    assert "sha512" in sip.contentFiles[0].checksums[1]


    assert sip.contentFiles[1].dsid == "img2.jpg"
    assert sip.contentFiles[1].mimetype == "image/jpg"
    assert sip.contentFiles[1].title == "title2"
    assert sip.contentFiles[1].description == "description2"
    assert sip.contentFiles[1].creator == "creator2"
    assert sip.contentFiles[1].rights == "rights2"
    assert sip.contentFiles[1].size == 0
    assert sip.contentFiles[1].bagpath == ""
    assert sip.contentFiles[1].lang == ["de"]
    assert sip.contentFiles[1].tags == ["tagfoo"]
    assert sip.contentFiles[1].puid == "fmt/43"
    assert "md5" in sip.contentFiles[0].checksums[0]
    assert "sha512" in sip.contentFiles[0].checksums[1]


def test_get_json(sipjson_obj):
    "Test the get_json method, which returns the SIPJSON object as a dictionary."

    jsondata = sipjson_obj.get_json()
    assert jsondata["title"] == sipjson_obj.title
    assert jsondata["project"] == sipjson_obj.project
    assert jsondata["description"] == sipjson_obj.description
    assert jsondata["creator"] == sipjson_obj.creator
    assert jsondata["rights"] == sipjson_obj.rights
    assert jsondata["publisher"] == sipjson_obj.publisher
    assert jsondata["source"] == sipjson_obj.source
    assert jsondata["recid"] == sipjson_obj.recid
    assert jsondata["objectType"] == sipjson_obj.objectType
    assert jsondata["created_by"] == "Test Creator"
    assert jsondata["mainResource"] == "mainResource"
    assert jsondata["contentFiles"][0]["dsid"] == "img1.png"
    assert jsondata["contentFiles"][1]["dsid"] == "img2.jpg"
    assert jsondata["contentFiles"][0]["mimetype"] == "image/png"
    assert jsondata["contentFiles"][1]["mimetype"] == "image/jpg"
    assert jsondata["contentFiles"][0]["title"] == "title1"
    assert jsondata["contentFiles"][1]["title"] == "title2"
    assert jsondata["contentFiles"][0]["description"] == "description1"
    assert jsondata["contentFiles"][1]["description"] == "description2"
    assert jsondata["contentFiles"][0]["creator"] == "creator1"
    assert jsondata["contentFiles"][1]["creator"] == "creator2"
    assert jsondata["contentFiles"][0]["rights"] == "rights1"
    assert jsondata["contentFiles"][1]["rights"] == "rights2"
    assert jsondata["contentFiles"][0]["size"] == 123  # noqa: PLR2004
    assert jsondata["contentFiles"][1]["size"] == 456  # noqa: PLR2004
    assert jsondata["contentFiles"][0]["bagpath"] == "data/content/bagpath1"
    assert jsondata["contentFiles"][1]["bagpath"] == "data/content/bagpath2"
    assert jsondata["created_by"] == "Test Creator"
    assert jsondata["$schema"] == gamslib.sip.CURRENT_SIP_JSON_SCHEMA_URL
    assert jsondata["lang"] == ["fr", "de"] 
    assert jsondata["contentFiles"][1]["lang"] == ["de"]
    assert jsondata["contentFiles"][0]["tags"] == ["footag", "bartag"]
    assert jsondata["contentFiles"][1]["tags"] == ["tagfoo"]
    assert jsondata["contentFiles"][0]["puid"] == "fmt/11"
    assert jsondata["contentFiles"][1]["puid"] == "fmt/22"

def test_validate_dsids_unique(dummyobjectcsv):
    "Test validate_dsids with unique dsids  (should not raise)."
    sip = SipJson.from_objectcsvmanager("Test Creator", dummyobjectcsv)
    sip.validate_datastreams()  # Should not raise


def test_validate_recids_duplicate(dummyobjectcsv):
    "Test validate_recids with duplicate recids (should raise ValueError)."
    sip = SipJson.from_objectcsvmanager("Test Creator", dummyobjectcsv)
    # Introduce a duplicate recid
    sip.contentFiles[1].dsid = sip.contentFiles[0].dsid
    with pytest.raises(ValueError, match="Non-unique dsid:"):
        sip.validate_datastreams()

