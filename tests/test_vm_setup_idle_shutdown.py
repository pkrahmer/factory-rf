"""The setup script's option `--idle-shutdown` and its step `poweroff`."""

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest

from vm_support import (
    ENVIRONMENT,
    REQUIRED,
    SYSTEM_PATH,
    compares,
    enclosing_if,
    in_order,
    lines_with,
    name_positions,
    run_setup,
    step_texts,
    writes_path,
)

SUDOERS = "/etc/sudoers.d/factory-poweroff"
RULE = "factory ALL=(root) NOPASSWD: /usr/bin/systemctl poweroff"
NOT_ASKED = "setup: poweroff: not asked; the factory gets no power-off right"
SETTING = "FACTORY_IDLE_SHUTDOWN_MINUTES"
ASSIGNMENT = re.compile(r"(?<![\w$])[A-Z][A-Z0-9_]*=")


@dataclass(frozen=True)
class Script:
    """The setup script's text without comment lines and its steps `poweroff` and `environment`."""

    code: str
    poweroff: str
    environment: str


@pytest.fixture
def script(code: str) -> Script:
    """Return the setup script's text and its steps `poweroff` and `environment`."""
    steps = step_texts(code)
    return Script(code, steps["poweroff"], steps["environment"])


@pytest.mark.parametrize(
    ("words", "accepted"),
    [
        pytest.param(["--idle-shutdown"], False, id="without-value"),
        pytest.param(["--idle-shutdown", ""], False, id="empty"),
        pytest.param(["--idle-shutdown", "0"], False, id="zero"),
        pytest.param(["--idle-shutdown", "x"], False, id="letter"),
        pytest.param(["--idle-shutdown", "-5"], False, id="negative"),
        pytest.param(["--idle-shutdown", "1.5"], False, id="fraction"),
        pytest.param(["--idle-shutdown", "1"], True, id="one"),
        pytest.param(["--idle-shutdown", "30"], True, id="thirty"),
    ],
)
def test_the_idle_shutdown_takes_a_whole_number_of_minutes_of_at_least_one(
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
        assert any(line.startswith("usage: setup.sh") for line in lines[1:])


@pytest.mark.parametrize(
    "check",
    [
        pytest.param(
            lambda s: in_order(
                s.code, ["setup: caches: ", "setup: poweroff: ", "setup: folders: "]
            ),
            id="after-caches-before-folders",
        ),
        *(
            pytest.param(lambda s, word=word: word in s.poweroff, id=word)
            for word in (SUDOERS, "chmod 0440", "visudo -cf", f"rm -f {SUDOERS}")
        ),
        pytest.param(lambda s: s.code.count(RULE) == 1 and RULE in s.poweroff, id="one-rule"),
        pytest.param(
            lambda s: lines_with(s.code, "systemctl poweroff") == lines_with(s.code, RULE),
            id="poweroff-only-in-the-rule",
        ),
    ],
)
def test_the_poweroff_step_follows_caches_and_writes_or_removes_its_rule(
    script: Script, check: Callable[[Script], bool]
) -> None:
    assert check(script)


def test_the_idle_shutdown_setting_is_the_environment_file_s_line_after_the_others(
    code: str,
) -> None:
    positions = name_positions(code, SETTING)

    assert len(positions) == 1
    assert code.find("XDG_RUNTIME_DIR=") < positions[0] < code.find("factory@.service")
    found = [name_positions(code, name) for name, _ in ENVIRONMENT]
    assert all(len(places) == 1 for places in found)
    assert [places[0] for places in found] == sorted(places[0] for places in found)


def test_a_refused_visudo_check_removes_the_poweroff_rule_and_ends_the_script(
    script: Script,
) -> None:
    lines = script.poweroff.splitlines()
    checked = next(index for index, line in enumerate(lines) if "visudo -cf" in line)
    after = lines[checked + 1 :]
    removed = next(index for index, line in enumerate(after) if f"rm -f {SUDOERS}" in line)
    printed = next(index for index, line in enumerate(after) if ">&2" in line)
    ended = next(index for index, line in enumerate(after) if line.strip() == "exit 1")

    assert removed < ended
    assert printed < ended


def _written_by_root_with_0440(script: Script) -> bool:
    lines = script.poweroff.splitlines()
    writes = [line for line in lines if writes_path(line, SUDOERS)]
    modes = [
        line
        for line in lines
        if SUDOERS in line and ("chmod 0440" in line or "install -m 0440" in line)
    ]
    return (
        writes != []
        and modes != []
        and not any("runuser" in line or "as_factory" in line for line in writes)
    )


def _compared_before_written(script: Script) -> bool:
    lines = script.poweroff.splitlines()
    compared = [i for i, line in enumerate(lines) if compares(script.code, line, SUDOERS)]
    written = [i for i, line in enumerate(lines) if writes_path(line, SUDOERS)]
    return compared != [] and written != [] and compared[0] < written[0]


@pytest.mark.parametrize(
    "check",
    [
        pytest.param(_compared_before_written, id="compared-before-written"),
        pytest.param(lambda s: f"wrote {SUDOERS}" in s.poweroff, id="wrote"),
        pytest.param(
            lambda s: any("found" in line and SUDOERS in line for line in s.poweroff.splitlines()),
            id="found",
        ),
        pytest.param(_written_by_root_with_0440, id="root-0440"),
    ],
)
def test_the_poweroff_step_writes_its_rule_only_when_its_text_differs(
    script: Script, check: Callable[[Script], bool]
) -> None:
    assert check(script)


def test_without_the_option_the_step_says_the_factory_gets_no_power_off_right(
    script: Script,
) -> None:
    assert re.search(re.escape(NOT_ASKED) + r"[\"']", script.poweroff) is not None


def _option_variables(code: str) -> list[str]:
    arm = re.search(r"(?s)--idle-shutdown\)(.*?);;", code)
    return [] if arm is None else re.findall(r"(?<![\w$])(\w+)=", arm.group(1))


def _tests_the_option(text: str, variables: list[str]) -> bool:
    return any(re.search(rf"\$\{{?{name}(?!\w)", text) for name in variables)


def test_the_idle_shutdown_setting_is_written_last_and_only_with_the_option(
    script: Script,
) -> None:
    lines = script.environment.splitlines()
    index = next(i for i, line in enumerate(lines) if f"{SETTING}=" in line)
    line = lines[index]
    variables = _option_variables(script.code)
    condition = enclosing_if(lines, index)
    guard = line[: line.find(f"{SETTING}=")]

    assert variables != []
    assert (condition is not None and _tests_the_option(lines[condition], variables)) or (
        _tests_the_option(guard, variables)
    )
    rest = "\n".join(lines[index + 1 :])
    assert ASSIGNMENT.search(rest) is None
    assert "XDG_RUNTIME_DIR=" in "\n".join(lines[:index])
