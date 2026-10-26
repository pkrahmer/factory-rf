"""The setup script's step `caches`: the cache drop helper and the rule that lets factory run it."""

import re
from collections.abc import Callable
from dataclasses import dataclass

import pytest

from vm_support import SETUP, function_text, step_texts

HELPER = "/usr/local/bin/factory-drop-caches"
SUDOERS = "/etc/sudoers.d/factory-drop-caches"
HELPER_LINES = ("#!/bin/sh", "sync", "echo 1 > /proc/sys/vm/drop_caches")
RULE = f"factory ALL=(root) NOPASSWD: {HELPER}"
REFUSED = f"setup: caches: visudo -cf refused {SUDOERS}; removed it"
COMPARISONS = re.compile(r"(?<![\w-])(?:cmp|diff|grep\s+(?:-\w*x\w*\s+|.*\s-\w*x))")


@dataclass(frozen=True)
class Script:
    """The setup script's raw text, its text without comment lines and the step `caches`."""

    raw: str
    code: str
    caches: str


@pytest.fixture
def script(code: str) -> Script:
    """Return the setup script's texts and its step `caches`."""
    return Script(SETUP.read_text(encoding="utf-8"), code, step_texts(code)["caches"])


def _in_order(text: str, words: list[str]) -> bool:
    positions = [text.find(word) for word in words]
    return -1 not in positions and positions == sorted(positions)


def _outside_caches(script: Script, word: str) -> list[str]:
    before, _, after = script.code.partition(script.caches)
    return [line for line in (before + after).splitlines() if word in line]


@pytest.mark.parametrize(
    "check",
    [
        pytest.param(
            lambda s: _in_order(
                s.code, ["setup: sudoers: ", "setup: caches: ", "setup: folders: "]
            ),
            id="after-sudoers-before-folders",
        ),
        pytest.param(
            # The shebang is a comment line to the dropping, so the three lines are read raw.
            lambda s: (
                "\n".join(HELPER_LINES) + "\n" in s.raw
                and _in_order(s.caches, list(HELPER_LINES[1:]))
            ),
            id="helper-lines",
        ),
        pytest.param(
            lambda s: _in_order(s.caches, ["install -m 0755", HELPER]), id="install-helper"
        ),
        pytest.param(lambda s: SUDOERS in s.caches, id="sudoers-file"),
        pytest.param(lambda s: "chmod 0440" in s.caches, id="chmod"),
        pytest.param(lambda s: "visudo -cf" in s.caches, id="visudo"),
        pytest.param(lambda s: f"rm -f {SUDOERS}" in s.caches, id="removes-refused"),
        pytest.param(lambda s: "$sudoers" not in s.caches, id="every-run"),
        pytest.param(
            lambda s: s.code.count(RULE) == 1 and RULE in s.caches, id="one-rule-in-the-step"
        ),
        pytest.param(
            lambda s: _outside_caches(s, "/proc/sys/vm/drop_caches") == [],
            id="drop-only-in-the-step",
        ),
    ],
)
def test_the_caches_step_writes_the_helper_and_its_rule(
    script: Script, check: Callable[[Script], bool]
) -> None:
    assert check(script)


def test_a_refused_visudo_check_removes_the_rule_and_ends_the_script(script: Script) -> None:
    lines = script.caches.splitlines()
    refused = [index for index, line in enumerate(lines) if REFUSED in line]

    assert refused != []
    assert ">&2" in lines[refused[0]]
    assert any(line.strip() == "exit 1" for line in lines[refused[0] + 1 :])


def _compares(code: str, line: str, path: str) -> bool:
    # A comparison is written in the line, or in the script's function the line calls.
    if path not in line:
        return False
    if COMPARISONS.search(line):
        return True
    for name in re.findall(r"(?<![\w-])([a-z_]\w*)\s", line):
        try:
            body = function_text(code, name)
        except StopIteration:
            continue
        if COMPARISONS.search(body):
            return True
    return False


def _writes(line: str, path: str) -> bool:
    return path in line and (
        re.search(r"(?<![\w-])(?:install|cp|mv|tee)\s", line) is not None
        or re.search(rf">\s*[\"']?{re.escape(path)}", line) is not None
    )


@pytest.mark.parametrize(
    "path", [pytest.param(HELPER, id="helper"), pytest.param(SUDOERS, id="sudoers")]
)
def test_the_caches_step_writes_a_file_only_when_its_text_differs(
    script: Script, path: str
) -> None:
    lines = script.caches.splitlines()
    compared = [index for index, line in enumerate(lines) if _compares(script.code, line, path)]
    written = [index for index, line in enumerate(lines) if _writes(line, path)]

    assert compared != []
    assert written != []
    assert compared[0] < written[0]
    assert f"wrote {path}" in script.caches
    assert any("found" in line and path in line for line in lines)
