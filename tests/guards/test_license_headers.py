"""Every Python module of the package and every operator script names its license in its header."""

import os
from pathlib import Path

import pytest

from factory.shared.adapters.process import ProcessRequest, run_process
from support.git_support import run_git

ROOT = Path(__file__).parents[2]
HEADER = "# SPDX-License-Identifier: Apache-2.0"
SHEBANG = "#!"
PACKAGE = "src/factory/"
OPERATOR = "operator/"
TEMPLATE = "operator/template/"
BASH_SHEBANGS = ("#!/bin/bash", "#!/usr/bin/env bash")
SH_SHEBANGS = ("#!/bin/sh", "#!/usr/bin/env sh")


def _first_line(text: str) -> str:
    return text.split("\n", 1)[0]


def in_scope(path: str, first_line: str) -> bool:
    """Whether the tracked file `path`, whose first line is `first_line`, must carry the header."""
    if path.startswith(PACKAGE):
        return path.endswith(".py")
    if not path.startswith(OPERATOR) or path.startswith(TEMPLATE):
        return False
    name = path.rsplit("/", 1)[-1]
    return name.endswith(".sh") or name == "Dockerfile" or first_line.startswith(SHEBANG)


def _script_line(text: str) -> str:
    """The line that says whether `text` is a script: its first, or the one after a header."""
    lines = text.split("\n")
    if lines[0] == HEADER and len(lines) > 1:
        return lines[1]
    return lines[0]


def carries_header(text: str) -> bool:
    """Whether `text` holds the header on its first line, or on the line after its shebang."""
    lines = text.split("\n")
    if lines[0].startswith(SHEBANG):
        return len(lines) > 1 and lines[1] == HEADER
    # A shebang below the header is no shebang: the header stands before it.
    return lines[0] == HEADER and not _script_line(text).startswith(SHEBANG)


def unlicensed(root: Path, paths: list[str]) -> list[str]:
    """The paths among `paths`, relative to `root`, in the scope and without the header."""
    missing = []
    for path in paths:
        text = (root / path).read_text(encoding="utf-8")
        if in_scope(path, _script_line(text)) and not carries_header(text):
            missing.append(path)
    return missing


def _tracked() -> list[str]:
    return run_git(ROOT, "ls-files").splitlines()


def _scripts() -> list[tuple[str, str]]:
    """Each operator script in the scope with its first line."""
    found = []
    for path in _tracked():
        if not path.startswith(OPERATOR):
            continue
        first = _first_line((ROOT / path).read_text(encoding="utf-8"))
        if in_scope(path, first):
            found.append((path, first))
    return found


def test_every_file_in_scope_carries_the_license_header() -> None:
    assert unlicensed(ROOT, _tracked()) == []


MODULE_BODY = '"""A module."""\n\nVALUE = 1\n'
SCRIPT_BODY = "set -eu\necho done\n"


@pytest.mark.parametrize(
    ("path", "text", "passes"),
    [
        pytest.param("src/factory/area/module.py", MODULE_BODY, False, id="module-without"),
        pytest.param(
            "src/factory/area/module.py",
            f'"""A module."""\n{HEADER}\n\nVALUE = 1\n',
            False,
            id="module-header-after-docstring",
        ),
        pytest.param(
            "src/factory/area/module.py",
            f"\n{HEADER}\n{MODULE_BODY}",
            False,
            id="module-header-after-another-line",
        ),
        pytest.param(
            "src/factory/area/module.py", f"{HEADER}\n{MODULE_BODY}", True, id="module-header-first"
        ),
        pytest.param(
            "operator/bin/tool",
            f"{HEADER}\n#!/bin/sh\n{SCRIPT_BODY}",
            False,
            id="header-before-shebang",
        ),
        pytest.param(
            "operator/vm/Dockerfile",
            "# The image.\nFROM debian\n",
            False,
            id="dockerfile-without",
        ),
        pytest.param(
            "operator/lib/library.sh",
            f"# A library.\n{SCRIPT_BODY}",
            False,
            id="sh-file-without",
        ),
        pytest.param(
            "operator/bin/tool",
            f"#!/bin/sh\n{HEADER}\n{SCRIPT_BODY}",
            True,
            id="header-after-shebang",
        ),
        pytest.param(
            "operator/lib/library.sh",
            f"{HEADER}\n{SCRIPT_BODY}",
            True,
            id="sh-file-header-first",
        ),
        pytest.param(
            "operator/vm/Dockerfile",
            f"{HEADER}\nFROM debian\n",
            True,
            id="dockerfile-header-first",
        ),
    ],
)
def test_the_guard_names_a_file_without_the_header_in_its_place(
    tmp_path: Path, path: str, text: str, passes: bool
) -> None:
    file = tmp_path / path
    file.parent.mkdir(parents=True)
    file.write_text(text, encoding="utf-8")

    assert unlicensed(tmp_path, [path]) == ([] if passes else [path])


@pytest.mark.parametrize(
    ("path", "first_line", "inside"),
    [
        pytest.param("tests/guards/test_module.py", '"""A test."""', False, id="test-module"),
        pytest.param("operator/template/bin/tool.sh", "#!/bin/sh", False, id="template-script"),
        pytest.param("operator/README.md", "# The operator folder", False, id="readme"),
        pytest.param("operator/settings.json", "{", False, id="json-without-shebang"),
        pytest.param("operator/vm/Dockerfile", "# The image.", True, id="dockerfile"),
        pytest.param("operator/lib/library.sh", "# A library.", True, id="sh-file-without-shebang"),
    ],
)
def test_the_scope_holds_package_modules_and_operator_scripts_only(
    path: str, first_line: str, inside: bool
) -> None:
    assert in_scope(path, first_line) == inside


def _syntax_checker(path: str, first_line: str) -> str | None:
    if first_line.startswith(BASH_SHEBANGS):
        return "bash"
    if first_line.startswith(SH_SHEBANGS) or (
        path.endswith(".sh") and not first_line.startswith(SHEBANG)
    ):
        return "sh"
    return None


def test_every_operator_script_still_parses() -> None:
    failures = []
    for path, first in _scripts():
        shell = _syntax_checker(path, first)
        if shell is None:
            continue
        result = run_process(
            ProcessRequest(
                argv=[shell, "-n", str(ROOT / path)],
                cwd=ROOT,
                env={"PATH": os.environ["PATH"]},
                merge_stderr=True,
            )
        )
        if result.exit_status != 0:
            failures.append(f"{path}: {result.stdout}")

    assert failures == []
