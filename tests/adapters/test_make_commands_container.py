"""The make class in a check container: the reset, the copy of the host's changes, real make."""

import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.fake_containers import FakeContainerRuns
from factory.adapters.fake_snapshots import FakeSnapshots
from factory.adapters.git_cli import GitCli
from factory.adapters.make_commands import ContainerMakeCommands
from factory.application.containers import ContainerRuns
from factory.application.git import Git
from factory.application.project_commands import ProjectCommands
from factory.domain.checks import TargetTime
from factory.domain.containers import ContainerLaunch, ContainerResult, Mount
from factory.domain.errors import ContainerError, GitError, ProjectCommandError
from factory.domain.git import ChangedPath, GitOptions
from git_support import TEST_IDENTITY, commit_all, write_files

LIMIT = timedelta(minutes=1)
CHECK_MARKER = ".checked"
HOST_FILES = {
    ".gitignore": ".venv/\n",
    "src/kept.py": "kept = 1\n",
    "src/old.py": "old = 1\n",
}
# Every file of the dataset's checkout but its `.git`, one per line, sorted.
LISTING = "@find . -path ./.git -prune -o -type f -print | LC_ALL=C sort"
BASE_LISTING = ["./.gitignore", "./Makefile", "./src/kept.py", "./src/old.py"]
GIT_MARKER = "marker"
HOME_FILE = "home/kept.txt"


def makefile(**recipes: str) -> str:
    """A Makefile with one phony target per keyword, each running its recipe lines."""
    targets = "".join(
        f"{name}:\n" + "".join(f"\t{line}\n" for line in body.splitlines())
        for name, body in recipes.items()
    )
    return f".PHONY: {' '.join(recipes)}\n\n{targets}"


@dataclass(frozen=True)
class Setup:
    """The host's clone, the dataset's folder and base, and the fakes on them."""

    host: GitCli
    host_directory: Path
    workspace: Path
    base: Path
    snapshots: FakeSnapshots
    containers: FakeContainerRuns

    @property
    def dataset_checkout(self) -> Path:
        """The checkout in the dataset."""
        return self.workspace / "checkout"

    def with_base(self, makefile_text: str) -> None:
        """Make the base the host's committed files, `makefile_text`, a `.git` marker and a home."""
        base_checkout = self.base / "checkout"
        write_files(base_checkout, {**HOST_FILES, "Makefile": makefile_text})
        write_files(base_checkout / ".git", {GIT_MARKER: "the dataset's own\n"})
        write_files(self.base, {HOME_FILE: "home\n"})

    def commands(
        self, *, snapshots: FakeSnapshots | None = None, git: Git | None = None
    ) -> ContainerMakeCommands:
        """The class under test on the setup's fakes, or on the ones given."""
        return ContainerMakeCommands(
            snapshots or self.snapshots,
            self.containers,
            git or self.host,
            checkout=self.host_directory,
        )


@pytest.fixture
def setup(tmp_path: Path, checkout: GitCli) -> Setup:
    """A host clone whose `HEAD` holds `HOST_FILES`, and an empty dataset with no base yet."""
    host_directory = tmp_path / "checkout"
    write_files(host_directory, HOST_FILES)
    commit_all(host_directory, "Add the host's files")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    base = tmp_path / "base"
    return Setup(
        host=checkout,
        host_directory=host_directory,
        workspace=workspace,
        base=base,
        snapshots=FakeSnapshots(workspace, base),
        containers=FakeContainerRuns(workspace),
    )


def _write_stray(setup: Setup) -> None:
    write_files(setup.dataset_checkout, {"stray.txt": "stray\n"})


