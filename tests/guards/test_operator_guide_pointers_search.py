"""The operator's scripts and skill name the operator guide's topic file wherever they name it."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
SETUP = ROOT / "operator" / "vm" / "setup.sh"
SEARCHED = (ROOT / "operator" / "vm", ROOT / "operator" / "skill")
GUIDE_PATH = "docs/operator-guide/"
TOPIC_FILE = re.compile(r"docs/operator-guide/([\w.-]+\.md)")
DONE_LINE = (
    "printf 'setup: done: build the stage image and start factory@%s;"
    ' see "The machine" in docs/operator-guide/machine.md\\n\' "$instance"'
)


def _unpointed(lines: list[str]) -> list[str]:
    return [line for line in lines if "operator guide" in line and GUIDE_PATH not in line]


def _searched_lines() -> list[tuple[Path, str]]:
    found: list[tuple[Path, str]] = []
    for folder in SEARCHED:
        for path in sorted(folder.rglob("*")):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            found.extend((path, line) for line in text.splitlines())
    return found


def test_every_mention_of_the_operator_guide_names_its_path() -> None:
    lines = _searched_lines()

    assert lines != []
    assert _unpointed([line for _, line in lines]) == []


@pytest.mark.parametrize(
    ("line", "caught"),
    [
        pytest.param('see the operator guide, "The machine"', True, id="no-path"),
        pytest.param('see "The machine" in docs/operator-guide/machine.md', False, id="topic-file"),
        pytest.param("the operator guide (docs/operator-guide/README.md)", False, id="index-file"),
    ],
)
def test_a_mention_without_a_path_is_caught(line: str, caught: bool) -> None:
    assert _unpointed([line]) == ([line] if caught else [])


def test_every_named_topic_file_exists() -> None:
    named = {name for _, line in _searched_lines() for name in TOPIC_FILE.findall(line)}

    assert named != set()
    assert sorted(name for name in named if not (ROOT / GUIDE_PATH / name).is_file()) == []


@pytest.mark.parametrize("old", ["(operator guide, ", "see the operator guide, "])
def test_the_setup_script_holds_no_old_pointer(old: str) -> None:
    lines = SETUP.read_text(encoding="utf-8").splitlines()

    assert [line for line in lines if old in line] == []


def test_the_closing_line_names_the_machine_topic_file() -> None:
    lines = SETUP.read_text(encoding="utf-8").splitlines()

    assert [line.strip() for line in lines if "setup: done: " in line] == [DONE_LINE]
