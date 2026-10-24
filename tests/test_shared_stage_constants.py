"""The stage tests' shared values are each written in one module, which the others import from."""

import pytest

from search_support import modules_assigning


@pytest.mark.parametrize(
    ("value", "home"),
    [
        pytest.param("written by the agent\n", "take_support.py", id="agent-text"),
        pytest.param("tests/test_a.py", "stage_run_support.py", id="inside"),
        pytest.param("notes.md", "stage_run_support.py", id="notes"),
    ],
)
def test_a_shared_stage_value_is_assigned_only_in_its_home(value: str, home: str) -> None:
    assert modules_assigning(value) == [home]
