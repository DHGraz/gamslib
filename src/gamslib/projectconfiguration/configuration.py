"A Configuration class for gams projects."

# pylint: disable=too-many-arguments
# pylint: disable=too-few-public-methods

import logging
import os
import tomllib
from pathlib import Path
from typing import Annotated, Any, Literal

from dotenv import dotenv_values
from pydantic import BaseModel, StringConstraints, ValidationError

logger = logging.getLogger(__name__)


class Metadata(BaseModel, validate_assignment=True):
    """Represent the 'metadata' section of the configuration file."""

    project_id: Annotated[str, StringConstraints(min_length=2)]
    creator: Annotated[str, StringConstraints(min_length=3)]
    publisher: Annotated[str, StringConstraints(min_length=3)]
    rights: str = ""
    funder:str = ""


class General(BaseModel, validate_assignment=True):
    """Represent the 'general' section of the configuration file."""

    dsid_keep_extension: bool = True
    loglevel: Literal["debug", "info", "warning", "error", "critical"] = "info"
    format_detector: Literal["magika", "base", ""] = "magika"
    format_detector_url: str = ""
    ds_ignore_files: list[str] = []


class Configuration(BaseModel):
    """Represent the configuration from the project toml file.

    Properties can be accessed as attributes of the object and sub object:
        eg.: metadata.rights
    """

    toml_file: Path
    metadata: Metadata
    general: General

    def model_post_init(self, context: Any, /) -> None:
        self._update_from_dotenv()
        self._update_from_env()

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

    def _update_from_dotenv(self, dotenv_file: Path | None = None):
        """Update the configuration object from the '.env' file."""
        if dotenv_file is None:
            dotenv_file = Path.cwd() / ".env"
        for key, value in dotenv_values(dotenv_file).items():
            if "." in key:  # global fields are ignored
                table, field = key.lower().split(".")
                logger.debug("Setting %s to %s (from .env file.)", key, value)
                if table == "metadata":
                    setattr(self.metadata, field, value)
                elif table == "general":
                    setattr(self.general, field, value)

    def _update_from_env(self):
        """Update the configuration object from environment variables."""
        for key, value in os.environ.items():
            if key.startswith("GAMSCFG_") and key != "GAMSCFG_PROJECT_TOML":
                new_key = key[8:].lower()
                if "_" in new_key:
                    table, field = new_key.split("_", 1)
                    logger.debug(
                        "Setting %s to %s (from environment variable.)", key, value
                    )
                    if table == "metadata":
                        setattr(self.metadata, field, value)
                    elif table == "general":
                        setattr(self.general, field, value)
