"""A command's input file, read as UTF-8 text in one place."""

from pathlib import Path


class UnreadableInput(Exception):
    """A command's input file that cannot be read as UTF-8 text."""


def read_input(path: Path) -> str:
    """Return the file's text read as UTF-8, or raise `UnreadableInput`."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise UnreadableInput(f"cannot read {path}: {error}") from error
