"""Every agent run is sealed: `.git` is sealed before the run and checked right after it."""

import shutil
import stat
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.git_cli import GitCli
from factory.adapters.preflight_stamp_file import JsonPreflightStampFile
from factory.application.agent_runtime import AgentRuntime
from factory.application.boundaries import Boundaries
from factory.application.opening import WorkItemOpening
from factory.application.preflight import MachineChecks, Preflight, agent_run_probe_item
from factory.application.sealed_runs import run_sealed
from factory.application.stage import StageLauncher
from factory.application.stops import StopService
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult
from factory.domain.errors import AgentRuntimeError, RepositoryUnsealed
from factory.domain.settings import InstanceSettings
from git_support import PIPELINE_YAML, install_agents
from human_clone import HumanClone
from sealed_run_support import COMPLETED, leave, run_request
from stage_run_support import ENVIRONMENT, INSTANCE

MOVED = ".git-moved"
OPEN_FOLDER = 0o2775
OPEN_FILE = 0o666
IMAGE = "build-7"
WORK_ITEM = "F0001-S0001"
BACKLOG_PATH = "factory/features/F0001-example/backlog/F0001-S0001-first.md"
PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
STORY = """\
# First story

## Description

Text.

## Interface

None.

## Acceptance criteria

1. It works.
2. make check stays green.
3. docs: none, nothing changes.

## Smoke test

```bash
true
```
Expect: nothing.

## Journal
"""

Swap = Callable[[Path], None]


def _move_away(checkout: Path) -> Path:
    moved = checkout / MOVED
    if moved.exists():
        shutil.rmtree(moved)
    (checkout / ".git").rename(moved)
    return moved


def _swap_for_folder(checkout: Path) -> None:
    moved = _move_away(checkout)
    folder = checkout / ".git"
    shutil.copytree(moved, folder, symlinks=True)
    folder.chmod(OPEN_FOLDER)


def _swap_for_link(checkout: Path) -> None:
    moved = _move_away(checkout)
    (checkout / ".git").symlink_to(moved, target_is_directory=True)


def _remove(checkout: Path) -> None:
    _move_away(checkout)


class SwappingRuntime(AgentRuntime):
    """Does `swap` to the checkout during the run, then lets the fake play the request."""

    def __init__(self, delegate: FakeAgentRuntime, checkout: Path, swap: Swap) -> None:
        self._delegate = delegate
        self._checkout = checkout
        self._swap = swap

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        self._swap(self._checkout)
        return self._delegate.run(request)

    def version(self) -> str:
        return self._delegate.version()


class ModeRecordingRuntime(AgentRuntime):
    """Records the modes of `.git` and `.git/config` during the run, then lets the fake play."""

    def __init__(self, delegate: FakeAgentRuntime, checkout: Path) -> None:
        self._delegate = delegate
        self._checkout = checkout
        self.modes: list[tuple[int, int]] = []

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        folder = self._checkout / ".git"
        self.modes.append(
            (
                stat.S_IMODE(folder.lstat().st_mode),
                stat.S_IMODE((folder / "config").lstat().st_mode),
            )
        )
        return self._delegate.run(request)

    def version(self) -> str:
        return self._delegate.version()


def test_the_run_sees_a_sealed_git_folder_and_its_result_is_returned(
    boundaries: Boundaries, agent_runtime: FakeAgentRuntime
) -> None:
    folder = boundaries.checkout / ".git"
    folder.chmod(OPEN_FOLDER)
    (folder / "config").chmod(OPEN_FILE)
    agent_runtime.queue(ScriptedRun(result=COMPLETED))
    runtime = ModeRecordingRuntime(agent_runtime, boundaries.checkout)
    recording = replace(boundaries, agent_runtime=runtime)

    result = run_sealed(recording, run_request(boundaries.checkout)).result

    assert runtime.modes == [(0o2755, 0o644)]
    assert result == COMPLETED


