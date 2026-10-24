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
GROUP = 1000
ANSWER = "for path in paths:\n    print('::\\t' + path)"
FATAL = "sys.stderr.write('fatal: boom\\n')\nsys.exit(128)"
SHORT = "for path in paths[1:]:\n    print('::\\t' + path)"


@pytest.fixture
def ignoring(checkout: GitCli, human: HumanClone) -> GitCli:
    """The checkout at a `main` holding the tracked `docs/kept.log` and then the `.gitignore`."""
    human.push_file("main", "docs/kept.log", "kept\n")
    human.push_file("main", ".gitignore", GITIGNORE)
    checkout.fetch()
    checkout.reset_to("origin/main")
    return checkout


@pytest.mark.parametrize(
    ("paths", "expected"),
    [
        pytest.param(
            [".venv/bin/python", "src/a.py", "run.log"],
            [".venv/bin/python", "run.log"],
            id="in-order",
        ),
        pytest.param(
            ["run.log", ".venv/bin/python"], ["run.log", ".venv/bin/python"], id="order-given"
        ),
        pytest.param(["src/a.py"], [], id="not-ignored"),
        pytest.param(["keep.log"], [], id="negation"),
        pytest.param(["docs/kept.log"], [], id="tracked"),
    ],
)
def test_ignored_names_the_paths_the_rules_ignore_in_the_order_given(
    ignoring: GitCli, paths: list[str], expected: list[str]
) -> None:
    assert ignoring.ignored(paths) == expected


def _stand_in(tmp_path: Path, answer: str) -> tuple[GitCli, Path]:
    calls = tmp_path / "calls"
    body = (
        "import json\nimport sys\n"
        f"with open({str(calls)!r}, 'a') as f:\n"
        "    f.write(json.dumps(sys.argv[1:]) + '\\n')\n"
        "paths = sys.argv[sys.argv.index('--') + 1:]\n"
        f"{answer}"
    )
    executable = write_executable(tmp_path, body)
    return GitCli(tmp_path, GitOptions(executable=str(executable))), calls


def _calls(calls: Path) -> list[list[str]]:
    if not calls.exists():
        return []
    return [json.loads(line) for line in calls.read_text(encoding="utf-8").splitlines()]


def _paths(count: int) -> list[str]:
    return [f"src/file-{number:04d}.py" for number in range(count)]


@pytest.mark.parametrize(
    ("answer", "paths", "error", "count"),
    [
        pytest.param(ANSWER, _paths(GROUP), None, 1, id="one-group"),
        pytest.param(ANSWER, _paths(GROUP + 1), None, 2, id="two-groups"),
        pytest.param(ANSWER, [], None, 0, id="no-paths"),
        pytest.param(ANSWER, ["/abs"], ValueError, 0, id="absolute"),
        pytest.param(ANSWER, ["a/../b"], ValueError, 0, id="dot-dot"),
        pytest.param(FATAL, ["src/a.py"], GitError, 1, id="fatal"),
        pytest.param(SHORT, ["src/a.py", "src/b.py"], GitError, 1, id="line-short"),
    ],
)
def test_ignored_asks_git_in_groups_and_refuses_what_it_cannot_read(
    tmp_path: Path,
    *,
    answer: str,
    paths: list[str],
    error: type[Exception] | None,
    count: int,
) -> None:
    cli, calls = _stand_in(tmp_path, answer)

    if error is None:
        assert cli.ignored(paths) == []
    else:
        with pytest.raises(error):
            cli.ignored(paths)

    recorded = _calls(calls)
    assert len(recorded) == count
    assert all("check-ignore" in arguments for arguments in recorded)
    if error is None:
        asked = [path for arguments in recorded for path in arguments[arguments.index("--") + 1 :]]
        assert asked == paths
