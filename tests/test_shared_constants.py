"""The instance name the tests use is written in one module, which the others import it from."""

from pathlib import Path

import pytest

from search_support import top_level_copies

TESTS = Path(__file__).parent


def test_the_instance_name_is_assigned_in_one_module() -> None:
    copies = sorted(
        path.relative_to(TESTS).as_posix()
        for path in TESTS.rglob("*.py")
        if top_level_copies(path.read_text(encoding="utf-8"), "factory-1")
    )

    assert copies == ["stage_run_support.py"]


@pytest.mark.parametrize(
    ("source", "names"),
    [
        pytest.param('INSTANCE = "factory-1"\n', ["INSTANCE"], id="plain"),
        pytest.param('OWN = "factory-1"\n', ["OWN"], id="other-name"),
        pytest.param('NAME: str = "factory-1"\n', ["NAME"], id="annotated"),
        pytest.param('INSTANCE = "factory-7"\n', [], id="other-value"),
        pytest.param("OWN = INSTANCE\n", [], id="name-as-value"),
        pytest.param('def f():\n    name = "factory-1"\n', [], id="in-function"),
        pytest.param('class C:\n    NAME = "factory-1"\n', [], id="in-class"),
    ],
)
def test_the_guard_counts_a_top_level_assignment_of_the_instance_name(
    source: str, names: list[str]
) -> None:
    assert top_level_copies(source, "factory-1") == names
