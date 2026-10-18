"""The rules of one confined run, the targets they come from, and the Landlock ABI they need."""

from collections.abc import Collection, Sequence
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from factory.domain.agent_runs import AbsolutePath, GuardSettings
from factory.domain.pipeline_definition import (
    CURRENT_SEGMENT,
    HOME_PREFIX,
    has_wildcard,
    tool_path_folder,
)
from factory.domain.write_paths import is_inside_checkout

LANDLOCK_MINIMUM_ABI = 3
# The devices a shell and its tools write to; a run allows those of them that exist.
DEVICE_FILES: tuple[str, ...] = (
    "/dev/null",
    "/dev/zero",
    "/dev/full",
    "/dev/random",
    "/dev/urandom",
    "/dev/tty",
)
DEVICE_FOLDERS: tuple[str, ...] = ("/dev/shm",)


def abi_fault(abi: int) -> str | None:
    """The fault of a kernel that offers Landlock ABI `abi`, or `None` when it suffices."""
    if abi >= LANDLOCK_MINIMUM_ABI:
        return None
    return (
        f"the kernel offers Landlock ABI {abi}, "
        f"the write guard needs ABI {LANDLOCK_MINIMUM_ABI} or higher"
    )


class Confinement(BaseModel):
    """The writes one agent run may make: folders, single files and its own temporary folder."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    folders: list[AbsolutePath]
    files: list[AbsolutePath]
    temporary_directory: AbsolutePath


TargetKind = Literal["folder", "file"]


class WriteTarget(BaseModel):
    """One path the kernel may allow: a folder and everything beneath it, or one file."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: AbsolutePath
    kind: TargetKind


def write_targets(guard: GuardSettings, *, home: Path | None) -> list[WriteTarget]:
    """The kernel's targets of the write paths, then the tool paths, of `guard`."""
    targets = [
        *(_write_path_target(path, guard.root) for path in guard.write_paths),
        *(_tool_path_target(path, guard.root, home) for path in guard.tool_paths),
    ]
    return _unique([target for target in targets if target is not None])


def confinement_of(
    targets: Sequence[WriteTarget],
    *,
    root: Path,
    existing_files: Collection[Path],
    extras: Sequence[WriteTarget],
    temporary_directory: Path,
) -> Confinement:
    """The rules of one run: the targets as the files that exist allow them, and the extras."""
    allowed = [_as_allowed(target, root, existing_files) for target in targets]
    narrowed = [target for target in allowed if target is not None]
    return Confinement(
        folders=_unique(_paths_of(narrowed, "folder") + _paths_of(extras, "folder")),
        files=_unique(_paths_of(narrowed, "file") + _paths_of(extras, "file")),
        temporary_directory=temporary_directory,
    )


def _write_path_target(write_path: str, root: Path) -> WriteTarget | None:
    segments = write_path.split("/")
    # pathlib collapses a `.` segment, so it could name the root or the folder above it.
    if not is_inside_checkout(write_path) or CURRENT_SEGMENT in segments:
        return None
    first_wildcard = next(
        (index for index, segment in enumerate(segments) if has_wildcard(segment)), None
    )
    if first_wildcard is None:
        return WriteTarget(path=root / write_path, kind="file")
    # The kernel names no pattern, so a wildcard widens to the folder above it; the undo
    # narrows what the pattern does not match. Never the root: that would allow everything.
    if first_wildcard == 0:
        return None
    return WriteTarget(path=root.joinpath(*segments[:first_wildcard]), kind="folder")


def _tool_path_target(tool_path: str, root: Path, home: Path | None) -> WriteTarget | None:
    folder = tool_path_folder(tool_path)
    if folder is None:
        return None
    if not folder.startswith(HOME_PREFIX):
        return WriteTarget(path=root / folder, kind="folder")
    if home is None:
        return None
    return WriteTarget(path=home / folder.removeprefix(HOME_PREFIX), kind="folder")


def _as_allowed(
    target: WriteTarget, root: Path, existing_files: Collection[Path]
) -> WriteTarget | None:
    if target.kind == "folder" or target.path in existing_files:
        return target
    # The kernel allows writes on existing files only, so a file still to be made widens to
    # its folder; at the root that folder would be the whole checkout, so it gives nothing.
    if target.path.parent == root:
        return None
    return WriteTarget(path=target.path.parent, kind="folder")


def _paths_of(targets: Sequence[WriteTarget], kind: TargetKind) -> list[Path]:
    return [target.path for target in targets if target.kind == kind]


def _unique[T](items: Sequence[T]) -> list[T]:
    return list(dict.fromkeys(items))
