"""The stage tests' shared values are each written in one module, which the others import from."""

from pathlib import Path

import pytest

from search_support import top_level_copies

TESTS = Path(__file__).parent


@pytest.mark.parametrize(
    ("value", "home"),
    [
        pytest.param("written by the agent\n", "take_support.py", id="agent-text"),
        pytest.param("tests/test_a.py", "stage_run_support.py", id="inside"),
        pytest.param("notes.md", "stage_run_support.py", id="notes"),
    ],
)
def test_a_shared_stage_value_is_assigned_only_in_its_home(value: str, home: str) -> None:
    copies = sorted(
        path.relative_to(TESTS).as_posix()
        for path in TESTS.rglob("*.py")
        if top_level_copies(path.read_text(encoding="utf-8"), value)
    )

    assert copies == [home]
