This folder contains csv files which are the central source for subformat information.

Currently we only use xml and json subformats (thus only 2 csv file: 
json_subformats.csv and xml_subformats.csv). 
If needed, additional csv files fore new subformats can be added, following
the given format. They will be recognized automatically. It is very
important, that the file name follows this schema:

```
  <main_type>_subformats.csv
```

where main_format is a generic name like 'xml' or 'json'.


Each csv file needs a first line with the column names and at least one 
data line. The four columns are:


subformat:
    This is the name which should bes used in the SubFormat enum. 
    Preferably in uppercase letters.
full name:
    This is a string which is used as text in the SubFormat StrEnum object.
ds name:
    This is an alternative name, which is used as part of 'title' in the 
    datastreams.csv file. Currently I tried to use the main type as first
    word. This is sometimes strange (XML RDF document), but make it easier
    for frontend people to detect the type. 
mimetype: 
    The official mimetype of the subtype. This will be the mime type of
    the main format (application/xml), but might be a special type, if 
    defined like 'application/tei+xml'.
