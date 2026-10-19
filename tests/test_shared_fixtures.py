"""The shared fixtures of `tests/conftest.py` are defined there once, never copied into a module."""

import re
from pathlib import Path

TESTS = Path(__file__).parent


def _defining(signature: str) -> list[str]:
    pattern = re.compile(rf"^{re.escape(signature)}", re.MULTILINE)
    return sorted(
        path.relative_to(TESTS).as_posix()
        for path in TESTS.rglob("*.py")
        if pattern.search(path.read_text(encoding="utf-8"))
    )


def test_the_definition_fixture_is_defined_only_in_conftest() -> None:
    assert _defining("def definition(boundaries: Boundaries)") == ["conftest.py"]


def test_the_agents_fixture_is_defined_only_in_conftest() -> None:
    assert _defining("def installed_agents(") == ["conftest.py"]
    assert _defining("def _agents(agent_home: Path, boundaries: Boundaries)") == []
