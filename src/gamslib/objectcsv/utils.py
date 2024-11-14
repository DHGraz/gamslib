"""Utility functions for the objectcsv module."""

import logging
from pathlib import Path
from typing import Generator

logger = logging.getLogger()


def find_object_folders(root_directory: Path) -> Generator[Path, None, None]:
    """Find all object folders below root_directory."""
    for directory in root_directory.rglob("*"):
        if directory.is_dir():
            if "DC.xml" in [f.name for f in directory.iterdir()]:
                yield directory
            else:
                #    if not directory == root_directory:
                logger.warning(
                    "Skipping folder %s as it does not contain a DC.xml file.",
                    directory,
                )
