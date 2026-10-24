"""The rule of the fresh home: which entries of an agent's home a run leaves, and which go."""

from collections.abc import Sequence
from pathlib import Path
from typing import Final, Literal

FRESH_HOME_PREFIX: Final = "factory-fresh-home:"
HomeFate = Literal["keep", "descend", "remove"]


def inside_home(relative: str) -> bool:
    """Whether `relative` names a path inside a home: not empty, not absolute, no `.` or `..`."""
    # An absolute path begins with an empty segment; `Path` would fold `a//b` and `./a`.
    return not any(segment in {"", ".", ".."} for segment in relative.split("/"))


def kept_paths(
    home: Path,
    *,
    login_files: Sequence[Path | None],
    state_files: Sequence[str],
    folders: Sequence[str],
) -> list[str]:
    """The paths, relative to `home`, that a fresh home keeps, in order and without repeats."""
    logins = [
        login.relative_to(home).as_posix()
        for login in login_files
        if login is not None and login.is_relative_to(home)
    ]
    named = [*state_files, *folders]
    for relative in named:
        if not inside_home(relative):
            raise ValueError(f"{relative} is not a path inside the home")
    return list(dict.fromkeys([*logins, *named]))


def fate(relative: str, *, owned: bool, folder: bool, kept: Sequence[str]) -> HomeFate:
    """What the program does with the entry `relative` of the home."""
    if any(beneath_or_at(relative, path) for path in kept):
        return "keep"
    if folder:
        return "descend"
    return "remove" if owned else "keep"


def removed_when_empty(relative: str, *, owned: bool, kept: Sequence[str]) -> bool:
    """Whether a folder the walk descended into is removed once it is empty."""
    return owned and not any(beneath_or_at(path, relative) for path in kept)


def beneath_or_at(relative: str, above: str) -> bool:
    """Whether the `/`-separated path `relative` is `above` itself or lies under it."""
    return relative == above or relative.startswith(f"{above}/")
