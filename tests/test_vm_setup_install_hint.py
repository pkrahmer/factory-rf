"""The setup script's lines for an installed file that differs from the checkout, and its syntax."""

from pathlib import Path

import pytest

from factory.adapters.process import ProcessRequest, run_process
from vm_support import SETUP, step_texts

HINTS = {
    "tools": (
        "setup: tools: /usr/local/bin/git-credential-factory differs from the checkout;"
        " not installed; install it from your own copy of vm/git-credential-factory"
        ' (operator guide, "The rebuild after a merge")'
    ),
    "service": (
        "setup: service: /etc/systemd/system/factory@.service differs from the checkout;"
        " not installed; install it from your own copy of vm/factory.service"
        ' (operator guide, "The rebuild after a merge")'
    ),
}


@pytest.mark.parametrize("step", ["tools", "service"])
def test_a_differing_installed_file_names_the_operators_own_copy(code: str, step: str) -> None:
    hint = HINTS[step]
    step_text = step_texts(code)[step]

    assert step_text.count(hint) == 1
    hint_lines = [line for line in step_text.splitlines() if hint in line]
    assert len(hint_lines) == 1
    assert ">&2" in hint_lines[0]
    differing = [line for line in code.splitlines() if "differs from the checkout" in line]
    assert len(differing) == 2
    assert all(any(text in line for text in HINTS.values()) for line in differing)


def test_the_setup_script_parses(tmp_path: Path) -> None:
    result = run_process(ProcessRequest(argv=["sh", "-n", str(SETUP)], cwd=tmp_path))

    assert result.exit_status == 0, result.stderr
