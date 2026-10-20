"""Build agent homes under `tmp_path` and answer ownership for the fresh-home tests."""

from collections.abc import Callable, Iterable
from pathlib import Path


def build_home(home: Path, entries: Iterable[str]) -> None:
    """Create each entry under `home`: a name ending in `/` is a folder, any other a file."""
    for entry in entries:
        path = home / entry
        if entry.endswith("/"):
            path.mkdir(parents=True, exist_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()


def listing(home: Path) -> set[str]:
    """Every entry beneath `home`, links included, as its path relative to `home` in `/` form."""
    return {path.relative_to(home).as_posix() for path in home.rglob("*")}


def owned_but(home: Path, others: Iterable[str]) -> Callable[[Path], bool]:
    """An `owned` that is false for the named entries of `home` and true for every other."""
    foreign = set(others)

    def owned(path: Path) -> bool:
        return path.relative_to(home).as_posix() not in foreign

    return owned


def refusing(home: Path, refused: str) -> Callable[[Path], bool]:
    """An `owned` that raises `PermissionError` for the entry `refused` and is true otherwise."""

    def owned(path: Path) -> bool:
        if path.relative_to(home).as_posix() == refused:
            raise PermissionError(13, "Permission denied")
        return True

    return owned
