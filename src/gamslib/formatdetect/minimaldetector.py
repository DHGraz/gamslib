# move to __init__.py?

from pathlib import Path
from mimetypes import guess_type
import warnings
from . import xmltypes
from . import jsontypes
from .formatinfo import FormatInfo
from .formatdetector import FormatDetector, DEFAULT_TYPE


class MinimalDetector(FormatDetector):
    """The most simple Format Detector using the mimetypes module.

    This detector uses the mimetypes module to determine the file type.
    As this module heavily relies on file extensions, it is not very reliable.
    """


    def guess_file_type(self, filepath:Path) -> FormatInfo:
        mime_type, _ = guess_type(filepath)
        detector_name = str(self)#)#self.__class__.__name__
        subtype = ""

        if mime_type is None:
            # if we cannot determine the mime type, we return the DEFAULT_TYPE
            warnings.warn(f"Could not determine mimetype for {filepath}. Using default type.")
            mime_type = DEFAULT_TYPE
        elif xmltypes.is_xml_type(mime_type):
            mime_type, subtype = xmltypes.get_format_info(filepath, mime_type) 
        elif jsontypes.is_json_type(mime_type):
            mime_type, subtype = jsontypes.get_format_info(filepath, mime_type) 

        return FormatInfo(detector=detector_name, mimetype=mime_type, subtype=subtype)


    def __repr__(self):
        return "MinimalDetector"    
        