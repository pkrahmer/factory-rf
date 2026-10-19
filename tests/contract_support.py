"""What the contract command's tests share: its output lines and a row of `main`'s cases."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

WRITTEN = "contract: 5 schemas written\n"
USAGE = "usage: python -m factory.entry.contract [<folder>]\n"


@dataclass(frozen=True)
class MainRow:
    """One case of the contract command: its arguments, where it writes, what it prints."""

    arguments: Callable[[Path], list[str]]
    written: Callable[[Path], Path] | None
    out: str
    err: str
    code: int
