"""The agent's home is reset after the seal and before every agent run and project command."""

import stat
from collections.abc import Callable
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from typing import override

import pytest

from application.test_checkout_preparer_seal import RecordingLog
from application.test_sealed_project_commands import PASSED, ProbeCommands
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.git_cli import GitCli
from factory.application.agent_home import AgentHome
from factory.application.boundaries import Boundaries
from factory.application.sealed_runs import SealedProjectCommands, run_sealed
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult
from factory.domain.errors import AgentRuntimeError, ProjectCommandError
from sealed_run_support import COMPLETED, run_request

OPEN_FOLDER = 0o2775
LIMIT = timedelta(seconds=30)

Counter = Callable[[], int]
MakeHome = Callable[[Path, Counter], "RecordingHome | None"]


class RecordingHome(AgentHome):
    """Records, at each reset, whether `.git` was group-writable and how many calls came before.

    With `fault`, it opens `.git` again when `unseal` is set, then raises the fault.
    """

    def __init__(
        self,
        checkout: Path,
        count: Counter,
        fault: AgentRuntimeError | None = None,
        *,
        unseal: bool = False,
    ) -> None:
        self._checkout = checkout
        self._count = count
        self._fault = fault
        self._unseal = unseal
        self.resets: list[tuple[bool, int]] = []

    @override
    def reset(self) -> None:
        folder = self._checkout / ".git"
        self.resets.append((bool(folder.lstat().st_mode & stat.S_IWGRP), self._count()))
        if self._fault is None:
            return
        if self._unseal:
            folder.chmod(OPEN_FOLDER)
        raise self._fault


def _recording(checkout: Path, count: Counter) -> RecordingHome:
    return RecordingHome(checkout, count)


def _raising(checkout: Path, count: Counter) -> RecordingHome:
    # The home opens `.git` before it raises: a check of the seal after it would raise instead.
    return RecordingHome(checkout, count, AgentRuntimeError("x"), unseal=True)


def _raising_sealed(checkout: Path, count: Counter) -> RecordingHome:
    return RecordingHome(checkout, count, AgentRuntimeError("x"))


def _none(checkout: Path, count: Counter) -> None:
    del checkout, count


@pytest.fixture
def directory(checkout: GitCli, tmp_path: Path) -> Path:
    """Return the working copy of the `checkout` clone, its `.git` group-writable."""
    del checkout
    folder = tmp_path / "checkout"
    (folder / ".git").chmod(OPEN_FOLDER)
    return folder


@pytest.mark.parametrize(
    ("make_home", "raises", "resets", "requests"),
    [
        pytest.param(_recording, False, [(False, 0)], 1, id="reset-then-run"),
        pytest.param(_raising, True, [(False, 0)], 0, id="reset-raises"),
        pytest.param(_none, False, None, 1, id="no-home"),
    ],
)
def test_the_home_is_reset_after_the_seal_and_before_the_run(
    boundaries: Boundaries,
    agent_runtime: FakeAgentRuntime,
    directory: Path,
    *,
    make_home: MakeHome,
    raises: bool,
    resets: list[tuple[bool, int]] | None,
    requests: int,
) -> None:
    agent_runtime.queue(ScriptedRun(result=COMPLETED))
    home = make_home(directory, lambda: len(agent_runtime.requests()))
    with_home = replace(boundaries, agent_home=home)

    if raises:
        with pytest.raises(AgentRuntimeError) as raised:
            run_sealed(with_home, run_request(boundaries.checkout))
        assert type(raised.value) is AgentRuntimeError
        assert raised.value.detail == "x"
    else:
        assert run_sealed(with_home, run_request(boundaries.checkout)).result == COMPLETED

    if home is not None:
        assert home.resets == resets
    assert len(agent_runtime.requests()) == requests


def test_a_run_that_calls_the_runtime_twice_resets_the_home_once_before_the_first_call(
    boundaries: Boundaries, agent_runtime: FakeAgentRuntime, directory: Path
) -> None:
    agent_runtime.queue(ScriptedRun(result=COMPLETED))
    agent_runtime.queue(ScriptedRun(result=COMPLETED))
    home = RecordingHome(directory, lambda: len(agent_runtime.requests()))

    def twice(request: AgentRunRequest) -> AgentRunResult:
        agent_runtime.run(request)
        return agent_runtime.run(request)

    run_sealed(replace(boundaries, agent_home=home), run_request(boundaries.checkout), run=twice)

    assert home.resets == [(False, 0)]
    assert len(agent_runtime.requests()) == 2


@pytest.mark.parametrize(
    ("make_home", "raises", "resets", "calls"),
    [
        pytest.param(_recording, False, [(False, 0), (False, 1)], 2, id="reset-before-each"),
        pytest.param(_raising_sealed, True, [(False, 0)], 0, id="reset-raises"),
        pytest.param(_none, False, None, 2, id="no-home"),
    ],
)
def test_the_home_is_reset_after_the_seal_and_before_each_project_command(
    checkout: GitCli,
    directory: Path,
    *,
    make_home: MakeHome,
    raises: bool,
    resets: list[tuple[bool, int]] | None,
    calls: int,
) -> None:
    inner = ProbeCommands(directory, lambda _path: None, lambda _command, _limit: PASSED)
    home = make_home(directory, lambda: len(inner.calls))
    sealed = SealedProjectCommands(inner, checkout, RecordingLog(), home)

    if raises:
        with pytest.raises(ProjectCommandError) as raised:
            sealed.run("check", time_limit=LIMIT)
        assert raised.value.command == "check"
        assert raised.value.detail == "x"
    else:
        assert sealed.run("check", time_limit=LIMIT) == PASSED
        (directory / ".git").chmod(OPEN_FOLDER)
        assert sealed.run("check", time_limit=LIMIT) == PASSED

    if home is not None:
        assert home.resets == resets
    assert len(inner.calls) == calls
    assert inner.group_writable == [False] * calls
