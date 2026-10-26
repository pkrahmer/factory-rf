"""The ZFS adapter's cache drop: after a rollback that succeeded, and only there."""

import shlex
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.printed_output import no_end_detail
from factory.adapters.zfs_snapshots import ZfsSnapshots
from factory.domain.errors import SnapshotError
from time_limits import ROOMY_BOUND_SECONDS
from zfs_support import DATASET, MOUNT_POINT, Answer, write_drop, write_zfs

LIMIT = timedelta(seconds=1)
REFUSAL = "sudo: a password is required"


@dataclass(frozen=True)
class DropPlan:
    """What the stand-in drop prints, how long it sleeps and how it exits."""

    printed: str = ""
    exit_status: int = 0
    sleep_seconds: int = 0


def _shell_zfs(folder: Path, record: Path, exit_status: int = 0) -> Path:
    # A `sh` stand-in starts within the one-second limit even when every core is busy.
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "zfs"
    path.write_text(
        f"#!/bin/sh\nprintf '%s\\n' \"$*\" >> {shlex.quote(str(record))}\nexit {exit_status}\n",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def test_the_reset_drops_the_cache_after_the_rollback(tmp_path: Path) -> None:
    record = tmp_path / "calls.txt"
    zfs = _shell_zfs(tmp_path / "zfs-bin", record)
    drop = write_drop(tmp_path / "drop-bin", record=record)
    snapshots = ZfsSnapshots(
        "tank/factory/vm", MOUNT_POINT, drop_caches=(str(drop.path),), executable=str(zfs)
    )

    snapshots.reset()

    assert record.read_text(encoding="utf-8").splitlines() == [
        "rollback -r tank/factory/vm@base",
        str(drop.path),
    ]


MISSING = "/nowhere/factory-drop-caches"


@pytest.mark.parametrize(
    ("rollback_status", "drop", "words", "command", "detail", "drop_called"),
    [
        pytest.param(
            1,
            DropPlan(),
            lambda path: (str(path),),
            lambda _, raised: "rollback -r" in raised,
            lambda _: True,
            False,
            id="rollback-fails",
        ),
        pytest.param(
            0,
            DropPlan(printed=f"{REFUSAL}\n", exit_status=1),
            lambda path: ("/bin/sh", str(path)),
            lambda path, raised: raised == f"/bin/sh {path}",
            lambda detail: REFUSAL in detail,
            True,
            id="drop-fails",
        ),
        pytest.param(
            0,
            DropPlan(),
            lambda _: (MISSING,),
            lambda _, raised: raised == MISSING,
            lambda _: True,
            False,
            id="drop-missing",
        ),
        pytest.param(
            0,
            DropPlan(sleep_seconds=60),
            lambda path: (str(path),),
            lambda path, raised: raised == str(path),
            lambda detail: detail == no_end_detail(LIMIT),
            True,
            id="drop-time-limit",
        ),
    ],
)
def test_a_fault_of_the_rollback_or_the_drop_is_a_snapshot_error(
    tmp_path: Path,
    *,
    rollback_status: int,
    drop: DropPlan,
    words: Callable[[Path], tuple[str, ...]],
    command: Callable[[Path, str], bool],
    detail: Callable[[str], bool],
    drop_called: bool,
) -> None:
    zfs = _shell_zfs(tmp_path / "zfs-bin", tmp_path / "zfs-calls.txt", rollback_status)
    stand_in = write_drop(
        tmp_path / "drop-bin",
        printed=drop.printed,
        exit_status=drop.exit_status,
        sleep_seconds=drop.sleep_seconds,
    )
    snapshots = ZfsSnapshots(
        DATASET,
        MOUNT_POINT,
        drop_caches=words(stand_in.path),
        executable=str(zfs),
        time_limit=LIMIT,
    )

    started = time.monotonic()
    with pytest.raises(SnapshotError) as raised:
        snapshots.reset()
    elapsed = time.monotonic() - started

    assert command(stand_in.path, raised.value.command), raised.value.command
    assert detail(raised.value.detail), raised.value.detail
    assert (stand_in.calls() != []) is drop_called
    assert elapsed < ROOMY_BOUND_SECONDS


@pytest.mark.parametrize(
    ("plan", "call"),
    [
        pytest.param({}, lambda s: s.advance(), id="advance"),
        pytest.param({}, lambda s: s.changed_paths(), id="changed-paths"),
        pytest.param(
            {"--version": Answer(stdout="zfs-2.2.2\n")}, lambda s: s.version(), id="version"
        ),
        pytest.param(
            {"list": Answer(stdout=f"{DATASET}\n")},
            lambda s: s.dataset_exists(),
            id="dataset-exists",
        ),
    ],
)
def test_only_the_reset_drops_the_cache(
    tmp_path: Path, plan: dict[str, Answer], call: Callable[[ZfsSnapshots], object]
) -> None:
    zfs = write_zfs(tmp_path / "zfs-bin", plan)
    drop = write_drop(tmp_path / "drop-bin")
    snapshots = ZfsSnapshots(
        DATASET, MOUNT_POINT, drop_caches=(str(drop.path),), executable=str(zfs.path)
    )

    call(snapshots)

    assert drop.calls() == []


@pytest.mark.parametrize(
    ("words", "accepted"),
    [
        pytest.param((), False, id="empty"),
        pytest.param(("x",), True, id="one-word"),
    ],
)
def test_the_drop_command_must_name_a_program(words: tuple[str, ...], accepted: bool) -> None:
    if accepted:
        ZfsSnapshots(DATASET, MOUNT_POINT, drop_caches=words)
    else:
        with pytest.raises(ValueError, match=r".+"):
            ZfsSnapshots(DATASET, MOUNT_POINT, drop_caches=words)
