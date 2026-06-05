"""Tests for shared validators and models in datacite metadata."""

import pytest
from pydantic import ValidationError

from gamslib.datacite.metadata import (
    Affiliation,
    Date,
    Language,
    LocalizedTitle,
    Metadata,
    PersonOrOrganization,
    PersonOrOrganizationIdentifier,
    Rights,
    Subject,
)


def test_localized_title_normalizes_iso_639_1_codes():
    """LocalizedTitle stores ISO 639-1 codes in lowercase."""
    title = LocalizedTitle(lang="EN", title="Example")

    assert title.lang == "en"


def test_localized_title_rejects_invalid_iso_639_1_codes():
    """LocalizedTitle rejects unknown ISO 639-1 codes."""
    with pytest.raises(ValidationError, match="not a valid ISO 639-1"):
        LocalizedTitle(lang="zz", title="Example")


def test_language_normalizes_iso_639_3_codes():
    """Language stores ISO 639-3 codes in lowercase."""
    language = Language(id="DEU")

    assert language.id == "deu"


def test_language_rejects_invalid_iso_639_3_codes():
    """Language rejects unknown ISO 639-3 codes."""
    with pytest.raises(ValidationError, match="not a valid ISO 639-3"):
        Language(id="zzz")


def test_person_or_organization_identifier_normalizes_scheme():
    """Identifier schemes are accepted case-insensitively and stored lowercase."""
    identifier = PersonOrOrganizationIdentifier(scheme="ORCID", identifier="0000-0000")

    assert identifier.scheme == "orcid"


def test_person_or_organization_accepts_valid_personal_values():
    """Personal entries require given and family names and reject organization name."""
    person = PersonOrOrganization(
        type="personal",
        given_name="Ada",
        family_name="Lovelace",
    )

    assert person.type == "personal"
    assert person.given_name == "Ada"
    assert person.family_name == "Lovelace"
    assert person.name is None


def test_person_or_organization_accepts_valid_organizational_values():
    """Organizational entries require name and reject personal name parts."""
    organization = PersonOrOrganization(type="organizational", name="University of Graz")

    assert organization.type == "organizational"
    assert organization.name == "University of Graz"
    assert organization.given_name is None
    assert organization.family_name is None


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        (
            {"type": "personal", "family_name": "Lovelace"},
            "both given_name and family_name are required",
        ),
        (
            {
                "type": "personal",
                "given_name": "Ada",
                "family_name": "Lovelace",
                "name": "University of Graz",
            },
            "name must not be set",
        ),
        (
            {"type": "organizational"},
            "name is required",
        ),
        (
            {
                "type": "organizational",
                "name": "University of Graz",
                "given_name": "Ada",
            },
            "given_name and family_name must not be set",
        ),
    ],
)
def test_person_or_organization_rejects_invalid_name_combinations(kwargs, message):
    """PersonOrOrganization enforces the type-specific name rules."""
    with pytest.raises(ValidationError, match=message):
        PersonOrOrganization(**kwargs)


def test_date_and_metadata_validate_edtf_values():
    """Date fields validate via the shared EDTF helper."""
    date = Date(date="2024/2025")
    metadata = Metadata(id="image-photo", title="Example", publication_date="2024-05", creators=[])

    assert date.date == "2024/2025"
    assert metadata.publication_date == "2024-05"


@pytest.mark.parametrize(
    ("factory", "kwargs"),
    [
        (Affiliation, {"id": "isni"}),
        (Affiliation, {"name": "University of Graz"}),
        (Rights, {"id": "https://example.org/license"}),
        (Rights, {"title": "CC-BY"}),
        (Subject, {"id": "https://example.org/subject"}),
        (Subject, {"subject": "Digital humanities"}),
    ],
)
def test_exactly_one_models_accept_single_value(factory, kwargs):
    """Models using the exactly-one helper accept exactly one populated field."""
    model = factory(**kwargs)

    for key, value in kwargs.items():
        assert getattr(model, key) == value


@pytest.mark.parametrize(
    ("factory", "kwargs", "message"),
    [
        (
            Affiliation,
            {"id": "isni", "name": "University of Graz"},
            "Exactly one of id or name must be provided for an affiliation.",
        ),
        (
            Affiliation,
            {},
            "Exactly one of id or name must be provided for an affiliation.",
        ),
        (
            Rights,
            {"id": "https://example.org/license", "title": "CC-BY"},
            "Exactly one of id or title must be provided for rights information.",
        ),
        (
            Subject,
            {"id": "https://example.org/subject", "subject": "Digital humanities"},
            "Exactly one of id or subject must be provided for a subject.",
        ),
    ],
)
def test_exactly_one_models_reject_invalid_combinations(factory, kwargs, message):
    """Models using the exactly-one helper reject zero or multiple populated fields."""
    with pytest.raises(ValidationError, match=message):
        factory(**kwargs)