def test_check_runs_after_sync_in_the_container_and_its_files_stay_there(setup: Setup) -> None:
    setup.with_base(
        makefile(
            sync="@echo 'sync: green (0.1 s)'",
            check=f"@echo checked\n@touch {CHECK_MARKER}\n@echo 'check: green (0.2 s)'",
        )
    )
    status_before = setup.host.status()

    result = setup.commands().run("check", time_limit=LIMIT)

    assert result.command == "check"
    assert result.status == "passed"
    assert result.exit_status == 0
    assert result.last_line == "check: green (0.2 s)"
    assert result.targets == [
        TargetTime(target="sync", seconds=0.1),
        TargetTime(target="check", seconds=0.2),
    ]
    [call] = setup.containers.calls
    assert call.command == [
        "/bin/sh",
        "-c",
        '"$1" sync && "$1" --no-print-directory "$2"',
        "factory-check",
        "make",
        "check",
    ]
    assert call.mounts == []
    assert call.environment == {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/work/home"}
    assert call.time_limit == timedelta(minutes=1)
    assert call.working_directory == "/work/checkout"
    assert (setup.dataset_checkout / CHECK_MARKER).is_file()
    assert not (setup.host_directory / CHECK_MARKER).exists()
    assert setup.host.status() == status_before


def test_output_tail_is_the_last_thirty_lines(setup: Setup) -> None:
    setup.with_base(
        makefile(
            sync="@echo 'sync: green (0.1 s)'",
            check='@for i in $$(seq 1 40); do echo "line $$i"; done',
        )
    )

    result = setup.commands().run("check", time_limit=LIMIT)

    assert result.output_tail.splitlines() == [f"line {i}" for i in range(11, 41)]


def _host_unchanged(setup: Setup) -> None:
    """Nothing on the host differs from `HEAD`."""


def _stray_in_dataset(setup: Setup) -> None:
    _write_stray(setup)


def _host_adds_and_changes(setup: Setup) -> None:
    write_files(setup.host_directory, {"src/new.py": "new = 1\n", "src/kept.py": "kept = 2\n"})


def _host_deletes(setup: Setup) -> None:
    (setup.host_directory / "src/old.py").unlink()


def _host_ignored(setup: Setup) -> None:
    write_files(setup.host_directory, {".venv/x": "ignored\n"})


@pytest.mark.parametrize(
    ("prepare", "listing", "host_bytes"),
    [
        pytest.param(_stray_in_dataset, BASE_LISTING, [], id="stray-file-is-reset"),
        pytest.param(
            _host_adds_and_changes,
            sorted([*BASE_LISTING, "./src/new.py"]),
            ["src/new.py", "src/kept.py"],
            id="added-and-changed-are-copied",
        ),
        pytest.param(
            _host_deletes,
            [path for path in BASE_LISTING if path != "./src/old.py"],
            [],
            id="deleted-is-removed",
        ),
        pytest.param(_host_ignored, BASE_LISTING, [], id="ignored-is-not-copied"),
        pytest.param(_host_unchanged, BASE_LISTING, [], id="nothing-changed"),
    ],
)
def test_check_sees_the_base_with_what_differs_from_head_on_the_host(
    setup: Setup, prepare: Callable[[Setup], None], listing: list[str], host_bytes: list[str]
) -> None:
    setup.with_base(makefile(sync="@true", check=LISTING))
    prepare(setup)

    result = setup.commands().run("check", time_limit=LIMIT)

    assert result.status == "passed"
    assert result.output_tail.splitlines() == listing
    for path in host_bytes:
        host_file = setup.host_directory / path
        assert (setup.dataset_checkout / path).read_bytes() == host_file.read_bytes()


def test_failing_sync_fails_and_check_does_not_run(setup: Setup) -> None:
    setup.with_base(makefile(sync="@echo boom\n@exit 1", check=f"@touch {CHECK_MARKER}"))

    result = setup.commands().run("check", time_limit=LIMIT)

    assert result.status == "failed"
    assert result.exit_status == 2
    assert result.last_line == "boom"
    assert not (setup.dataset_checkout / CHECK_MARKER).exists()


def test_check_reaching_its_time_limit_is_a_time_limit_result(setup: Setup) -> None:
    setup.with_base(makefile(sync="@true", check="@sleep 30"))

    started = time.monotonic()
    result = setup.commands().run("check", time_limit=timedelta(seconds=1))
    elapsed = time.monotonic() - started

    assert result.status == "time_limit"
    assert result.exit_status is None
    assert 1 <= elapsed < 25


@pytest.mark.parametrize(
    ("command", "time_limit", "error", "detail"),
    [
        pytest.param("check", timedelta(0), ValueError, None, id="zero-limit"),
        pytest.param("check", timedelta(seconds=-1), ValueError, None, id="negative-limit"),
        pytest.param(
            "Check", LIMIT, ProjectCommandError, "invalid command name 'Check'", id="bad-name"
        ),
    ],
)
def test_refused_call_runs_nothing(
    setup: Setup,
    command: str,
    time_limit: timedelta,
    error: type[Exception],
    detail: str | None,
) -> None:
    setup.with_base(makefile(sync="@true", check="@true"))
    _write_stray(setup)

    with pytest.raises(error) as raised:
        setup.commands().run(command, time_limit=time_limit)

    if detail is not None:
        assert isinstance(raised.value, ProjectCommandError)
        assert raised.value.detail == detail
    assert setup.containers.calls == []
    assert (setup.dataset_checkout / "stray.txt").is_file()


class _UnstartableContainers(ContainerRuns):
    """Container runs whose container never starts."""

    def launch(
        self,
        command: Sequence[str],
        *,
        mounts: Sequence[Mount],
        environment: Mapping[str, str],
        time_limit: timedelta,
        working_directory: str,
    ) -> ContainerLaunch:
        """Refuse as `run` does."""
        del command, mounts, environment, time_limit, working_directory
        raise ContainerError("make", "[Errno 2] No such file or directory")

    def run(
        self,
        command: Sequence[str],
        *,
        mounts: Sequence[Mount],
        environment: Mapping[str, str],
        time_limit: timedelta,
        working_directory: str,
    ) -> ContainerResult:
        """Raise the error of a missing program."""
        del command, mounts, environment, time_limit, working_directory
        raise ContainerError("make", "[Errno 2] No such file or directory")


GIT_FAULT = GitError("git diff", 128, "bad revision")


class _FailingGit(GitCli):
    """The host's git, whose `changed_paths` fails."""

    def changed_paths(self, since: str) -> list[ChangedPath]:
        """Raise the shared `GIT_FAULT`."""
        del since
        raise GIT_FAULT


class _EscapingGit(GitCli):
    """The host's git, whose `changed_paths` names a path outside the tree."""

    def changed_paths(self, since: str) -> list[ChangedPath]:
        """A path that climbs out of the checkout."""
        del since
        return [ChangedPath(path="../x", change="added")]


def _git_of(setup: Setup, kind: type[GitCli]) -> GitCli:
    return kind(setup.host_directory, GitOptions(identity=TEST_IDENTITY))


def _without_base(setup: Setup) -> ContainerMakeCommands:
    snapshots = FakeSnapshots(setup.workspace, setup.workspace.parent / "no-base")
    return setup.commands(snapshots=snapshots)


def _unstartable(setup: Setup) -> ContainerMakeCommands:
    return ContainerMakeCommands(
        setup.snapshots, _UnstartableContainers(), setup.host, checkout=setup.host_directory
    )


def _failing_git(setup: Setup) -> ContainerMakeCommands:
    return setup.commands(git=_git_of(setup, _FailingGit))


def _escaping_git(setup: Setup) -> ContainerMakeCommands:
    return setup.commands(git=_git_of(setup, _EscapingGit))


def _is_snapshot_fault(error: BaseException) -> bool:
    return (
        isinstance(error, ProjectCommandError)
        and error.command == "check"
        and error.detail.startswith("snapshot command reset failed:")
    )


def _is_container_fault(error: BaseException) -> bool:
    return (
        isinstance(error, ProjectCommandError)
        and error.command == "check"
        and error.detail == "container command make failed: [Errno 2] No such file or directory"
    )


@pytest.mark.parametrize(
    ("build", "error", "matches", "runs_nothing"),
    [
        pytest.param(_without_base, ProjectCommandError, _is_snapshot_fault, False, id="no-base"),
        pytest.param(
            _unstartable, ProjectCommandError, _is_container_fault, False, id="no-container"
        ),
        pytest.param(
            _failing_git, GitError, lambda error: error is GIT_FAULT, True, id="git-fails"
        ),
        pytest.param(
            _escaping_git,
            ValueError,
            lambda error: isinstance(error, ValueError),
            True,
            id="path-outside",
        ),
    ],
)
def test_faults_are_project_command_errors_but_git_and_paths_propagate(
    setup: Setup,
    build: Callable[[Setup], ContainerMakeCommands],
    error: type[Exception],
    matches: Callable[[BaseException], bool],
    runs_nothing: bool,
) -> None:
    setup.with_base(makefile(sync="@true", check="@true"))

    with pytest.raises(error) as raised:
        build(setup).run("check", time_limit=LIMIT)

    assert matches(raised.value)
    if runs_nothing:
        assert setup.containers.calls == []


def test_container_commands_are_project_commands(setup: Setup) -> None:
    assert isinstance(setup.commands(), ProjectCommands)


def _files(root: Path, *, beside_checkout: bool) -> dict[str, bytes]:
    files = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    if beside_checkout:
        return {path: data for path, data in files.items() if not path.startswith("checkout/")}
    return {path: data for path, data in files.items() if path.startswith("checkout/.git/")}


@pytest.mark.parametrize(
    "beside_checkout",
    [
        pytest.param(False, id="dataset-git-untouched"),
        pytest.param(True, id="nothing-beside-checkout"),
    ],
)
def test_copy_writes_under_the_dataset_checkout_and_never_its_git(
    setup: Setup, beside_checkout: bool
) -> None:
    setup.with_base(makefile(sync="@true", check="@true"))
    _host_adds_and_changes(setup)
    before = _files(setup.base, beside_checkout=beside_checkout)

    result = setup.commands().run("check", time_limit=LIMIT)

    assert result.status == "passed"
    assert _files(setup.workspace, beside_checkout=beside_checkout) == before
