"""The tick publishes the stop records right after the restore, and goes on when it cannot."""

import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import override

import pytest

from disk_support import FakeDiskSpace
from factory.adapters.git_cli import GitCli
from factory.adapters.process import ProcessRequest, run_process
from factory.adapters.record_log_jsonl import JsonLinesRecordLog
from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Handler
from factory.application.tick import IdleHandler, Tick
from factory.domain.disk import GIGABYTE
from factory.domain.events import EventKind
from factory.domain.git import GitOptions
from factory.domain.paths import STOP_RECORDS_FILE
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.settings import InstanceSettings
from factory.domain.stops import StopRecord, parse_stop_records
from git_support import (
    CHECKOUT,
    COLOURED_AGENT_FILE,
    PIPELINE_YAML,
    TEST_IDENTITY,
    remote_commit,
    run_git,
    write_agent,
)
from human_clone import HumanClone
from log_support import log_lines
from stage_run_support import INSTANCE

MIN_FREE_GB = 2
ENOUGH = MIN_FREE_GB * GIGABYTE
LOCAL = StopRecord(
    event="raised",
    scope="repository",
    reason="main_branch_failing",
    at=datetime(2026, 10, 12, 11, 0, tzinfo=UTC),
)
ROOT = os.geteuid() == 0


@dataclass(frozen=True)
class _Context:
    tmp_path: Path
    remote: Path
    human: HumanClone
    agent_home: Path
    records: JsonLinesRecordLog[StopRecord]
    settings: InstanceSettings
    disk: FakeDiskSpace

    @property
    def checkout(self) -> Path:
        return self.tmp_path / CHECKOUT


Step = Callable[[_Context], None]
# After a tick: the (event, reason) pairs of main's file, or None for "no new commit on main".
Expected = list[tuple[str, str]] | None


def _handlers(_definition: PipelineDefinition) -> Mapping[EventKind, Handler]:
    return {"idle": IdleHandler()}


def _remote_file(remote: Path) -> str | None:
    result = run_process(
        ProcessRequest(argv=["git", "show", f"main:{STOP_RECORDS_FILE}"], cwd=remote)
    )
    return result.stdout if result.exit_status == 0 else None


def _remote_pairs(remote: Path) -> list[tuple[str, str]]:
    text = _remote_file(remote) or ""
    return [(record.event, record.reason) for record in parse_stop_records(text)]


pytestmark = pytest.mark.usefixtures("installed_agents")


@pytest.fixture
def settings(tmp_path: Path) -> InstanceSettings:
    """Settings whose checkout and state directory lie under `tmp_path`."""
    return InstanceSettings.model_validate(
        {
            "repository_url": "/srv/project.git",
            "instance": INSTANCE,
            "checkout": tmp_path / CHECKOUT,
            "state_directory": tmp_path / "state",
            "min_free_gb": MIN_FREE_GB,
        }
    )


@pytest.fixture
def disk(settings: InstanceSettings) -> FakeDiskSpace:
    """Enough free space on the work and the state directory."""
    return FakeDiskSpace(free={settings.checkout.parent: ENOUGH, settings.state_directory: ENOUGH})


@pytest.fixture
def context(
    tmp_path: Path,
    remote: Path,
    human: HumanClone,
    agent_home: Path,
    *,
    records: JsonLinesRecordLog[StopRecord],
    settings: InstanceSettings,
    disk: FakeDiskSpace,
) -> _Context:
    """Everything a step of a row may change before a tick."""
    return _Context(tmp_path, remote, human, agent_home, records, settings, disk)


def _nothing(_context: _Context) -> None:
    pass


def _local_record(context: _Context) -> None:
    context.records.append(LOCAL)


def _fetch_fails(context: _Context) -> None:
    run_git(context.checkout, "remote", "set-url", "origin", str(context.tmp_path / "gone.git"))


def _fetch_works(context: _Context) -> None:
    run_git(context.checkout, "remote", "set-url", "origin", str(context.remote))


def _disk_short(context: _Context) -> None:
    context.disk.free[context.settings.checkout.parent] = ENOUGH - 1


def _disk_room(context: _Context) -> None:
    context.disk.free[context.settings.checkout.parent] = ENOUGH


def _definition_invalid(context: _Context) -> None:
    _local_record(context)
    broken = PIPELINE_YAML.replace('contract: "1.0"\n', "")
    context.human.push_file("main", "factory/pipeline.yml", broken)


def _agent_invalid(context: _Context) -> None:
    _local_record(context)
    write_agent(context.agent_home, "coder", COLOURED_AGENT_FILE)


