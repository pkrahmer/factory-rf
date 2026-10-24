"""The instance name the tests use is written in one module, which the others import it from."""

import pytest

from search_support import modules_assigning, top_level_copies


def test_the_instance_name_is_assigned_in_one_module() -> None:
    assert modules_assigning("factory-1") == ["stage_run_support.py"]


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
