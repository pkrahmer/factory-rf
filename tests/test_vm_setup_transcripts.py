"""The setup script's option `--transcript-days` and its step `transcripts`."""

import re
from pathlib import Path

import pytest

from vm_support import (
    REQUIRED,
    SYSTEM_PATH,
    compares,
    indent,
    name_positions,
    run_setup,
    writes_path,
)

OPTION = "--transcript-days"
MARKER = "setup: transcripts: "
SETTING = "FACTORY_TRANSCRIPT_DIR"
LINE = "FACTORY_TRANSCRIPT_DIR=/srv/factory/$instance/transcripts"
RULE_FILE = "/etc/tmpfiles.d/factory-$instance-transcripts.conf"
FOLDER_FORMS = ("$base/transcripts", "/srv/factory/$instance/transcripts")
OPTION_PARSING = re.compile(r"\bcase\s+\"?\$\{?1\b")
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


def _days_variables(code: str) -> list[str]:
    arm = re.search(rf"(?s){re.escape(OPTION)}\)(.*?);;", code)
    return [] if arm is None else re.findall(r"(?<![\w$])(\w+)=", arm.group(1))


def _path_words(code: str, forms: tuple[str, ...]) -> list[str]:
    """The path's literal forms and every variable the script assigns one of them to."""
    names = [
        found.group(1)
        for form in forms
        for found in re.finditer(rf"(?<![\w$])(\w+)=[\"']?{re.escape(form)}(?![\w/.-])", code)
    ]
    return [*forms, *(f"${name}" for name in names), *(f"${{{name}}}" for name in names)]


def _tests_days(text: str, variables: list[str]) -> bool:
    return any(re.search(rf"\$\{{?{name}(?!\w)", text) for name in variables)


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


def _guarded_by_days(lines: list[str], index: int, variables: list[str]) -> bool:
    line = lines[index]
    return any(_tests_days(each, variables) for each in _conditions(lines, index)) or (
        _tests_days(line.split("&&")[0] if "&&" in line else "", variables)
    )


@pytest.mark.parametrize(
    ("words", "accepted"),
    [
        pytest.param([OPTION], False, id="without-value"),
        pytest.param([OPTION, ""], False, id="empty"),
        pytest.param([OPTION, "x"], False, id="letter"),
        pytest.param([OPTION, "-1"], False, id="negative"),
        pytest.param([OPTION, "1.5"], False, id="fraction"),
        pytest.param([OPTION, "0"], True, id="zero"),
        pytest.param([OPTION, "7"], True, id="seven"),
        pytest.param([], True, id="default"),
    ],
)
def test_the_transcript_days_take_a_whole_number_of_zero_or_more(
    tmp_path: Path, words: list[str], accepted: bool
) -> None:
    stand_in = tmp_path / "bin" / "id"
    stand_in.parent.mkdir()
    stand_in.write_text("#!/bin/sh\necho 1000\n", encoding="utf-8")
    stand_in.chmod(0o755)

    result = run_setup(tmp_path, [*REQUIRED, *words], path=f"{stand_in.parent}:{SYSTEM_PATH}")

    assert result.exit_status == 2
    assert result.stdout == ""
    if accepted:
        assert result.stderr == "setup.sh: run as root\n"
    else:
        lines = result.stderr.splitlines()
        assert lines[0].startswith("setup.sh: ")
        assert OPTION in lines[0]
        assert any(line.startswith("usage: setup.sh") for line in lines[1:])


def test_the_usage_names_the_transcript_days(tmp_path: Path) -> None:
    result = run_setup(tmp_path, ["--help"])

    assert result.exit_status == 0
    assert OPTION in result.stdout.splitlines()[0]


def test_the_transcript_days_default_to_thirty_before_the_option_parsing(code: str) -> None:
    variables = _days_variables(code)
    parsing = OPTION_PARSING.search(code)
    defaults = [
        found.start()
        for name in variables
        for found in re.finditer(rf"(?<![\w$-]){name}=[\"']?30(?![\w])", code)
    ]

    assert variables != []
    assert parsing is not None
    assert len(defaults) == 1
    assert defaults[0] < parsing.start()


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
    assert any(
        any(word in each for word in words) and ("700" in each or "factory" in each)
        for each in conditions
    )
    assert _guarded_by_days(lines, made[0], _days_variables(code))


def test_the_setting_s_line_is_written_once_and_only_with_days(code: str) -> None:
    positions = name_positions(code, SETTING)

    assert code.count(LINE) == 1
    assert len(positions) == 1
    lines = code.splitlines()
    index = next(i for i, line in enumerate(lines) if LINE in line)
    assert _guarded_by_days(lines, index, _days_variables(code))


def test_the_tmpfiles_rule_says_the_folder_its_owner_mode_and_age(code: str) -> None:
    variables = _days_variables(code)
    step = _step(code)
    rules = [
        line
        for line in step.splitlines()
        if any(
            re.search(
                re.escape("d /srv/factory/$instance/transcripts 0700 factory factory ")
                + rf"\$\{{?{name}\}}?d(?!\w)",
                line,
            )
            for name in variables
        )
    ]

    assert variables != []
    assert len(rules) == 1
    assert step.count(RULE_FILE) >= 1


def test_the_tmpfiles_rule_is_written_only_with_days_and_when_its_text_differs(
    code: str,
) -> None:
    lines = _step(code).splitlines()
    variables = _days_variables(code)
    words = _path_words(code, (RULE_FILE,))
    compared = [
        i for i, line in enumerate(lines) if any(compares(code, line, word) for word in words)
    ]
    written = [i for i, line in enumerate(lines) if any(writes_path(line, word) for word in words)]

    assert compared != []
    assert written != []
    assert compared[0] < written[0]
    assert all(_guarded_by_days(lines, index, variables) for index in written)
    assert any("found" in line for line in lines)
