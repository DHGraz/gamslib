"Provides a configuration class"

# pylint: disable=too-many-arguments
# pylint: disable=too-few-public-methods


from pathlib import Path
from typing import Annotated, Literal

import tomllib
from pydantic import BaseModel, ValidationError, StringConstraints


def find_project_toml(start_dir: Path) -> Path:
    """Find the project.toml file in the start_dir or above.

    Return a path object to the project.toml file.
    If no project.toml file is found, raise a FileNotFoundError.
    """
    for folder in (start_dir / "a_non_existing_folder_to_include_start_dir").parents:
        project_toml = folder / "project.toml"
        if project_toml.exists():
            return project_toml

    # if we read this point, no project.toml has been found in object_root or above
    # So we check if there's a project.toml in the current working directory
    project_toml = Path.cwd() / "project.toml"

    if project_toml.exists():
        return project_toml
    raise FileNotFoundError("No project.toml file found in or above the start_dir.")


class Metadata(BaseModel, validate_assignment=True):
    """Represent the 'metadata' section of the configuration file."""

    project_id: Annotated[str, StringConstraints(min_length=2)]
    creator: Annotated[str, StringConstraints(min_length=3)]
    publisher: Annotated[str, StringConstraints(min_length=3)]
    rights: str = ""


class General(BaseModel, validate_assignment=True):
    """Represent the 'general' section of the configuration file."""

    dsid_keep_extension: bool = True
    loglevel: Literal["debug", "info", "warning", "error", "critical"] = "info"


class Configuration(BaseModel):
    """Represent the configuration from the project toml file.

    Properties can be accessed as attributes of the object and sub object:
        eg.: metadata.rights
    """

    toml_file: Path
    metadata: Metadata
    general: General

    @classmethod
    def _make_readable_message(cls, cfgfile, error_type: str, loc: tuple) -> str | None:
        """Return a readable error message or None.

        Helper function which creates a readable error messages.

        Returns a readable error message or None if 'type' is not known by function.
        """
        # There are many more types which could be handled, but are not needed yet.
        # See: https://docs.pydantic.dev/latest/errors/validation_errors/
        reasons = {
            "missing": "missing required field",
            "string_too_short": "value is too short",
            "bool_type": "value is not a boolean",
            "bool_parsing": "value is not a boolean",
            "literal_error": "value is not allowed here",
        }

        loc_str = ".".join([str(e) for e in loc])
        reason = reasons.get(error_type)
        if reason is None:
            return None
        return f"Error in project TOML file '{cfgfile}'. {reason}: '{loc_str}'"

    @classmethod
    def from_toml(cls, toml_file: Path) -> "Configuration":
        """Create a configuration object from a toml file."""
        try:
            with toml_file.open("r", encoding="utf-8", newline="") as tfile:
                data = tomllib.loads(tfile.read())
                data["toml_file"] = toml_file
            return cls(**data)
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                f"Configuration file '{toml_file.parent}' not found."
            ) from exc
        except tomllib.TOMLDecodeError as exc:
            raise tomllib.TOMLDecodeError(
                f"Error in project TOML file '{toml_file}': {exc}"
            ) from exc
        except ValidationError as exc:
            msg = cls._make_readable_message(
                toml_file, exc.errors()[0]["type"], exc.errors()[0]["loc"]
            )
            raise ValueError(msg) from exc
