
import hashlib
import json
import mimetypes
from pathlib import Path

import pytest

from gamslib.sip import utils


def make_contentfile_for_sip_json(file_path:Path):
    """Helper function for test data creation.
    
    Return a dict describing a content file as expected by sip.json.
    """
    return {
        "size": file_path.stat().st_size,
        "bagpath": "data/content/" + file_path.name,
        "dsid": file_path.name,
        "mimetype": mimetypes.guess_type(file_path)[0],
        "title": f"Title of {file_path.name}",
        "description": f"Description of {file_path.name}",
        "creator": f"Creator of {file_path.name}",
        "rights": "https://creativecommons.org/licenses/by-nc/4.0",
        "lang": ["en"],
        "tags": ["tag1", "tag2"]
    }


def create_manifests(bag_dir:Path, *args:Path):
    """Create the needed manifest files in bag_dirfor each path in args.

    This is a helper function for valid_bag_dir fixture, which creates
    manifest files for all files in content dir.
    """
    md5sums = []
    sha256sums = []
    sha512sums = []

    for file_path in args:
        if file_path.name == "sip.json":
            filename = "data/meta/sip.json"
        else:
            filename = f"data/content/{file_path.name}" 
        file_bytes = file_path.read_bytes()

        md5sums.append((hashlib.md5(file_bytes).hexdigest(), filename))
        sha256sums.append((hashlib.sha256(file_bytes).hexdigest(), filename))
        sha512sums.append((hashlib.sha512(file_bytes).hexdigest(), filename))

    # sort by path/filename
    md5data = "\n".join([f"{md5sum}  {filename}" for md5sum, filename in sorted(md5sums,key= lambda x: x[1])])
    sha256_data = "\n".join([f"{sha256sum}  {filename}" for sha256sum, filename in sorted(sha256sums,key= lambda x: x[1])])
    sha512_data = "\n".join([f"{sha512sum}  {filename}" for sha512sum, filename in sorted(sha512sums,key= lambda x: x[1])])

    (bag_dir / "manifest-md5.txt").write_text(md5data)
    (bag_dir / "manifest-sha256.txt").write_text(sha256_data)
    (bag_dir / "manifest-sha512.txt").write_text(sha512_data)


def update_sip_json(sipjson_path:Path, *content_paths:Path):
    """Update sip.json with content files from content_paths.

    This is a helper function for valid_bag_dir fixture, which updates
    sip.json with content files from content_paths.
    """
    # read sip.json
    with sipjson_path.open('r', encoding="utf-8", newline="") as sipjson_file:
            sipjson = json.load(sipjson_file)

    for content_file in content_paths:
        sipjson["contentFiles"].append(make_contentfile_for_sip_json(content_file))
    
    # write sip.json back to file
    with open(sipjson_path, 'w', encoding="utf-8", newline="") as sipjson_file:
        json.dump(sipjson, sipjson_file, ensure_ascii=False, indent=4)
    
def fix_payload_oxums(bag_dir:Path):
    """Helper function for test data creation.
    
    Set the correct payload oxums for the test data.    
    """
    total_bytes = utils.count_bytes(bag_dir / "data")
    num_of_files = utils.count_files(bag_dir / "data")

    fixed_lines = []
    with (bag_dir / "bag-info.txt").open("r", encoding="utf-8", newline="") as baginfo_file:
        for line in baginfo_file:
            if "Payload-Oxum" in line:
                fixed_lines.append(f"Payload-Oxum: {total_bytes}.{num_of_files}\n")
            else:
                fixed_lines.append(line)
    with (bag_dir / "bag-info.txt").open("w", encoding="utf-8", newline="") as baginfo_file:
        baginfo_file.writelines(fixed_lines)

@pytest.fixture
def valid_bag_dir(shared_datadir):
    """Return Path to a copy of a valid bag directory to test validation.

    To be as flexible as possible, some parts of metadata are computed on the fly.
    """
    bag_dir = shared_datadir / "valid_bag"
    sipjson_path = bag_dir / "data" / "meta" / "sip.json"
    content_files = list((bag_dir / "data" / "content").glob('*'))
    update_sip_json(sipjson_path, *content_files)    
    fix_payload_oxums(bag_dir)
    create_manifests(bag_dir, sipjson_path,  *content_files)
    return bag_dir
    

