"""The program that clears an agent's home of its own user's entries but the kept paths."""

import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TextIO

from factory.adapters.home_files import clear_home, own_entry
from factory.domain.agent_home import FRESH_HOME_PREFIX, inside_home

USAGE = "usage: fresh_home --home <folder> [--keep <path>]..."

_HOME_OPTION = "--home"
_KEEP_OPTION = "--keep"
_DONE = 0
_FAULTS = 1
_REFUSED = 2


class _Refusal(Exception):
    """Arguments refused before anything is removed; the message is the line to write."""


def main(
    argv: Sequence[str] | None = None,
    *,
    stderr: TextIO | None = None,
    owned: Callable[[Path], bool] | None = None,
) -> int:
    """Clear the home named by `--home` of this user's entries but the kept paths; 0 when done."""
    arguments = sys.argv[1:] if argv is None else list(argv)
    errors = sys.stderr if stderr is None else stderr
    try:
        home, kept = _parse(arguments)
    except _Refusal as refusal:
        errors.write(f"{FRESH_HOME_PREFIX} {refusal}\n")
        return _REFUSED
    faults = clear_home(home, kept, owned=owned or own_entry)
    for fault in faults:
        errors.write(f"{FRESH_HOME_PREFIX} {fault}\n")
    return _FAULTS if faults else _DONE


def _parse(arguments: list[str]) -> tuple[Path, list[str]]:
    # No default home: a call that names none must never clear one.
    if len(arguments) < 2 or len(arguments) % 2 or arguments[0] != _HOME_OPTION:
        raise _Refusal(USAGE)
    options = arguments[2::2]
    if any(option != _KEEP_OPTION for option in options):
        raise _Refusal(USAGE)
    return _home(arguments[1]), [_kept(path) for path in arguments[3::2]]


def _home(folder: str) -> Path:
    home = Path(folder)
    if not home.is_absolute() or home == Path("/") or not home.is_dir():
        raise _Refusal(f"{_HOME_OPTION} {folder} is not an absolute folder other than /")
    return home


def _kept(path: str) -> str:
    if not inside_home(path):
        raise _Refusal(f"{_KEEP_OPTION} {path} is not a path inside the home")
    return path


if __name__ == "__main__":
    sys.exit(main())
