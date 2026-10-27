"""The ZFS adapter: the reset, the advance, the faults, the version and the dataset's presence."""

import re
import time
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters import process
from factory.adapters.process import ProcessResult
from factory.adapters.zfs_snapshots import SNAPSHOT_TIME_LIMIT, ZfsSnapshots
from factory.application.snapshots import Snapshots
from factory.domain.errors import SnapshotError
from run_process_recorder import Recorder
from time_limits import ROOMY_BOUND_SECONDS
from zfs_support import DATASET, MOUNT_POINT, Answer, snapshots_on, write_zfs

BASE = f"{DATASET}@base"
LIST_BASE = ["list", "-H", "-o", "name", "-t", "snapshot", BASE]
DESTROY = ["destroy", BASE]
SNAPSHOT = ["snapshot", BASE]
ROLLBACK = ["rollback", "-r", BASE]
DROP = ("/nowhere/factory-drop-caches",)


def test_reset_rolls_back_to_the_base_and_keeps_the_mount_point(tmp_path: Path) -> None:
    zfs = write_zfs(tmp_path)
    snapshots = snapshots_on(zfs)

    snapshots.reset()

    assert zfs.arguments() == [ROLLBACK]
    assert snapshots.mount_point == Path("/srv/factory/vm/work")


@pytest.mark.parametrize(
    ("plan", "calls", "failed", "detail"),
    [
        pytest.param({"list": Answer()}, [LIST_BASE, DESTROY, SNAPSHOT], None, None, id="base"),
        pytest.param(
            {
                "list": Answer(
                    stderr=f"cannot open '{BASE}': dataset does not exist\n", exit_status=1
                )
            },
            [LIST_BASE, SNAPSHOT],
            None,
            None,
            id="no-base",
        ),
        pytest.param({"list": Answer(exit_status=2)}, [LIST_BASE], LIST_BASE, None, id="list-2"),
        pytest.param(
            {
                "list": Answer(),
                "destroy": Answer(
                    stdout=f"cannot destroy '{BASE}': dataset is busy\n", exit_status=1
                ),
            },
            [LIST_BASE, DESTROY],
            DESTROY,
            f"cannot destroy '{BASE}': dataset is busy",
            id="destroy-fails",
        ),
        pytest.param(
            {
                "list": Answer(),
                "snapshot": Answer(
                    stdout=f"cannot create snapshot '{BASE}': out of space\n", exit_status=1
                ),
            },
            [LIST_BASE, DESTROY, SNAPSHOT],
            SNAPSHOT,
            f"cannot create snapshot '{BASE}': out of space",
            id="snapshot-fails",
        ),
    ],
)
def test_advance_replaces_the_base_by_what_list_says(
    tmp_path: Path,
    plan: dict[str, Answer],
    calls: list[list[str]],
    failed: list[str] | None,
    detail: str | None,
) -> None:
    zfs = write_zfs(tmp_path, plan)

    if failed is None:
        snapshots_on(zfs).advance()
    else:
        with pytest.raises(SnapshotError) as raised:
            snapshots_on(zfs).advance()
        assert raised.value.command == zfs.command(*failed)
        if detail is not None:
            assert raised.value.detail == detail

    assert zfs.arguments() == calls


@pytest.mark.parametrize(
    ("answer", "time_limit", "detail", "at_least_seconds"),
    [
        pytest.param(
            Answer(stdout="warning\nrollback: dataset is busy\n", exit_status=1),
            SNAPSHOT_TIME_LIMIT,
            re.escape("rollback: dataset is busy"),
            0,
            id="last-line",
        ),
        pytest.param(
            Answer(stdout="rollback: dataset is busy\n\n", exit_status=1),
            SNAPSHOT_TIME_LIMIT,
            re.escape("rollback: dataset is busy"),
            0,
            id="trailing-blank",
        ),
        pytest.param(Answer(exit_status=1), SNAPSHOT_TIME_LIMIT, "exit status 1", 0, id="silent"),
        pytest.param(
            Answer(sleep_seconds=60),
            timedelta(seconds=1.5),
            "no end within 2 s",
            1,
            id="time-limit",
        ),
        pytest.param(None, SNAPSHOT_TIME_LIMIT, r"\[Errno 2\].*", 0, id="missing"),
    ],
)
def test_a_failed_reset_names_its_detail(
    tmp_path: Path,
    answer: Answer | None,
    time_limit: timedelta,
    detail: str,
    at_least_seconds: float,
) -> None:
    # No answer stands for an executable that does not exist.
    zfs = write_zfs(tmp_path, {} if answer is None else {"rollback": answer})
    executable = "/nowhere/zfs" if answer is None else str(zfs.path)
    snapshots = ZfsSnapshots(
        DATASET, MOUNT_POINT, drop_caches=DROP, executable=executable, time_limit=time_limit
    )

    started = time.monotonic()
    with pytest.raises(SnapshotError) as raised:
        snapshots.reset()
    elapsed = time.monotonic() - started

    assert raised.value.command.startswith(f"{executable} rollback")
    assert re.fullmatch(detail, raised.value.detail)
    assert at_least_seconds <= elapsed < ROOMY_BOUND_SECONDS


