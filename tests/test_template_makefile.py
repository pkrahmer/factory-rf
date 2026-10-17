"""The template's Makefile: its text, and its targets run with a stand-in `uv`."""

import json
import os
import re
import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path

import pytest

from adapters.claude_stand_in import Step, read_calls, write_stand_in
from factory.adapters.process import ProcessRequest, ProcessResult, run_process
from git_support import commit_all, run_git, write_files
from shipped_agents import ROOT

MAKEFILE = ROOT / "template" / "Makefile"

# An outer `make` passes its variables on through these; the run must see none of them.
DROPPED = {"MAKEFLAGS", "MFLAGS", "MAKELEVEL", "FEATURE", "SOURCE", "LAYERS"}
VARIABLES = ["SOURCE=src/todo", "LAYERS=uv run lint-imports"]

TRACKED = {
    ".secrets.baseline": "{}\n",
    "README.md": "# Todo\n",
    "src/todo/a.py": "x = 1\n",
    "uv.lock": "version = 1\n",
}


def _lines() -> list[str]:
    return MAKEFILE.read_text(encoding="utf-8").splitlines()


def _green(target: str) -> re.Pattern[str]:
    return re.compile(rf"^{target}: green \(\d+\.\d s\)$")


@pytest.fixture
def project(tmp_path: Path) -> Path:
    folder = tmp_path / "project"
    folder.mkdir()
    shutil.copyfile(MAKEFILE, folder / "Makefile")
    return folder


def _stand_in(tmp_path: Path, steps: list[Step]) -> Path:
    path = write_stand_in(tmp_path / "bin", steps)
    path.rename(path.with_name("uv"))
    return tmp_path / "bin"


def _make(tmp_path: Path, *args: str) -> ProcessResult:
    environment = {key: value for key, value in os.environ.items() if key not in DROPPED}
    environment["PATH"] = f"{tmp_path / 'bin'}{os.pathsep}{os.environ['PATH']}"
    return run_process(
        ProcessRequest(
            argv=["make", *args],
            cwd=tmp_path / "project",
            env=environment,
            time_limit=timedelta(seconds=120),
            merge_stderr=True,
        )
    )


def _arguments(tmp_path: Path) -> list[list[str]]:
    return [call.arguments for call in read_calls(tmp_path / "bin")]


def test_phony_line_names_the_targets_and_there_is_no_documents_target() -> None:
    phony = [line for line in _lines() if line.startswith(".PHONY:")]

    assert len(phony) == 1
    assert phony[0].removeprefix(".PHONY:").split() == [
        "check",
        "lint",
        "types",
        "layers",
        "sast",
        "secrets",
        "licenses",
        "test",
        "duplicates",
        "mutants",
    ]
    assert not [line for line in _lines() if re.match(r"^documents\s*:", line)]


def test_check_runs_the_other_targets_and_says_green() -> None:
    lines = _lines()
    heads = [index for index, line in enumerate(lines) if re.match(r"^check\s*:", line)]

    assert len(heads) == 1
    head = heads[0]
    assert lines[head].split(":", 1)[1].split() == [
        "lint",
        "types",
        "layers",
        "sast",
        "secrets",
        "licenses",
        "test",
    ]
    recipe = []
    for line in lines[head + 1 :]:
        if not line.startswith("\t"):
            break
        recipe.append(line)
    assert recipe == ['\techo "check: green"']


def test_package_folder_and_layers_command_are_placeholders() -> None:
    lines = _lines()

    assert "SOURCE = src/<package>" in lines
    assert "LAYERS = <layers command>" in lines


@pytest.mark.parametrize(
    "tool",
    [
        "ruff",
        "mypy",
        "semgrep",
        "bandit",
        "detect-secrets",
        "pip-licenses",
        "pytest",
        "pytest-cov",
        "pytest-xdist",
        "pylint",
        "vulture",
        "mutmut",
        "import-linter",
    ],
)
def test_header_names_the_development_dependency(tool: str) -> None:
    header = []
    for line in _lines():
        if not line.startswith("#"):
            break
        header.append(line)

    assert re.search(rf"(?<![\w-]){re.escape(tool)}(?![\w-])", "\n".join(header))


@pytest.mark.usefixtures("project")
@pytest.mark.parametrize("status", [0, 1])
@pytest.mark.parametrize("target", ["lint", "types", "layers", "sast", "licenses", "test"])
def test_target_is_timed_green_and_stops_at_its_first_failing_line(
    tmp_path: Path, target: str, status: int
) -> None:
    _stand_in(tmp_path, [Step(exit_status=status)] * 4)

    result = _make(tmp_path, target, *VARIABLES)

    if status == 0:
        assert result.exit_status == 0, result.stdout
        assert _green(target).match(result.stdout.splitlines()[-1]), result.stdout
    else:
        assert result.exit_status != 0
        assert "green" not in result.stdout
        assert len(read_calls(tmp_path / "bin")) == 1


