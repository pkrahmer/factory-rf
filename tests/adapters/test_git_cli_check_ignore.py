"""The git wrapper's question which paths the checkout's ignore rules ignore."""

import json
from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from factory.domain.errors import GitError
from factory.domain.git import GitOptions
from git_support import write_executable
from human_clone import HumanClone

GITIGNORE = ".venv/\n*.log\n!keep.log\n"
KEPT_LOG = "docs/kept.log"
WORK_BRANCH = "work"

STANDIN = """\
import json
import sys

arguments = sys.argv[1:]
with open({calls!r}, "a", encoding="utf-8") as calls:
    calls.write(json.dumps(arguments) + "\\n")
paths = arguments[arguments.index("--") + 1 :]
mode = {mode!r}
if mode == "fatal":
    print("fatal: boom", file=sys.stderr)
    sys.exit(128)
if mode == "short":
    paths = paths[:-1]
if mode == "long":
    paths = [*paths, "extra"]
for path in paths:
    print("::\\t" + path)
"""


@pytest.fixture
def ignoring(checkout: GitCli, human: HumanClone) -> GitCli:
    """The checkout on a branch of `main`, which holds the tracked `docs/kept.log`, then rules."""
    # The file goes first: `GitCli.commit` stages no file the rules already ignore.
    human.push_file("main", KEPT_LOG, "kept\n")
    human.push_file("main", ".gitignore", GITIGNORE)
    checkout.fetch()
    checkout.checkout(WORK_BRANCH, start_point="origin/main")
    return checkout


def _standin(tmp_path: Path, mode: str) -> tuple[GitCli, Path]:
    calls = tmp_path / "calls.jsonl"
    executable = write_executable(tmp_path, STANDIN.format(calls=str(calls), mode=mode))
    return GitCli(tmp_path, GitOptions(executable=str(executable))), calls


def _calls(calls: Path) -> list[list[str]]:
    if not calls.exists():
        return []
    lines = calls.read_text(encoding="utf-8").splitlines()
    return [[str(argument) for argument in json.loads(line)] for line in lines]


@pytest.mark.parametrize(
    ("paths", "expected"),
    [
        pytest.param(
            [".venv/bin/python", "src/a.py", "run.log"],
            [".venv/bin/python", "run.log"],
            id="order-given",
        ),
        pytest.param(
            ["run.log", ".venv/bin/python"], ["run.log", ".venv/bin/python"], id="order-reversed"
        ),
        pytest.param(["src/a.py"], [], id="unmatched"),
        pytest.param(["keep.log"], [], id="negation"),
        pytest.param([KEPT_LOG], [], id="tracked"),
    ],
)
def test_ignored_names_the_paths_the_rules_ignore_in_the_order_given(
    ignoring: GitCli, paths: list[str], expected: list[str]
) -> None:
    assert ignoring.ignored(paths) == expected


@pytest.mark.parametrize(
    ("paths", "refused"),
    [
        pytest.param([], False, id="no-paths"),
        pytest.param(["/abs"], True, id="absolute"),
        pytest.param(["a/../b"], True, id="dot-dot"),
    ],
)
def test_ignored_runs_no_git_for_no_paths_or_a_refused_path(
    tmp_path: Path, paths: list[str], *, refused: bool
) -> None:
    cli, calls = _standin(tmp_path, "answer")

    if refused:
        with pytest.raises(ValueError):
            cli.ignored(paths)
    else:
        assert cli.ignored(paths) == []

    assert _calls(calls) == []


@pytest.mark.parametrize(
    ("count", "mode", "groups"),
    [
        pytest.param(1000, "answer", [1000], id="one-group"),
        pytest.param(1001, "answer", [1000, 1], id="two-groups"),
        pytest.param(3, "fatal", None, id="exit-128"),
        pytest.param(3, "short", None, id="line-short"),
        pytest.param(3, "long", None, id="line-long"),
    ],
)
def test_ignored_asks_git_in_groups_and_refuses_an_answer_it_cannot_read(
    tmp_path: Path, count: int, mode: str, groups: list[int] | None
) -> None:
    cli, calls = _standin(tmp_path, mode)
    paths = [f"src/file{number}.py" for number in range(count)]

    if groups is None:
        with pytest.raises(GitError):
            cli.ignored(paths)
        return

    assert cli.ignored(paths) == []
    recorded = _calls(calls)
    asked = [call[call.index("--") + 1 :] for call in recorded]
    assert [len(group) for group in asked] == groups
    assert [path for group in asked for path in group] == paths
    for call in recorded:
        assert call[: call.index("--")][-3:] == ["check-ignore", "--verbose", "--non-matching"]