def test_the_default_time_limit_is_ten_minutes_and_reaches_run_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recording = Recorder()
    success = ProcessResult(
        exit_status=0, stdout="", stderr="", timed_out=False, duration=timedelta(0)
    )
    recording.results.extend([success, success])
    monkeypatch.setattr(process, "run_process", recording)

    ZfsSnapshots(DATASET, MOUNT_POINT, drop_caches=DROP, executable="/nowhere/zfs").reset()

    assert timedelta(minutes=10) == SNAPSHOT_TIME_LIMIT
    [rollback] = [request for request in recording.requests if request.argv[1:2] == ["rollback"]]
    assert rollback.time_limit == SNAPSHOT_TIME_LIMIT


@pytest.mark.parametrize(
    "time_limit",
    [
        pytest.param(timedelta(seconds=1.2), id="fraction"),
        pytest.param(timedelta(seconds=2), id="whole"),
    ],
)
def test_the_time_limit_is_named_in_whole_seconds_rounded_up(
    monkeypatch: pytest.MonkeyPatch, time_limit: timedelta
) -> None:
    recording = Recorder()
    recording.results.append(
        ProcessResult(exit_status=None, stdout="", stderr="", timed_out=True, duration=time_limit)
    )
    monkeypatch.setattr(process, "run_process", recording)

    with pytest.raises(SnapshotError) as raised:
        ZfsSnapshots(
            DATASET,
            MOUNT_POINT,
            drop_caches=DROP,
            executable="/nowhere/zfs",
            time_limit=time_limit,
        ).reset()

    assert raised.value.detail == "no end within 2 s"


def test_a_command_merges_stderr_runs_at_the_root_in_the_factorys_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ZFS_STAND_IN_MARK", "set by the test")
    zfs = write_zfs(tmp_path, {"rollback": Answer(stderr="boom\n", exit_status=1)})

    with pytest.raises(SnapshotError) as raised:
        snapshots_on(zfs).reset()

    assert raised.value.detail == "boom"
    [call] = zfs.calls()
    assert call.working_directory == Path("/")
    assert call.environment["ZFS_STAND_IN_MARK"] == "set by the test"


@pytest.mark.parametrize(
    ("answer", "returned", "detail"),
    [
        pytest.param(
            Answer(stdout="zfs-2.2.2-0ubuntu9.1\nzfs-kmod-2.2.2-0ubuntu9.1\n"),
            "zfs-2.2.2-0ubuntu9.1",
            None,
            id="first-line",
        ),
        pytest.param(
            Answer(stdout="\nzfs-2.2.2-0ubuntu9.1\n"),
            "zfs-2.2.2-0ubuntu9.1",
            None,
            id="leading-blank",
        ),
        pytest.param(
            Answer(stdout="  zfs-2.2.2-0ubuntu9.1  \nzfs-kmod-2.2.2-0ubuntu9.1\n"),
            "zfs-2.2.2-0ubuntu9.1",
            None,
            id="stripped",
        ),
        pytest.param(Answer(), None, "printed nothing", id="nothing"),
        pytest.param(
            Answer(stdout="zfs: command not found\n", exit_status=1),
            None,
            "zfs: command not found",
            id="fails",
        ),
    ],
)
def test_version_is_the_first_line_zfs_prints(
    tmp_path: Path, answer: Answer, returned: str | None, detail: str | None
) -> None:
    zfs = write_zfs(tmp_path, {"--version": answer})

    if returned is not None:
        assert snapshots_on(zfs).version() == returned
    else:
        with pytest.raises(SnapshotError) as raised:
            snapshots_on(zfs).version()
        assert raised.value.detail == detail
    assert zfs.arguments() == [["--version"]]


@pytest.mark.parametrize(
    ("answer", "returned", "detail"),
    [
        pytest.param(Answer(stdout=f"{DATASET}\n"), True, None, id="named"),
        pytest.param(
            Answer(stderr=f"cannot open '{DATASET}': dataset does not exist\n", exit_status=1),
            False,
            None,
            id="none",
        ),
        pytest.param(
            Answer(stdout="tank/other\n"), None, f"named tank/other, not {DATASET}", id="other"
        ),
        pytest.param(Answer(), None, "printed nothing", id="nothing"),
        pytest.param(
            Answer(stdout=f"warning\ncannot open '{DATASET}': permission denied\n", exit_status=2),
            None,
            f"cannot open '{DATASET}': permission denied",
            id="fails",
        ),
    ],
)
def test_dataset_exists_reads_what_list_names(
    tmp_path: Path, answer: Answer, returned: bool | None, detail: str | None
) -> None:
    zfs = write_zfs(tmp_path, {"list": answer})

    if returned is not None:
        assert snapshots_on(zfs).dataset_exists() is returned
    else:
        with pytest.raises(SnapshotError) as raised:
            snapshots_on(zfs).dataset_exists()
        assert raised.value.detail == detail
    assert zfs.arguments() == [["list", "-H", "-o", "name", DATASET]]


def test_the_adapter_implements_the_snapshots_interface(tmp_path: Path) -> None:
    assert isinstance(snapshots_on(write_zfs(tmp_path)), Snapshots)
