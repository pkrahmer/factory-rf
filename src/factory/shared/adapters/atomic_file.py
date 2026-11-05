"""Replacing a file atomically, so that a reader sees the old text or the new, never half."""

import os
import tempfile
from pathlib import Path


def replace_text(path: Path, text: str) -> None:
    """Replace the file at `path` with `text`, creating its directory; raises `OSError`."""
    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=directory, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as file:
            file.write(text)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise
