"""The setup script's step `transcripts` and its setting's line."""

import re

import pytest

from vm_support import indent, name_positions

MARKER = "setup: transcripts: "
SETTING = "FACTORY_TRANSCRIPT_DIR"
LINE = "FACTORY_TRANSCRIPT_DIR=/srv/factory/$instance/transcripts"
FOLDER_FORMS = ("$base/transcripts", "/srv/factory/$instance/transcripts")
ANY_MARKER = re.compile(r"setup: [\w-]+: ")


def _step(code: str) -> str:
    first = code.find(MARKER)
    last = code.rfind(MARKER)
    assert first >= 0, f"no '{MARKER}' text"
    earlier = [
        found.start() for found in ANY_MARKER.finditer(code, 0, first) if found.group(0) != MARKER
    ]
    start = code.find("\n", earlier[-1]) if earlier else 0
    end = code.find("\n", last)
    return code[start : len(code) if end < 0 else end]


def _path_words(code: str, forms: tuple[str, ...]) -> list[str]:
    """The path's literal forms and every variable the script assigns one of them to."""
    names = [
        found.group(1)
        for form in forms
        for found in re.finditer(rf"(?<![\w$])(\w+)=[\"']?{re.escape(form)}(?![\w/.-])", code)
    ]
    return [*forms, *(f"${name}" for name in names), *(f"${{{name}}}" for name in names)]


def _conditions(lines: list[str], index: int) -> list[str]:
    """The `if` and `elif` lines that the line at `index` lies under, nearest first."""
    found: list[str] = []
    level = indent(lines[index])
    for earlier in range(index - 1, -1, -1):
        line = lines[earlier]
        if not line.strip() or indent(line) >= level:
            continue
        word = line.lstrip()
        if word.startswith(("else", "elif ")):
            for opener in range(earlier - 1, -1, -1):
                head = lines[opener]
                if indent(head) == indent(line) and head.lstrip().startswith(("if ", "elif ")):
                    found.append(head)
                    if head.lstrip().startswith("if "):
                        break
        if word.startswith(("if ", "elif ")):
            found.append(line)
        level = indent(line)
    return found


def test_the_step_makes_the_folder_factory_s_with_0700_only_when_it_is_missing(code: str) -> None:
    lines = _step(code).splitlines()
    words = _path_words(code, FOLDER_FORMS)
    made = [
        index
        for index, line in enumerate(lines)
        if "install -d" in line
        and "-o factory" in line
        and "-g factory" in line
        and "-m 0700" in line
        and any(word in line for word in words)
    ]

    assert len(made) == 1
    conditions = _conditions(lines, made[0])
    assert len(conditions) == 1
    assert any(word in conditions[0] for word in words)
    assert "700" in conditions[0] or "factory" in conditions[0]
    found = [line for line in lines if "found" in line and MARKER in line]
    assert len(found) == 1
    assert any(word in found[0] for word in words)
    assert "rule" not in found[0]
    assert "tmpfiles" not in found[0]


def test_the_setting_s_line_is_written_once_and_always(code: str) -> None:
    positions = name_positions(code, SETTING)

    assert code.count(LINE) == 1
    assert len(positions) == 1
    lines = code.splitlines()
    index = next(i for i, line in enumerate(lines) if LINE in line)
    assert _conditions(lines, index) == []
    assert "&&" not in lines[index]
    assert "||" not in lines[index]


@pytest.mark.parametrize("word", ["--transcript-days", "tmpfiles.d"])
def test_the_script_keeps_no_retention_for_the_transcripts(code: str, word: str) -> None:
    assert word not in code


def test_the_step_refuses_a_link_at_the_folder_before_it_makes_anything(code: str) -> None:
    lines = _step(code).splitlines()
    words = _path_words(code, FOLDER_FORMS)
    refusal = " is a link; remove it and run this script again"
    said = [
        index
        for index, line in enumerate(lines)
        if MARKER in line and any(f"{word}{refusal}" in line for word in words) and ">&2" in line
    ]
    made = [index for index, line in enumerate(lines) if "install -d" in line]

    assert len(said) == 1
    conditions = _conditions(lines, said[0])
    assert len(conditions) == 1
    assert "-L" in conditions[0]
    assert any(word in conditions[0] for word in words)
    following = [line.strip() for line in lines[said[0] + 1 :] if line.strip()]
    assert following
    assert following[0] == "exit 1"
    assert made
    assert all(said[0] < index for index in made)
