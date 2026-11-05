"""The probe, project agent and entrypoint test helpers are written in one shared place each."""

import re
from pathlib import Path

import pytest

from support.search_support import modules_matching

TESTS = Path(__file__).parents[1]
# The texts below are split so that a search of `tests` for them finds only their one module.
THIS = Path(__file__).name


@pytest.mark.parametrize(
    ("pattern", "module"),
    [
        pytest.param(
            re.escape("ENVIRONMENT = " + '{"PATH": "/opt/factory/bin:/usr/bin"'),
            "support/probe_support.py",
            id="environment",
        ),
        pytest.param(
            r'^COMPLETED = AgentRunResult\([^)]*entry="probe"',
            "support/probe_support.py",
            id="completed",
        ),
        pytest.param(
            re.escape("PROJECT_CODER = " + "AGENT_FILE.replace("),
            "support/git_support.py",
            id="project-coder",
        ),
    ],
)
def test_each_shared_helper_is_written_in_one_module(pattern: str, module: str) -> None:
    assert modules_matching(pattern, THIS) == [module]