def test_test_runs_pytest_on_every_core_with_a_junit_report(tmp_path: Path, project: Path) -> None:
    _stand_in(tmp_path, [Step()])

    _make(tmp_path, "test", *VARIABLES)

    calls = _arguments(tmp_path)
    assert len(calls) == 1
    arguments = calls[0]
    assert arguments[:2] == ["run", "pytest"]
    assert any(arguments[index : index + 2] == ["-n", "auto"] for index in range(len(arguments)))
    assert "--junit-xml=.reports/junit.xml" in arguments
    assert (project / ".reports").is_dir()


@pytest.mark.usefixtures("project")
def test_test_is_green_when_no_test_is_collected(tmp_path: Path) -> None:
    _stand_in(tmp_path, [Step(exit_status=5)])

    result = _make(tmp_path, "test", *VARIABLES)

    assert result.exit_status == 0, result.stdout
    assert _green("test").match(result.stdout.splitlines()[-1]), result.stdout


def _set_origin_main(folder: Path) -> None:
    head = run_git(folder, "rev-parse", "HEAD").strip()
    run_git(folder, "update-ref", "refs/remotes/origin/main", head)


def _branch(folder: Path, files: dict[str, str]) -> None:
    _set_origin_main(folder)
    run_git(folder, "checkout", "-q", "-b", "work-item/F0001-S0001")
    write_files(folder, files)
    commit_all(folder, "change")


def _on_main(folder: Path) -> None:
    _set_origin_main(folder)


def _without_origin(folder: Path) -> None:
    assert not run_git(folder, "branch", "--remotes").strip()


def _branch_with_code_untracked_and_unstaged(folder: Path) -> None:
    _branch(folder, {"src/todo/a.py": "x = 2\n"})
    write_files(folder, {"src/todo/b.py": "y = 1\n", "uv.lock": "version = 2\n"})


def _branch_with_lock_only(folder: Path) -> None:
    _branch(folder, {"uv.lock": "version = 2\n"})


def _branch_with_code(folder: Path) -> None:
    _branch(folder, {"src/todo/a.py": "x = 2\n"})


@pytest.mark.parametrize(
    ("setup", "status", "files"),
    [
        pytest.param(_on_main, 0, ["Makefile", "README.md", "src/todo/a.py"], id="main"),
        pytest.param(
            _without_origin, 0, ["Makefile", "README.md", "src/todo/a.py"], id="no-origin"
        ),
        pytest.param(
            _branch_with_code_untracked_and_unstaged,
            0,
            ["src/todo/a.py", "src/todo/b.py"],
            id="branch",
        ),
        pytest.param(_branch_with_lock_only, 0, None, id="lock-only"),
        pytest.param(_branch_with_code, 1, ["src/todo/a.py"], id="secret-found"),
    ],
)
def test_secrets_scans_the_changed_files_or_every_tracked_file(
    tmp_path: Path,
    project: Path,
    setup: Callable[[Path], None],
    status: int,
    files: list[str] | None,
) -> None:
    run_git(project, "init", "-q", "--initial-branch=main")
    write_files(project, TRACKED)
    commit_all(project, "seed")
    setup(project)
    _stand_in(tmp_path, [Step(exit_status=status)])

    result = _make(tmp_path, "secrets", *VARIABLES)

    if files is None:
        assert _arguments(tmp_path) == []
    else:
        assert _arguments(tmp_path) == [
            ["run", "detect-secrets-hook", "--baseline", ".secrets.baseline", *files]
        ]
    if status == 0:
        assert result.exit_status == 0, result.stdout
        assert _green("secrets").match(result.stdout.splitlines()[-1]), result.stdout
    else:
        assert result.exit_status != 0
        assert "green" not in result.stdout


def _pylint_json(messages: int) -> str:
    found = [
        {
            "type": "refactor",
            "module": "todo.a",
            "symbol": "duplicate-code",
            "message": "Similar lines in 2 files",
            "message-id": "R0801",
        }
    ] * messages
    return json.dumps(found, indent=4) + "\n"


VULTURE_LINES = (
    "src/todo/a.py:1: unused function 'f' (60% confidence)\n"
    "src/todo/a.py:5: unused variable 'y' (60% confidence)\n"
)


