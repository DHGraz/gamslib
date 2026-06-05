# The `datacite` subpackage

The `datacite` subpackage provides Pydantic models for a DataCite/Invenio record.
The hierarchy below starts with `DataCite` and shows which classes are used by other
classes. Types from `common.py` and `vocabularies.py` are intentionally left out.

## Modules

- [metadata_models](metadata_models.md) (all classes from `metadata_*` modules in one page)
- [datacite_record](datacite_record.md)
- [datacite](datacite.md)
- [access](access.md)
- [files](files.md)
- [metadata](metadata.md)
- [metadata_people](metadata_people.md)
- [metadata_identifiers](metadata_identifiers.md)
- [metadata_dates](metadata_dates.md)
- [metadata_additional_titles](metadata_additional_titles.md)
- [metadata_additional_descriptions](metadata_additional_descriptions.md)
- [metadata_funding](metadata_funding.md)
- [metadata_location](metadata_location.md)
- [metadata_reference](metadata_reference.md)
- [metadata_rights](metadata_rights.md)
- [metadata_subjects](metadata_subjects.md)
- [tombstone](tombstone.md)

## Class hierarchy

```text
DataCite [datacite_record.py]
├── access: Access [access.py]
│   └── embargo: Embargo | None [access.py]
├── metadata: Metadata [metadata.py]
│   ├── creators: list[Creator] [metadata_people.py]
│   │   └── Creator
│   │       ├── person_or_org: PersonOrOrganization
│   │       │   └── identifiers: PersonOrOrganizationIdentifier | None
│   │       └── affiliations: list[Affiliation]
│   ├── contributors: list[Contributor] [metadata_people.py]
│   │   └── Contributor
│   │       └── inherits from Creator
│   ├── additional_titles: list[AdditionalTitle] [metadata_additional_titles.py]
│   │   └── AdditionalTitle
│   │       └── type: AdditionalTitleType
│   ├── additional_descriptions: list[AdditionalDescription] [metadata_additional_descriptions.py]
│   │   └── AdditionalDescription
│   │       └── type: AdditionalDescriptionType
│   ├── rights: Rights | None [metadata_rights.py]
│   ├── subjects: list[Subject] [metadata_subjects.py]
│   ├── dates: list[Date] [metadata_dates.py]
│   │   └── Date
│   │       └── type: DateType | None
│   ├── identifiers: list[AlternateIdentifier] [metadata_identifiers.py]
│   ├── related_identifiers: list[RelatedIdentifier] [metadata_identifiers.py]
│   ├── locations: list[Location] [metadata_location.py]
│   │   └── Location
│   │       └── features: GeoJSONFeature
│   │           └── GeoJSONFeature
│   │               ├── geometry: Geometry | None
│   │               └── identifiers: list[GeoLocationIdentifier]
│   ├── funding: list[FundingReference] [metadata_funding.py]
│   │   └── FundingReference
│   │       ├── funder: Funder
│   │       └── award: Award | None
│   │           └── Award
│   │               ├── funder: Funder | None
│   │               └── identifiers: list[AwardIdentifier]
│   └── references: list[GeneralReference] [metadata_reference.py]
├── files: FilesRecord [files.py]
│   └── entries: dict[str, DataCiteFile] | None
│       └── DataCiteFile
│           └── links: FileLinks
└── tombstone: Tombstone | None [tombstone.py]
```

## Notes

- `DataCite`, as defined in in `datacite_record.py`, is the root record model for the whole subpackage. It is available as
  `gamslib.datacite.Datacite`.
- `Contributor` inherits from `Creator` and reuses the `person_or_org` and `affiliations`
  structure from `metadata_people.py`.
- `Funder` is used in two places: directly by `FundingReference` and optionally inside `Award`.
- `FilesRecord` models the record-level `files` section, while `Metadata` contains the actual
  descriptive DataCite metadata.
- Helper/value classes from `common.py` and `vocabularies.py` are omitted here on purpose.
