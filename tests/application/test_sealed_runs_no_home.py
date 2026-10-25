"""A sealed run and a sealed project command reset no home, and keep their seal."""

from collections.abc import Callable
from datetime import timedelta
from pathlib import Path
from typing import override

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.project_commands import ProjectCommands
from factory.application.sealed_runs import SealedProjectCommands, run_sealed
from factory.domain.checks import CheckResult
from recording_log import RecordingLog
from sealed_run_support import COMPLETED, run_request

LIMIT = timedelta(minutes=1)
PASSED = CheckResult(
    command="lint",
    status="passed",
    exit_status=0,
    duration=timedelta(seconds=3),
    last_line="lint: green",
    output_tail="lint: green\n",
)

Act = Callable[[Boundaries, FakeAgentRuntime, Path], None]


class RecordingCommands(ProjectCommands):
    """Records each command it is asked to run and passes it."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, timedelta]] = []

    @override
    def run(self, command: str, *, time_limit: timedelta) -> CheckResult:
        self.calls.append((command, time_limit))
        return PASSED


def _agent_run(boundaries: Boundaries, agent_runtime: FakeAgentRuntime, home: Path) -> None:
    agent_runtime.queue(ScriptedRun(result=COMPLETED))
    request = run_request(boundaries.checkout).model_copy(
        update={"environment": {"HOME": str(home)}}
    )
    run_sealed(boundaries, request)


def _project_command(boundaries: Boundaries, agent_runtime: FakeAgentRuntime, home: Path) -> None:
    del agent_runtime, home
    inner = RecordingCommands()
    SealedProjectCommands(inner, boundaries.git, RecordingLog()).run("lint", time_limit=LIMIT)
    assert inner.calls == [("lint", LIMIT)]


@pytest.mark.parametrize(
    "act",
    [
        pytest.param(_agent_run, id="agent-run"),
        pytest.param(_project_command, id="project-command"),
    ],
)
def test_a_sealed_run_leaves_the_home_alone_and_keeps_the_seal(
    boundaries: Boundaries, agent_runtime: FakeAgentRuntime, tmp_path: Path, *, act: Act
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    kept = home / "kept.txt"
    kept.write_text("mine\n", encoding="utf-8")

    act(boundaries, agent_runtime, home)

    assert kept.read_text(encoding="utf-8") == "mine\n"
    boundaries.git.check_seal()