@pytest.mark.parametrize(
    ("steps", "last_line", "calls"),
    [
        pytest.param(
            [Step(stdout=_pylint_json(0)), Step(stdout="", exit_status=0)],
            "duplicates: 0 similar code, 0 dead code, in .reports/",
            None,
            id="none",
        ),
        pytest.param(
            [Step(stdout=_pylint_json(2)), Step(stdout=VULTURE_LINES, exit_status=3)],
            "duplicates: 2 similar code, 2 dead code, in .reports/",
            None,
            id="findings",
        ),
        pytest.param(
            [Step(stdout=_pylint_json(0)), Step(stdout=VULTURE_LINES, exit_status=1)],
            None,
            None,
            id="vulture-fails",
        ),
        pytest.param([Step(exit_status=1)], None, 1, id="pylint-fails"),
    ],
)
@pytest.mark.usefixtures("project")
def test_duplicates_counts_similar_and_dead_code(
    tmp_path: Path,
    steps: list[Step],
    last_line: str | None,
    calls: int | None,
) -> None:
    _stand_in(tmp_path, steps)

    result = _make(tmp_path, "duplicates", "SOURCE=src/todo")

    if last_line is not None:
        assert result.exit_status == 0, result.stdout
        assert result.stdout.splitlines()[-1] == last_line
    else:
        assert result.exit_status != 0
        assert not [line for line in result.stdout.splitlines() if line.startswith("duplicates:")]
    if calls is not None:
        assert len(read_calls(tmp_path / "bin")) == calls


def _feature_history(folder: Path, branch: str) -> None:
    run_git(folder, "init", "-q", "--initial-branch=main")
    write_files(folder, {"src/todo/items.py": "def add() -> None: ...\n"})
    commit_all(folder, "work item F0003-S0001: doing ends: review")
    write_files(folder, {"src/todo/lists.py": "def make() -> None: ...\n"})
    commit_all(folder, "F0003-S0002: Lists (#7)")
    write_files(folder, {"README.md": "# Todo\n"})
    commit_all(folder, "work item F0004-S0001: doing ends: review")
    _set_origin_main(folder)
    run_git(folder, "checkout", "-q", "-b", branch)


def _on_acceptance_branch(folder: Path) -> None:
    _feature_history(folder, "work-item/F0003-A0001")


def _on_story_branch(folder: Path) -> None:
    _feature_history(folder, "work-item/F0003-S0002")


def _no_repository(folder: Path) -> None:
    assert not (folder / ".git").exists()


SET_FEATURE = "mutants: set FEATURE, as in make mutants FEATURE=F0001"
RESULTS = "todo.items.x_add__mutmut_1: survived\ntodo.other.x_f__mutmut_1: not checked\n"


@dataclass(frozen=True)
class MutantsCase:
    """One run of `make mutants`: the repository, the extra variables and what it must show."""

    setup: Callable[[Path], None]
    extra: list[str]
    status: int
    calls: list[list[str]]
    printed: list[str]
    not_printed: list[str] = field(default_factory=list)
    green: bool = False


@pytest.mark.parametrize(
    "case",
    [
        pytest.param(
            MutantsCase(
                setup=_on_acceptance_branch,
                extra=[],
                status=0,
                calls=[
                    ["run", "mutmut", "run", "todo.items.*", "todo.lists.*"],
                    ["run", "mutmut", "results"],
                ],
                printed=["todo.items.x_add__mutmut_1: survived"],
                not_printed=["todo.other.x_f__mutmut_1: not checked"],
                green=True,
            ),
            id="acceptance-branch",
        ),
        pytest.param(
            MutantsCase(
                setup=_on_acceptance_branch,
                extra=["FEATURE=F0004"],
                status=0,
                calls=[],
                printed=["mutants: no module under src/todo changed by F0004"],
            ),
            id="no-module",
        ),
        pytest.param(MutantsCase(_on_story_branch, [], 2, [], [SET_FEATURE]), id="story-branch"),
        pytest.param(MutantsCase(_no_repository, [], 2, [], [SET_FEATURE]), id="no-repository"),
    ],
)
def test_mutants_runs_mutmut_over_the_modules_the_feature_changed(
    tmp_path: Path, project: Path, case: MutantsCase
) -> None:
    case.setup(project)
    _stand_in(tmp_path, [Step(), Step(stdout=RESULTS)])

    result = _make(tmp_path, "mutants", "SOURCE=src/todo", *case.extra)

    lines = result.stdout.splitlines()
    assert result.exit_status == case.status, result.stdout
    assert _arguments(tmp_path) == case.calls
    for line in case.printed:
        assert line in lines
    for line in case.not_printed:
        assert line not in lines
    if case.green:
        assert _green("mutants").match(lines[-1]), result.stdout
