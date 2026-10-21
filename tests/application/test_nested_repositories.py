"""A git repository the agent leaves in the work tree is removed before any git command runs."""

import os
from collections.abc import Callable, Iterator
from dataclasses import replace
from pathlib import Path

import pytest

from application.test_after_agent import (
    BRANCH,
    SwitchingRuntime,
    _completed,
    _launch,
    _note,
    _stalled,
    _started_attempts,
)
from application.test_checkout_preparer_seal import RecordingLog, _existing, _settings
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.agent_runtime import AgentRuntime
from factory.application.boundaries import Boundaries
from factory.application.preflight import agent_run_probe_item
from factory.application.scheduler import CheckoutPreparer
from factory.application.sealed_runs import run_sealed
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult
from factory.domain.errors import AgentRuntimeError, GitError, RepositoryUnsealed
from factory.domain.git import GitOptions
from factory.domain.journal import entry_text
from factory.domain.post_texts import stall_note
from factory.domain.settings import InstanceSettings
from git_support import TEST_IDENTITY, install_agents, run_git, write_fsmonitor
from human_clone import HumanClone
from root_support import AS_ROOT
from sealed_run_support import COMPLETED, run_request
from stage_run_support import pushed

NESTED = "notes/sub/.git"
LOCKED = "locked"
ENVIRONMENT = {"PATH": "/usr/local/bin:/usr/bin", "HOME": "/home/factory"}
PROBE_DETAIL = (
    "the probe run left a git repository in the work tree, which the factory removed: "
    "notes/sub/.git"
)
REMOVED_LINE = "removed nested repositories: notes/sub/.git"
TWO_NESTED = "a/.git, b/.git"

Act = Callable[[Path], None]


class NestingRuntime(AgentRuntime):
    """Does `act` to the checkout during the run, then lets the delegate play the request."""

    def __init__(self, delegate: AgentRuntime, checkout: Path, act: Act) -> None:
        self._delegate = delegate
        self._checkout = checkout
        self._act = act

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        self._act(self._checkout)
        return self._delegate.run(request)

    def version(self) -> str:
        return self._delegate.version()


@pytest.fixture
def reopen(tmp_path: Path) -> Iterator[None]:
    """Open the `locked` folders of the test's checkouts again after the test."""
    yield
    for folder in tmp_path.glob(f"*/{LOCKED}"):
        folder.chmod(0o755)


def _init(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    run_git(folder, "init", "-q")


def _nest(checkout: Path) -> None:
    _init(checkout / "notes" / "sub")


def _nest_two(checkout: Path) -> None:
    _init(checkout / "b")
    _init(checkout / "a")


def _leave(_checkout: Path) -> None:
    pass


def _nest_and_unseal(checkout: Path) -> None:
    _nest(checkout)
    (checkout / ".git").chmod(0o2775)


def _nest_locked(checkout: Path) -> None:
    _init(checkout / LOCKED)
    (checkout / LOCKED).chmod(0o555)


def _nesting(boundaries: Boundaries, act: Act, delegate: AgentRuntime) -> Boundaries:
    return replace(boundaries, agent_runtime=NestingRuntime(delegate, boundaries.checkout, act))


@pytest.mark.usefixtures("reopen")
@pytest.mark.parametrize(
    ("act", "queued", "raised", "reported", "left"),
    [
        pytest.param(_nest, True, None, [NESTED], False, id="nested-and-completed"),
        pytest.param(_leave, True, None, [], False, id="nothing-nested"),
        pytest.param(_nest, False, AgentRuntimeError, None, False, id="nested-and-run-error"),
        pytest.param(
            _nest_and_unseal, True, RepositoryUnsealed, None, True, id="nested-and-unsealed"
        ),
        pytest.param(
            _nest_locked,
            False,
            RepositoryUnsealed,
            None,
            False,
            id="run-error-and-removal-fails",
            marks=AS_ROOT,
        ),
    ],
)
def test_run_sealed_reports_and_removes_the_nested_repositories(
    boundaries: Boundaries,
    agent_runtime: FakeAgentRuntime,
    *,
    act: Act,
    queued: bool,
    raised: type[Exception] | None,
    reported: list[str] | None,
    left: bool,
) -> None:
    if queued:
        agent_runtime.queue(ScriptedRun(result=COMPLETED))
    nesting = _nesting(boundaries, act, agent_runtime)

    if raised is None:
        sealed = run_sealed(nesting, run_request(boundaries.checkout))
        assert sealed.result == COMPLETED
        assert sealed.nested_repositories == reported
    else:
        with pytest.raises(Exception) as error:
            run_sealed(nesting, run_request(boundaries.checkout))
        assert type(error.value) is raised

    assert os.path.lexists(boundaries.checkout / NESTED) == left


def _monitored_nest(marker: Path) -> Act:
    monitor = write_fsmonitor(marker.parent, marker)

    def act(checkout: Path) -> None:
        _nest(checkout)
        run_git(checkout / "notes" / "sub", "config", "core.fsmonitor", str(monitor))

    return act


@pytest.mark.parametrize("switched", [False, True], ids=["on-branch", "left-branch-too"])
def test_a_stage_whose_agent_leaves_a_nested_repository_stalls(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    hosting: FakeHostingService,
    tmp_path: Path,
    switched: bool,
) -> None:
    marker = tmp_path / "fsmonitor-ran"
    marker.write_text("", encoding="utf-8")
    delegate: AgentRuntime = (
        SwitchingRuntime(
            agent_runtime, remote=remote, branch=BRANCH, hosting=hosting, checkout=boundaries.git
        )
        if switched
        else agent_runtime
    )
    launched = _launch(
        _nesting(boundaries, _monitored_nest(marker), delegate),
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        run=ScriptedRun(result=_completed("doing")),
    )

    assert launched.nested_repositories == [NESTED]
    assert not os.path.lexists(boundaries.checkout / NESTED)

    stalled = _stalled(boundaries, launched)

    assert stalled.reason == "nested_repository"
    assert stalled.attempts == _started_attempts(launched) + 1
    if not switched:
        assert stall_note("nested_repository", 1, stalled.attempts_cap, detail=NESTED) in _note(
            hosting, stalled
        )
        document = pushed(boundaries, remote)
        state = document.state
        assert state is not None
        assert (state.journal[-1].speaker, state.journal[-1].kind) == ("factory", "stall")
        assert NESTED in entry_text(document, state.journal[-1].number)
    assert marker.read_text(encoding="utf-8") == ""


def test_a_stage_whose_agent_leaves_two_repositories_names_both_in_the_stall_note(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    hosting: FakeHostingService,
) -> None:
    launched = _launch(
        _nesting(boundaries, _nest_two, agent_runtime),
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        run=ScriptedRun(result=_completed("doing")),
    )

    stalled = _stalled(boundaries, launched)

    assert stalled.reason == "nested_repository"
    assert f"which the factory removed: {TWO_NESTED}" in _note(hosting, stalled)


def _probe_settings(tmp_path: Path, agent_home: Path) -> InstanceSettings:
    return InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        state_directory=tmp_path / "state",
        agent_home=agent_home,
        pinned_agent_version="fake",
        agent_user="agent",
    )