@pytest.mark.parametrize(
    ("before", "swap", "queued", "expected", "context", "requested"),
    [
        pytest.param(
            leave,
            _swap_for_folder,
            True,
            RepositoryUnsealed,
            None,
            True,
            id="folder-in-place",
        ),
        pytest.param(
            leave, _swap_for_link, True, RepositoryUnsealed, None, True, id="link-in-place"
        ),
        pytest.param(
            leave,
            _swap_for_folder,
            False,
            RepositoryUnsealed,
            AgentRuntimeError,
            True,
            id="swap-then-runtime-error",
        ),
        pytest.param(
            _remove, leave, True, RepositoryUnsealed, None, False, id="missing-before-the-run"
        ),
        pytest.param(
            leave, leave, False, AgentRuntimeError, None, True, id="runtime-error-git-alone"
        ),
    ],
)
def test_a_run_raises_unless_git_is_sealed_before_and_after_it(
    boundaries: Boundaries,
    agent_runtime: FakeAgentRuntime,
    *,
    before: Swap,
    swap: Swap,
    queued: bool,
    expected: type[Exception],
    context: type[Exception] | None,
    requested: bool,
) -> None:
    if queued:
        agent_runtime.queue(ScriptedRun(result=COMPLETED))
    runtime = SwappingRuntime(agent_runtime, boundaries.checkout, swap)
    swapping = replace(boundaries, agent_runtime=runtime)
    before(boundaries.checkout)

    with pytest.raises(Exception) as raised:
        run_sealed(swapping, run_request(boundaries.checkout))

    assert type(raised.value) is expected
    if context is None:
        assert not isinstance(raised.value.__context__, AgentRuntimeError)
    else:
        assert isinstance(raised.value.__context__, context)
    assert (len(agent_runtime.requests()) == 1) == requested


def test_launch_raises_when_the_run_swaps_git(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    checkout: GitCli,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
) -> None:
    install_agents(agent_home, ["intake", "tester", "coder"])
    human.push_file("main", BACKLOG_PATH, STORY)
    human.start(BACKLOG_PATH)
    checkout.fetch()
    definition = boundaries.pipeline_reader.parse(PIPELINE_YAML)
    prepared = WorkItemOpening(boundaries, definition).prepare(WORK_ITEM, PATH)
    agent_runtime.queue(ScriptedRun(result=COMPLETED))
    runtime = SwappingRuntime(agent_runtime, boundaries.checkout, _swap_for_folder)
    launcher = StageLauncher(
        replace(boundaries, agent_runtime=runtime), INSTANCE, definition, ENVIRONMENT
    )

    with pytest.raises(RepositoryUnsealed):
        launcher.launch(prepared)

    assert len(agent_runtime.requests()) == 1


def test_the_probe_raises_when_the_run_swaps_git_and_the_preflight_lets_it_out(
    boundaries: Boundaries,
    *,
    agent_runtime: FakeAgentRuntime,
    agent_home: Path,
    tmp_path: Path,
) -> None:
    install_agents(agent_home, ["intake", "coder", "reviewer"])
    settings = InstanceSettings(
        repository_url="/srv/project.git",
        instance=INSTANCE,
        state_directory=tmp_path / "state",
        agent_home=agent_home,
        pinned_agent_version="fake",
        agent_user="agent",
    )
    agent_runtime.queue(ScriptedRun(result=COMPLETED))
    agent_runtime.queue(ScriptedRun(result=COMPLETED))
    runtime = SwappingRuntime(agent_runtime, boundaries.checkout, _swap_for_folder)
    swapping = replace(boundaries, agent_runtime=runtime)

    with pytest.raises(RepositoryUnsealed):
        agent_run_probe_item(swapping, settings, ENVIRONMENT)

    extra = [lambda: agent_run_probe_item(swapping, settings, ENVIRONMENT)]
    checks = MachineChecks(swapping, settings, lambda name: f"/usr/bin/{name}", extra)
    stamps = JsonPreflightStampFile(tmp_path / "state" / "preflight-stamp.json")
    preflight = Preflight(swapping, checks, stamps, StopService(swapping), IMAGE)

    with pytest.raises(RepositoryUnsealed):
        preflight.run()
