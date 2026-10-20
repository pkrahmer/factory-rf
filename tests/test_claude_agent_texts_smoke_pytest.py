"""The intake rule on smoke test commands that pass pytest a `-q` its configuration already sets."""

import pytest

from factory.domain.sections import section_text
from shipped_agents import agent_body

_RULE = (
    "A smoke test command that runs pytest passes no `-q` when the project's pytest "
    "configuration already sets one (`addopts` in `pyproject.toml`, `pytest.ini`, `setup.cfg` "
    "or `tox.ini`): at `-qq` pytest prints no summary line, so an `Expect:` that counts or names "
    "it cannot be met. Such a command is a question."
)
_RULE_MARK = "passes no `-q` when the project's pytest configuration already sets one"
_STEP_TWO_START = "2. The factory has already checked the story's form"
_STEP_TWO_JOIN = (
    "each `Expect:` line says something the output can be checked against. "
    "A smoke test command that runs pytest passes no `-q` "
)
_STEP_TWO_END = "Such a command is a question."


def _intake_stage() -> str:
    return section_text(agent_body("intake"), "Stage") or ""


def test_intake_stage_holds_the_pytest_quiet_rule() -> None:
    assert _RULE in _intake_stage()


def test_pytest_quiet_rule_ends_step_two_of_intake() -> None:
    lines = [line for line in _intake_stage().splitlines() if line.startswith(_STEP_TWO_START)]
    assert len(lines) == 1
    assert _STEP_TWO_JOIN in lines[0]
    assert lines[0].endswith(_STEP_TWO_END)


@pytest.mark.parametrize(
    ("name", "count"),
    [
        pytest.param("intake", 1, id="intake"),
        pytest.param("tester", 0, id="tester"),
        pytest.param("coder", 0, id="coder"),
        pytest.param("reviewer", 0, id="reviewer"),
        pytest.param("documenter", 0, id="documenter"),
        pytest.param("smoke-tester", 0, id="smoke-tester"),
        pytest.param("acceptance-reviewer", 0, id="acceptance-reviewer"),
    ],
)
def test_only_intake_carries_the_pytest_quiet_rule(name: str, count: int) -> None:
    assert agent_body(name).count(_RULE_MARK) == count