@pytest.mark.parametrize(
    ("act", "result", "detail"),
    [
        pytest.param(_nest, COMPLETED, PROBE_DETAIL, id="nested-and-completed"),
        pytest.param(_leave, COMPLETED, None, id="nothing-nested"),
        pytest.param(
            _nest_two,
            COMPLETED,
            "the probe run left a git repository in the work tree, which the factory removed: "
            + TWO_NESTED,
            id="two-nested",
        ),
        pytest.param(
            _nest,
            AgentRunResult(end_reason="died", duration=COMPLETED.duration),
            PROBE_DETAIL,
            id="nested-and-died",
        ),
    ],
)
def test_a_probe_run_that_leaves_a_nested_repository_fails_the_item(
    boundaries: Boundaries,
    *,
    agent_runtime: FakeAgentRuntime,
    agent_home: Path,
    tmp_path: Path,
    act: Act,
    result: AgentRunResult,
    detail: str | None,
) -> None:
    install_agents(agent_home, ["intake", "coder", "reviewer"])
    agent_runtime.queue(ScriptedRun(result=result))

    item = agent_run_probe_item(
        _nesting(boundaries, act, agent_runtime), _probe_settings(tmp_path, agent_home), ENVIRONMENT
    )

    assert item.passed == (detail is None)
    if detail is not None:
        assert item.detail == detail
    assert not os.path.lexists(boundaries.checkout / NESTED)


class RecordingGit(GitCli):
    """The factory's git, counting its calls of `remove_nested_repositories`."""

    def __init__(self, directory: Path) -> None:
        super().__init__(directory, GitOptions(identity=TEST_IDENTITY))
        self.searches = 0

    def remove_nested_repositories(self) -> list[str]:
        self.searches += 1
        return super().remove_nested_repositories()


@pytest.fixture
def directory(tmp_path: Path) -> Path:
    """Return the instance's checkout folder, `tmp_path / "instance"`; nothing is created."""
    return tmp_path / "instance"


@pytest.mark.parametrize(
    ("act", "logged", "lines"),
    [
        pytest.param(_nest, True, [REMOVED_LINE], id="nested"),
        pytest.param(_nest, False, [], id="nested-without-log"),
        pytest.param(_leave, True, [], id="nothing-nested"),
        pytest.param(
            _nest_two, True, [f"removed nested repositories: {TWO_NESTED}"], id="two-nested"
        ),
    ],
)
def test_the_preparer_removes_the_nested_repositories_of_a_kept_checkout(
    remote: Path, directory: Path, act: Act, logged: bool, lines: list[str]
) -> None:
    added = _existing(remote, directory)
    act(directory)
    log = RecordingLog()
    git = GitCli(directory, GitOptions(identity=TEST_IDENTITY))
    settings = _settings(remote, directory)
    preparer = (
        CheckoutPreparer(git, settings, log=log) if logged else CheckoutPreparer(git, settings)
    )

    preparer.prepare()

    assert added.read_text(encoding="utf-8") == "put there by the test\n"
    assert not os.path.lexists(directory / NESTED)
    assert log.lines == lines


@AS_ROOT
@pytest.mark.usefixtures("reopen")
def test_a_nested_repository_the_preparer_cannot_remove_makes_it_clone_again(
    remote: Path, directory: Path
) -> None:
    _existing(remote, directory)
    _nest_locked(directory)
    git = GitCli(directory, GitOptions(identity=TEST_IDENTITY))
    log = RecordingLog()

    with pytest.raises(GitError) as raised:
        CheckoutPreparer(git, _settings(remote, directory), log=log).prepare()

    assert "discard" in str(raised.value)
    [line] = log.lines
    nested = directory / LOCKED / ".git"
    assert line.startswith(f"cloning the checkout again: seal failed (no exit status): {nested}: ")


def test_a_missing_checkout_is_cloned_without_a_search(remote: Path, directory: Path) -> None:
    git = RecordingGit(directory)

    CheckoutPreparer(git, _settings(remote, directory)).prepare()

    assert git.resolve("origin/main") is not None
    assert git.searches == 0
