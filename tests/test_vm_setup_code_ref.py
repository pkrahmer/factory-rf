"""The setup script's option `--code-ref`: the ref the factory's code is cloned at."""

import re
from pathlib import Path

import pytest

from vm_support import REQUIRED, SYSTEM_PATH, entries, run_setup, step_texts

HINT = "setup.sh: --ref is now --code-ref"
OLD_OPTION = re.compile(r"(?<![\w-])--ref(?![\w-])")
OPTION_PARSING = re.compile(r"\bcase\s+\"?\$\{?1\b")
STAND_INS = ("id", "git", "runuser", "dpkg-query", "apt-get", "zpool", "zfs", "mktemp", "install")


def _code_ref_variables(code: str) -> list[str]:
    arm = re.search(r"(?s)(?<![\w-])--code-ref\)(.*?);;", code)
    return [] if arm is None else re.findall(r"(?<![\w$])(\w+)=", arm.group(1))


def _branch_variable(line: str) -> str | None:
    found = re.search(r"--branch\s+\"?\$\{?(\w+)\}?\"?", line)
    return None if found is None else found.group(1)


@pytest.mark.parametrize(
    "marker",
    [
        pytest.param('GIT_ASKPASS="$askpass"', id="without-code-url"),
        pytest.param("env -u GIT_ASKPASS", id="different-code-url"),
    ],
)
def test_the_clone_of_the_code_takes_its_branch_from_the_code_ref(code: str, marker: str) -> None:
    variables = _code_ref_variables(code)
    clones = [
        line
        for line in step_texts(code)["checkout"].splitlines()
        if "git clone" in line and marker in line
    ]

    assert variables != []
    assert len(clones) == 1
    assert _branch_variable(clones[0]) in variables


def test_without_the_code_ref_the_clone_uses_main(code: str) -> None:
    variables = _code_ref_variables(code)
    parsing = OPTION_PARSING.search(code)
    defaults = [
        found.start()
        for variable in variables
        for found in re.finditer(rf"(?m)^{variable}=\"?main\"?$", code)
    ]

    assert variables != []
    assert parsing is not None
    assert len(defaults) == 1
    assert defaults[0] < parsing.start()


@pytest.mark.parametrize(
    "words",
    [
        pytest.param([*REQUIRED, "--ref", "v9"], id="with-value"),
        pytest.param([*REQUIRED, "--ref"], id="without-value"),
    ],
)
def test_the_old_ref_option_is_refused_with_a_hint(tmp_path: Path, words: list[str]) -> None:
    folder = tmp_path / "bin"
    folder.mkdir()
    log = tmp_path / "calls.log"
    for name in STAND_INS:
        stand_in = folder / name
        stand_in.write_text(f"#!/bin/sh\necho {name} >> {log}\n", encoding="utf-8")
        stand_in.chmod(0o755)
    before = entries(tmp_path)

    result = run_setup(tmp_path, words, path=f"{folder}:{SYSTEM_PATH}")

    assert result.exit_status == 2
    lines = result.stderr.splitlines()
    assert lines[0] == HINT
    assert lines[1].startswith("usage: setup.sh")
    assert entries(tmp_path) == before


@pytest.mark.parametrize(
    "words",
    [
        pytest.param(["--help"], id="help"),
        pytest.param([*REQUIRED, "--bogus"], id="fault"),
    ],
)
def test_the_usage_text_names_the_code_ref_and_not_the_ref(
    tmp_path: Path, words: list[str]
) -> None:
    result = run_setup(tmp_path, words)

    usage = result.stdout if words == ["--help"] else result.stderr
    assert usage.splitlines()[int(words != ["--help"])].startswith("usage: setup.sh")
    assert "--code-ref" in usage
    assert OLD_OPTION.search(usage) is None
