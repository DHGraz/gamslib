# Copilot Instructions for `gamslib`

## Big picture architecture
- `src/gamslib` is a reusable library for GAMS5 projects; code is organized by domain package, mirrored by tests in `tests/<domain>`.
- Main domains:
  - `objectcsv/`: read/write/merge object metadata (`object.csv`, `datastreams.csv`) via `ObjectCSVManager` and `ObjectCollection`.
  - `projectconfiguration/`: central config loading and overrides (`project.toml` + `.env` + `GAMSCFG_*` env vars).
  - `formatdetect/`: pluggable format detectors returning `FormatInfo` (`siegfried` default; optional `magika`; fallback `base`).
  - `validation/`: schema discovery + validators (XML/XSD/RNG/RNC/Schematron, JSON/PDF/RDF validators).
  - `sip/`: Bag/SIP validation helpers and bag-related utility functions.
- Typical flow in higher-level features: load config (`get_configuration`) -> detect format (`formatdetect.detect_format`) -> validate or populate metadata.

## Developer workflows (use these first)
- Run tests: `make test` (internally `uv run pytest tests`).
- Run focused tests while editing: `uv run pytest tests/objectcsv/test_objectcsvmanager.py` (swap path as needed).
- Lint: `make lint` (`uv run ruff check src`).
- Coverage: `make coverage`.
- Build wheel/sdist: `make build`.
- Regenerate API docs: `make docs` (writes into `reference/`).

## Project-specific coding/testing patterns
- Use `pathlib.Path` consistently for filesystem logic; avoid raw string paths.
- CSV IO pattern is important: open with `encoding="utf-8", newline=""` and use `csv.DictReader/DictWriter` (see `objectcsv/objectcsvmanager.py`).
- Preserve readable domain errors: many modules wrap low-level exceptions into domain exceptions (`ObjectDirectoryValidationError`, `InvalidCSVFileError`, `BagValidationError`).
- Config and detector objects are cached (`@lru_cache`): tests that alter env/config must call cache clear (`get_configuration.cache_clear()`, `make_detector.cache_clear()` if needed).
- Tests rely heavily on `pytest` fixtures (`tmp_path`, `monkeypatch`, `datadir`/`shared_datadir`) and on realistic sample files under `tests/**/data`.
- When validating XML with remote schema URIs, behavior depends on trusted hosts (`general.safe_xml_hosts` or `GAMSCFG_SAFE_XML_HOSTS`).

## Integration points and dependency-sensitive behavior
- Optional detector dependency: `magika` (`gamslib[magika]`); default behavior uses `siegfried`/`pygfried`.
- Optional Schematron backend: `saxonche` (`gamslib[saxon]`) for xslt2/xpath2+ Schematron; otherwise lxml path is used when possible.
- XML validation imports `gams_xml_catalog` and `requests`; do not remove these side-effect imports without checking schema resolution.
- `pyproject.toml` is authoritative for dependencies, extras, Python version (`>=3.11`), and tooling.

## Scope and change strategy for agents
- Keep changes domain-local (e.g., `objectcsv` change + matching `tests/objectcsv/*`).
- Prefer extending existing dataclasses/models and validators over introducing parallel abstractions.
- Add/update tests next to the affected module and use existing fixture style before adding new fixture systems.
