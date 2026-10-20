"""A sealed run removes the git-ignored paths it left, only when the run returned."""

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.git_cli import GitCli
from factory.application.agent_runtime import AgentRuntime
from factory.application.boundaries import Boundaries
from factory.application.sealed_runs import run_sealed
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult
from factory.domain.errors import AgentRuntimeError, GitError
from git_support import CLEAN_IGNORED, run_git, write_files
from human_clone import HumanClone
from root_support import AS_ROOT
from sealed_run_support import COMPLETED, run_request

STANDIN = "standin\n"
WRITES = {
    ".venv/lib/standin.pth": STANDIN,
    "src/__pycache__/a.cpython-312.pyc": STANDIN,
    "tests/hidden/.gitignore": "*\n",
    "tests/hidden/conftest.py": STANDIN,
    "src/new.py": "y = 2\n",
}
IGNORED = [path for path in WRITES if path != "src/new.py"]

Then = Callable[[Path], None]


class ThenRuntime(AgentRuntime):
    """Lets the fake play the request, then does `then` to the checkout before it returns."""

    def __init__(self, delegate: FakeAgentRuntime, checkout: Path, then: Then) -> None:
        self._delegate = delegate
        self._checkout = checkout
        self._then = then

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        result = self._delegate.run(request)
        self._then(self._checkout)
        return result

    def version(self) -> str:
        return self._delegate.version()


def _nothing(checkout: Path) -> None:
    del checkout


def _nested_repository(checkout: Path) -> None:
    dependency = checkout / ".venv" / "dep"
    dependency.mkdir(parents=True)
    run_git(dependency, "init", "-q")


def _boom(checkout: Path) -> None:
    del checkout
    raise AgentRuntimeError("boom")


def _locked(checkout: Path) -> None:
    locked = checkout / ".venv" / "locked"
    write_files(locked, {"x": STANDIN})
    locked.chmod(0o555)


@pytest.fixture
def ignoring(boundaries: Boundaries, human: HumanClone, checkout: GitCli) -> Boundaries:
    """The boundaries on a checkout whose `main` holds the `.gitignore`."""
    human.push_file("main", ".gitignore", ".venv/\n__pycache__/\n*.pyc\n")
    checkout.fetch()
    checkout.reset_to("origin/main")
    return boundaries


@pytest.mark.parametrize(
    ("then", "raised", "nested", "present", "gone"),
    [
        pytest.param(_nothing, None, [], ["src/new.py"], IGNORED, id="returned"),
        pytest.param(
            _nested_repository,
            None,
            [".venv/dep/.git"],
            ["src/new.py"],
            [*IGNORED, ".venv"],
            id="nested-repository",
        ),
        pytest.param(
            _boom,
            AgentRuntimeError,
            [],
            [".venv/lib/standin.pth", "tests/hidden/conftest.py"],
            [],
            id="raised",
        ),
        pytest.param(_locked, GitError, [], [], [], id="unremovable", marks=AS_ROOT),
    ],
)
def test_a_returned_run_leaves_no_ignored_path_and_a_raised_one_leaves_them(
    ignoring: Boundaries,
    agent_runtime: FakeAgentRuntime,
    *,
    then: Then,
    raised: type[Exception] | None,
    nested: list[str],
    present: list[str],
    gone: list[str],
) -> None:
    checkout = ignoring.checkout
    agent_runtime.queue(ScriptedRun(writes=WRITES, result=COMPLETED))
    runtime = ThenRuntime(agent_runtime, checkout, then)
    sealed_boundaries = replace(ignoring, agent_runtime=runtime)

    try:
        if raised is None:
            sealed = run_sealed(sealed_boundaries, run_request(checkout))
            assert sealed.result == COMPLETED
            assert sealed.nested_repositories == nested
        else:
            with pytest.raises(Exception) as error:
                run_sealed(sealed_boundaries, run_request(checkout))
            assert type(error.value) is raised
            if isinstance(error.value, GitError):
                assert error.value.command == CLEAN_IGNORED
            else:
                assert isinstance(error.value, AgentRuntimeError)
                assert error.value.detail == "boom"
    finally:
        locked = checkout / ".venv" / "locked"
        if locked.exists():
            locked.chmod(0o755)

    for path in present:
        assert (checkout / path).exists(), path
    for path in gone:
        assert not (checkout / path).exists(), path
