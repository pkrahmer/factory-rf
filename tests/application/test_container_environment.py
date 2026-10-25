"""The container environment: the sync container prepares the dataset; the agent runs unsealed."""

import stat
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import override

import pytest

from container_support import (
    FIVE_MINUTES,
    GONE,
    SYNC_MARKER,
    Dataset,
    container_dataset,
    container_environment,
    dataset_git,
    local_branches,
    push_main,
    sync_makefile,
)
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.containers import ContainerRuns
from factory.application.stage_environment import ContainerEnvironment
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult
from factory.domain.containers import ContainerLaunch, ContainerResult, Mount
from factory.domain.errors import ContainerError, SnapshotError
from factory.domain.git import CommitId
from git_support import AGENT_FILE, install_agents, run_git, write_agent, write_files
from human_clone import HumanClone
from sealed_run_support import COMPLETED, run_request
from undo_support import BRANCH, start_stage

AGENT = "tester"
CHANGED_AGENT_FILE = AGENT_FILE.replace("Do the work.", "Do the work again.")
STRAY = "stray.txt"


@pytest.fixture
def main_commit(boundaries: Boundaries, human: HumanClone, agent_home: Path) -> CommitId:
    """Push the sync Makefile to `main`, give the host the work item's branch, install an agent."""
    commit = push_main(boundaries, human, {"Makefile": sync_makefile()})
    run_git(boundaries.checkout, "branch", BRANCH)
    install_agents(agent_home, [AGENT])
    return commit


def test_prepare_syncs_the_dataset_to_the_commit_and_moves_the_base(
    dataset: Dataset, main_commit: CommitId, agent_home: Path
) -> None:
    container_environment(dataset).prepare(main_commit, "main", sync_time_limit=FIVE_MINUTES)

    assert dataset_git(dataset, "rev-parse", "HEAD").strip() == main_commit
    assert dataset_git(dataset, "symbolic-ref", "--short", "HEAD").strip() == "main"
    assert {"main", BRANCH} <= set(local_branches(dataset))
    assert (dataset.workspace / "checkout" / SYNC_MARKER).is_file()
    copied = dataset.workspace / "home" / ".claude" / "agents" / f"{AGENT}.md"
    assert copied.read_text(encoding="utf-8") == (agent_home / "agents" / f"{AGENT}.md").read_text(
        encoding="utf-8"
    )
    assert dataset.snapshots.changed_paths() == []


