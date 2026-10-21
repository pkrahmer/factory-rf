"""The instance name the tests use is written in one module, which the others import it from."""

import ast
from pathlib import Path

import pytest

TESTS = Path(__file__).parent


def instance_copies(source: str) -> list[str]:
    """The names that a top-level assignment in `source` gives the value `"factory-1"`."""
    names: list[str] = []
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        else:
            continue
        if isinstance(value, ast.Constant) and value.value == "factory-1":
            names.extend(target.id for target in targets if isinstance(target, ast.Name))
    return names


def test_the_instance_name_is_assigned_in_one_module() -> None:
    copies = sorted(
        path.relative_to(TESTS).as_posix()
        for path in TESTS.rglob("*.py")
        if instance_copies(path.read_text(encoding="utf-8"))
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
    assert instance_copies(source) == names
