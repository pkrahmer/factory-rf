"""The snapshots of a ZFS dataset, reached through the `zfs` executable."""

import math
import re
from datetime import timedelta
from pathlib import Path, PurePosixPath

from factory.adapters.process import ProcessRequest, ProcessResult, run_process
from factory.application.snapshots import Snapshots
from factory.domain.errors import SnapshotError
from factory.domain.git import ChangedPath, ChangeKind

BASE_SNAPSHOT = "base"
SNAPSHOT_TIME_LIMIT = timedelta(minutes=10)

_ROOT = Path("/")
_DIRECTORY_KIND = "/"
_RENAME = "R"
_CHANGES: dict[str, ChangeKind] = {"M": "modified", "+": "added", "-": "deleted"}
_OCTAL_ESCAPE = re.compile(rb"\\([0-7]{3})")


class _UnreadableLine(Exception):
    """A line of `zfs diff` the adapter cannot read; its message is the fault's detail."""


def _printed_lines(output: str) -> list[str]:
    return [line.strip() for line in output.splitlines() if line.strip()]


def _last_line(output: str) -> str | None:
    printed = _printed_lines(output)
    return printed[-1] if printed else None


def _first_line(output: str) -> str | None:
    printed = _printed_lines(output)
    return printed[0] if printed else None


def _failure_detail(result: ProcessResult) -> str:
    return _last_line(result.stdout) or f"exit status {result.exit_status}"


def _unescape(path: str, line: str) -> str:
    # `zfs` writes every byte outside printable ASCII, and the backslash, as `\ooo`.
    raw = _OCTAL_ESCAPE.sub(lambda match: bytes([int(match[1], 8)]), path.encode())
    try:
        return raw.decode()
    except UnicodeDecodeError as error:
        raise _UnreadableLine(f"cannot read the line {line}") from error


class ZfsSnapshots(Snapshots):
    """The dataset of a ZFS pool and its snapshot `@base`, reached through the `zfs` executable."""

    def __init__(
        self,
        dataset: str,
        mount_point: Path,
        *,
        executable: str = "zfs",
        time_limit: timedelta = SNAPSHOT_TIME_LIMIT,
    ) -> None:
        """Work on `dataset`, mounted at `mount_point`, through `executable`."""
        self._dataset = dataset
        self._mount_point = mount_point
        self._executable = executable
        self._time_limit = time_limit

    @property
    def mount_point(self) -> Path:
        """The path given, as given."""
        return self._mount_point

    @property
    def _base(self) -> str:
        return f"{self._dataset}@{BASE_SNAPSHOT}"

    def reset(self) -> None:
        """Roll the dataset back to `@base`, removing every later snapshot."""
        self._run(["rollback", "-r", self._base])

    def advance(self) -> None:
        """Destroy `@base` when it exists and take it anew."""
        listing = self._run(
            ["list", "-H", "-o", "name", "-t", "snapshot", self._base], accepted=(0, 1)
        )
        if listing.exit_status == 0:
            self._run(["destroy", self._base])
        self._run(["snapshot", self._base])

    def changed_paths(self) -> list[ChangedPath]:
        """Every non-directory entry `zfs diff` names against `@base`, relative to the mount."""
        arguments = ["diff", "-FH", self._base]
        result = self._run(arguments)
        changes: dict[str, ChangeKind] = {}
        try:
            for line in result.stdout.splitlines():
                if line.strip():
                    self._read_diff_line(line, changes)
        except _UnreadableLine as error:
            raise SnapshotError(self._command(arguments), str(error)) from error
        return [ChangedPath(path=path, change=changes[path]) for path in sorted(changes)]

    def version(self) -> str:
        """The first non-blank line `<zfs> --version` prints; `SnapshotError` when it fails."""
        arguments = ["--version"]
        version = _first_line(self._run(arguments).stdout)
        if version is None:
            raise SnapshotError(self._command(arguments), "printed nothing")
        return version

    def dataset_exists(self) -> bool:
        """Whether `<zfs> list -H -o name <dataset>` names it; a fault is `SnapshotError`."""
        arguments = ["list", "-H", "-o", "name", self._dataset]
        result = self._run(arguments, accepted=(0, 1))
        if result.exit_status == 1:
            return False
        named = _first_line(result.stdout)
        if named != self._dataset:
            raise SnapshotError(self._command(arguments), f"named {named}, not {self._dataset}")
        return True

    def _read_diff_line(self, line: str, changes: dict[str, ChangeKind]) -> None:
        fields = line.split("\t")
        change = fields[0]
        needed = 4 if change == _RENAME else 3
        if len(fields) < needed or (change != _RENAME and change not in _CHANGES):
            raise _UnreadableLine(f"cannot read the line {line}")
        kind = fields[1]
        found: list[tuple[str, ChangeKind]]
        if change == _RENAME:
            found = [(fields[2], "deleted"), (fields[3], "added")]
        else:
            found = [(fields[2], _CHANGES[change])]
        for path, path_change in found:
            relative = self._relative(_unescape(path, line))
            if kind != _DIRECTORY_KIND:
                _record(changes, relative, path_change)

    def _relative(self, path: str) -> str:
        mount_point = PurePosixPath(self._mount_point)
        if not PurePosixPath(path).is_relative_to(mount_point):
            raise _UnreadableLine(f"{path} is outside {self._mount_point}")
        return PurePosixPath(path).relative_to(mount_point).as_posix()

    def _command(self, arguments: list[str]) -> str:
        return " ".join([self._executable, *arguments])

    def _run(self, arguments: list[str], *, accepted: tuple[int, ...] = (0,)) -> ProcessResult:
        request = ProcessRequest(
            argv=[self._executable, *arguments],
            cwd=_ROOT,
            env=None,
            time_limit=self._time_limit,
            merge_stderr=True,
        )
        try:
            result = run_process(request)
        except OSError as error:
            raise SnapshotError(self._command(arguments), str(error)) from error
        if result.timed_out:
            seconds = math.ceil(self._time_limit.total_seconds())
            raise SnapshotError(self._command(arguments), f"no end within {seconds} s")
        if result.exit_status not in accepted:
            raise SnapshotError(self._command(arguments), _failure_detail(result))
        return result


def _record(changes: dict[str, ChangeKind], path: str, change: ChangeKind) -> None:
    # A path one line removes and another adds exists in the dataset now: it is an addition.
    previous = changes.get(path)
    changes[path] = "added" if "added" in (previous, change) else change