def test_the_sync_container_gets_container_paths_mounts_environment_and_limit(
    dataset: Dataset, main_commit: CommitId
) -> None:
    boundaries = dataset.boundaries

    container_environment(dataset).prepare(main_commit, "main", sync_time_limit=FIVE_MINUTES)

    [call] = dataset.containers.calls
    assert call.command[:2] == ["/bin/sh", "-c"]
    script = call.command[2]
    assert call.command[3:] == [
        "factory-sync",
        "/work/checkout",
        "/work/home",
        "/upstream",
        "/etc/factory/claude",
        "main",
        main_commit,
    ]
    for path in ("/work", "/upstream", "/etc/factory"):
        assert path not in script
    assert call.mounts == [
        Mount(source=boundaries.checkout / ".git", target="/upstream", read_only=True),
        Mount(source=boundaries.settings.agent_home, target="/etc/factory/claude", read_only=True),
    ]
    assert call.environment == {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/work/home"}
    assert call.time_limit == FIVE_MINUTES
    assert call.working_directory == "/work"


def test_a_second_prepare_reuses_the_repository_and_resets_everything_else(
    dataset: Dataset,
    boundaries: Boundaries,
    human: HumanClone,
    agent_home: Path,
    main_commit: CommitId,
) -> None:
    run_git(boundaries.checkout, "branch", GONE)
    write_agent(agent_home, "extra", AGENT_FILE)
    environment = container_environment(dataset)
    environment.prepare(main_commit, "main", sync_time_limit=FIVE_MINUTES)
    assert GONE in local_branches(dataset)
    write_files(dataset.workspace / "checkout", {STRAY: "left\n"})
    write_files(dataset.workspace / "home", {STRAY: "left\n"})
    run_git(boundaries.checkout, "branch", "-D", GONE)
    write_agent(agent_home, AGENT, CHANGED_AGENT_FILE)
    (agent_home / "agents" / "extra.md").unlink()
    start = start_stage(boundaries, human, write_paths=["src/*", "{work_item}"])

    environment.prepare(start.commit, BRANCH, sync_time_limit=FIVE_MINUTES)

    dataset_git(dataset, "cat-file", "-e", main_commit)
    assert len(dataset.containers.calls) == 2
    assert dataset_git(dataset, "rev-parse", "HEAD").strip() == start.commit
    assert dataset_git(dataset, "symbolic-ref", "--short", "HEAD").strip() == BRANCH
    assert GONE not in local_branches(dataset)
    assert not (dataset.workspace / "checkout" / STRAY).exists()
    assert not (dataset.workspace / "home" / STRAY).exists()
    agents = dataset.workspace / "home" / ".claude" / "agents"
    assert (agents / f"{AGENT}.md").read_text(encoding="utf-8") == CHANGED_AGENT_FILE
    assert not (agents / "extra.md").exists()


class ResultContainerRuns(ContainerRuns):
    """Container runs that run nothing and return one result for every run."""

    def __init__(self, result: ContainerResult) -> None:
        """Return `result` for every run."""
        self._result = result

    @override
    def launch(
        self,
        command: Sequence[str],
        *,
        mounts: Sequence[Mount],
        environment: Mapping[str, str],
        time_limit: timedelta,
        working_directory: str,
    ) -> ContainerLaunch:
        """Refuse: the sync is run, never launched."""
        raise AssertionError("the sync container is run, never launched")

    @override
    def run(
        self,
        command: Sequence[str],
        *,
        mounts: Sequence[Mount],
        environment: Mapping[str, str],
        time_limit: timedelta,
        working_directory: str,
    ) -> ContainerResult:
        """The one result."""
        return self._result


@dataclass(frozen=True)
class Fault:
    """One way `prepare` fails and what it must raise."""

    error: type[Exception]
    detail: str | None
    recipe: str | None = None
    with_base: bool = True
    commit: str | None = None
    result: ContainerResult | None = None
    time_limit: timedelta = FIVE_MINUTES
    base_kept: bool = False
    bounded: bool = False


def _result(status: int, output: str) -> ContainerResult:
    return ContainerResult(
        exit_status=status, output=output, timed_out=False, duration=timedelta(seconds=1)
    )


@pytest.mark.parametrize(
    "fault",
    [
        pytest.param(
            Fault(ContainerError, "boom", recipe="@echo boom; exit 1", base_kept=True),
            id="sync-fails",
        ),
        pytest.param(
            Fault(
                ContainerError,
                "no end within 2 s",
                recipe="@sleep 30",
                time_limit=timedelta(seconds=1.5),
                bounded=True,
            ),
            id="sync-times-out",
        ),
        pytest.param(Fault(SnapshotError, None, with_base=False), id="no-base"),
        pytest.param(Fault(ContainerError, None, commit="a" * 40), id="no-such-commit"),
        pytest.param(
            Fault(ContainerError, "exit status 3", result=_result(3, "\n")), id="blank-output"
        ),
        pytest.param(
            Fault(
                ContainerError,
                "exit status 2",
                result=_result(2, "make: *** [Makefile:3: sync] Error 2\n"),
            ),
            id="make-messages-only",
        ),
    ],
)
def test_a_failed_prepare_raises_and_leaves_the_base(
    boundaries: Boundaries,
    human: HumanClone,
    agent_home: Path,
    tmp_path: Path,
    *,
    fault: Fault,
) -> None:
    commit = push_main(boundaries, human, {"Makefile": sync_makefile(fault.recipe or "@true")})
    install_agents(agent_home, [AGENT])
    dataset = container_dataset(boundaries, tmp_path, with_base=fault.with_base)
    containers = dataset.containers if fault.result is None else ResultContainerRuns(fault.result)
    environment = ContainerEnvironment(dataset.boundaries, dataset.snapshots, containers)

    began = time.monotonic()
    with pytest.raises(fault.error) as raised:
        environment.prepare(fault.commit or commit, "main", sync_time_limit=fault.time_limit)
    elapsed = time.monotonic() - began

    error = raised.value
    if isinstance(error, ContainerError):
        assert error.command == "sync"
        if fault.detail is None:
            assert error.detail
        else:
            assert error.detail == fault.detail
    if not fault.with_base:
        assert dataset.containers.calls == []
    if fault.base_kept:
        assert dataset.snapshots.changed_paths() != []
        dataset.snapshots.reset()
        assert list(dataset.workspace.iterdir()) == []
    if fault.bounded:
        assert 1 <= elapsed < 25


@pytest.mark.parametrize(
    ("limit", "detail"),
    [
        pytest.param(timedelta(seconds=1.2), "no end within 2 s", id="fraction-rounds-up"),
        pytest.param(timedelta(seconds=3), "no end within 3 s", id="whole-stays"),
    ],
)
def test_the_timeouts_seconds_are_rounded_up(
    dataset: Dataset, *, limit: timedelta, detail: str
) -> None:
    timed_out = ContainerResult(exit_status=None, output="", timed_out=True, duration=limit)
    environment = ContainerEnvironment(
        dataset.boundaries, dataset.snapshots, ResultContainerRuns(timed_out)
    )

    with pytest.raises(ContainerError) as raised:
        environment.prepare("a" * 40, "main", sync_time_limit=limit)

    assert (raised.value.command, raised.value.detail) == ("sync", detail)


def _git_modes(checkout: Path) -> tuple[int, int]:
    folder = checkout / ".git"
    return stat.S_IMODE(folder.stat().st_mode), stat.S_IMODE((folder / "config").stat().st_mode)


class RecordingRun:
    """A run of the test: records each request and returns the completed result."""

    def __init__(self) -> None:
        """Start with no request."""
        self.requests: list[AgentRunRequest] = []

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        """Record `request`."""
        self.requests.append(request)
        return COMPLETED


@pytest.mark.parametrize("given", [False, True], ids=["runtime", "given-run"])
def test_run_agent_runs_unsealed_through_the_runtime_or_the_given_run(
    dataset: Dataset, agent_runtime: FakeAgentRuntime, *, given: bool
) -> None:
    checkout = dataset.boundaries.checkout
    request = run_request(checkout)
    modes = _git_modes(checkout)

    if given:
        recorder = RecordingRun()
        sealed = container_environment(dataset).run_agent(request, run=recorder.run)
        assert recorder.requests == [request]
        assert agent_runtime.requests() == []
    else:
        agent_runtime.queue(ScriptedRun(result=COMPLETED))
        sealed = container_environment(dataset).run_agent(request)
        assert agent_runtime.requests() == [request]

    assert sealed.result == COMPLETED
    assert sealed.nested_repositories == []
    assert _git_modes(checkout) == modes


def test_run_agent_leaves_nested_repositories_ignored_files_and_the_home(
    dataset: Dataset, agent_runtime: FakeAgentRuntime, agent_home: Path
) -> None:
    checkout = dataset.boundaries.checkout
    write_files(checkout, {".gitignore": "build/\n"})
    home_file = agent_home / "left-by-the-agent.txt"
    agent_runtime.queue(
        ScriptedRun(
            writes={"notes/.git/HEAD": "ref: refs/heads/main\n", "build/out.txt": "built\n"},
            result=COMPLETED,
        )
    )

    def run(request: AgentRunRequest) -> AgentRunResult:
        write_files(agent_home, {home_file.name: "the agent's\n"})
        return agent_runtime.run(request)

    sealed = container_environment(dataset).run_agent(run_request(checkout), run=run)

    assert sealed.nested_repositories == []
    assert (checkout / "notes" / ".git" / "HEAD").is_file()
    assert (checkout / "build" / "out.txt").read_text(encoding="utf-8") == "built\n"
    assert home_file.read_text(encoding="utf-8") == "the agent's\n"