def _restore_fails(context: _Context) -> None:
    _local_record(context)
    locked = context.checkout / "locked"
    locked.mkdir()
    (locked / "file.txt").write_text("cannot be removed\n", encoding="utf-8")
    locked.chmod(0o555)


def _unlock(context: _Context) -> None:
    locked = context.checkout / "locked"
    if locked.exists():
        locked.chmod(0o755)


@pytest.mark.parametrize(
    "steps",
    [
        pytest.param(
            [(_local_record, [("raised", "main_branch_failing")])], id="local-record-published"
        ),
        pytest.param(
            [
                (_fetch_fails, None),
                (_fetch_works, [("raised", "fetch_failed"), ("cleared", "fetch_failed")]),
            ],
            id="fetch-failed",
        ),
        pytest.param(
            [
                (_disk_short, None),
                (_disk_room, [("raised", "disk_low"), ("cleared", "disk_low")]),
            ],
            id="disk-low",
        ),
        pytest.param([(_definition_invalid, None)], id="pipeline-definition-invalid"),
        pytest.param([(_agent_invalid, None)], id="agent-definition-invalid"),
        pytest.param(
            [(_restore_fails, None)],
            id="checkout-restore-failed",
            marks=pytest.mark.skipif(ROOT, reason="root removes files in unwritable directories"),
        ),
    ],
)
def test_a_tick_publishes_the_records_only_once_it_got_past_the_restore(
    boundaries: Boundaries, context: _Context, steps: list[tuple[Step, Expected]]
) -> None:
    wired = replace(
        boundaries, stop_records=context.records, settings=context.settings, disk=context.disk
    )
    tick = Tick(wired, INSTANCE, _handlers)

    for prepare, expected in steps:
        prepare(context)
        head = remote_commit(context.remote, "main")
        try:
            tick.run()
        finally:
            _unlock(context)
        if expected is None:
            assert remote_commit(context.remote, "main") == head
        else:
            assert _remote_pairs(context.remote) == expected


class _UnresolvableMainForStopRecords(GitCli):
    """Real git, except that `origin/main` is gone while the stop records file is read."""

    def __init__(self, directory: Path) -> None:
        super().__init__(directory, GitOptions(identity=TEST_IDENTITY))
        self._checkout = directory

    @override
    def show_file(self, ref: str, path: str) -> str | None:
        if path != STOP_RECORDS_FILE:
            return super().show_file(ref, path)
        commit = self.resolve("origin/main")
        assert commit is not None
        run_git(self._checkout, "update-ref", "-d", "refs/remotes/origin/main")
        try:
            return super().show_file(ref, path)
        finally:
            run_git(self._checkout, "update-ref", "refs/remotes/origin/main", commit)


def _refuse_main(context: _Context, boundaries: Boundaries) -> Boundaries:
    hook = context.remote / "hooks" / "pre-receive"
    hook.write_text(
        "#!/bin/sh\nwhile read old new ref; do\n"
        '  [ "$ref" = refs/heads/main ] && exit 1\ndone\nexit 0\n',
        encoding="utf-8",
    )
    hook.chmod(0o755)
    return boundaries


def _folder_in_place(context: _Context, boundaries: Boundaries) -> Boundaries:
    context.human.push_file("main", f"{STOP_RECORDS_FILE}/placeholder.txt", "a folder\n")
    return boundaries


def _main_unresolvable(context: _Context, boundaries: Boundaries) -> Boundaries:
    return replace(boundaries, git=_UnresolvableMainForStopRecords(context.checkout))


@pytest.mark.parametrize(
    "fault",
    [
        pytest.param(_refuse_main, id="push-refused"),
        pytest.param(_folder_in_place, id="write-fails"),
        pytest.param(_main_unresolvable, id="git-error"),
    ],
)
def test_a_failed_publish_is_logged_and_the_tick_goes_on(
    boundaries: Boundaries,
    context: _Context,
    tmp_path: Path,
    fault: Callable[[_Context, Boundaries], Boundaries],
) -> None:
    context.records.append(LOCAL)
    wired = fault(context, replace(boundaries, stop_records=context.records))

    outcome = Tick(wired, INSTANCE, _handlers).run()

    lines = [line.split(" ", 1)[1] for line in log_lines(tmp_path)]
    assert any(line.startswith("cannot publish the stop records: ") for line in lines)
    assert context.records.read() == [LOCAL]
    assert outcome.stopped is None
    assert outcome.event is not None
    assert outcome.dispatch is not None
