"""Helpers the transcript tests share."""

import hashlib
from pathlib import Path


def sha256_of(path: Path) -> str:
    """The hex SHA-256 of the file at `path`."""
    return hashlib.sha256(path.read_bytes()).hexdigest()
