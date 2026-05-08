"""Manage data for genertating SIP JSON files."""

# pylint: disable=too-many-instance-attributes
import logging
import time
from dataclasses import asdict, dataclass, field


from gamslib.formatdetect import detect_format
from gamslib.objectcsv.objectcsvmanager import ObjectCSVManager
from gamslib.objectcsv.utils import split_entry
from gamslib.sip import CURRENT_SIP_JSON_SCHEMA_URL
from gamslib.sip.validation import validate_datastream_id
from gamslib.sip.utils import md5hash, sha512hash

logger = logging.getLogger(__name__)


@dataclass
class ContentFile:
    "A dataclass for metadata of a datastream (used to create sip.json)."

    dsid: str
    mimetype: str
    title: str
    description: str
    creator: str
    rights: str
    size: int = 0
    bagpath: str = ""
    puid: str = ""
    lang: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    checksums: list[dict[str, str]] = field(default_factory=list)


@dataclass
class SipJson:
    """A dataclass where the SIP JSON can be generated from.

    So a SipJson Objects contains metadatadata for the object
    and all content files.
    """

    title: str
    project: str
    description: str
    creator: str
    rights: str
    publisher: str
    source: str
    recid: str
    objectType: str  # pylint: disable=invalid-name
    created_by: str
    sip_creation_timestamp: int = field(default_factory=lambda: int(time.time()))
    mainResource: str = ""  # pylint: disable=invalid-name
    contentFiles: list[ContentFile] = field(default_factory=list)  # pylint: disable=invalid-name
    lang: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    funder: str = ""
    created_by = ""

    @classmethod
    def from_objectcsvmanager(
        cls, created_by: str, csv_mgr: ObjectCSVManager
    ) -> "SipJson":
        """Create a SIPJSON object from a ObjectCSVManager object."""
        objectdata = csv_mgr.get_object()
        # next(iter(object_csv.get_objectdata()))
        sip_json = SipJson(
            recid=objectdata.recid,
            title=objectdata.title,
            project=objectdata.project,
            description=objectdata.description,
            creator=objectdata.creator,
            rights=objectdata.rights,
            publisher=objectdata.publisher,
            source=objectdata.source,
            objectType=objectdata.objectType,
            mainResource=objectdata.mainResource,
            lang=csv_mgr.get_languages(),
            tags=split_entry(objectdata.tags),
            funder=objectdata.funder,
            created_by=created_by,
        )
        # This is not complete, because we do not have all data:
        # (file) size and bagpath must be added by the caller after creation
        for datastream in csv_mgr.get_datastreamdata():
            contentfile = ContentFile(
                dsid=datastream.dsid,
                mimetype=datastream.mimetype,
                title=datastream.title,
                description=datastream.description,
                creator=datastream.creator,
                rights=datastream.rights,
                lang=split_entry(datastream.lang),
                tags=split_entry(datastream.tags),
            )
            # formatdetect!
            ds_path = csv_mgr.obj_dir / datastream.dspath
            ds_format = detect_format(ds_path)
            if ds_format:
                contentfile.puid = ds_format.pronom_id
            contentfile.checksums = [
                f"md5 {md5hash(ds_path)}",
                f"sha512 {sha512hash(ds_path)}",
            ]
            sip_json.contentFiles.append(contentfile)
        return sip_json

    def validate_datastreams(self) -> None:
        """Validate data streams.

        Check that all
           * datastream IDs are valid
           * datastream IDs are unique

        Raises ValueError if a non-unique recid is found.
        """
        seen_dsids = set()
        for content_file in self.contentFiles:
            validate_datastream_id(content_file.dsid)
            if content_file.dsid in seen_dsids:
                raise ValueError(f"Non-unique dsid: {content_file.dsid}")
            seen_dsids.add(content_file.dsid)

    def get_json(self) -> dict:
        """Return the SIP JSON as a dictionary."""
        data = dict(asdict(self).items())
        data["$schema"] = CURRENT_SIP_JSON_SCHEMA_URL
        for content_file in data["contentFiles"]:
            # dspath is a Path, which is not serializable to json
            content_file["bagpath"] = str(content_file["bagpath"])
        return data
