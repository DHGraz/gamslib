# The `SubType` class

The `SubType` class is an enum which defines SubTypes of Formats. 
Not each format has a subtype, In this case the FortmatInfo.subtype value is `None`.
Some formats like XML have subtypes, eg. `SubType.TEIP5`, `SubType.LIDO` or `SubType.JSONLD`.

The full list(s) of defined subtypes can be found in the formatdetect resources folder.

::: gamslib.formatdetect.formatinfo.SubType