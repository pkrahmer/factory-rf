"""Each environment the tests share is written in one module, which the others import it from."""

import ast
from collections.abc import Mapping
from pathlib import Path

import pytest

import stage_run_support
import wiring_support

TESTS = Path(__file__).parent
SHARED: dict[str, dict[str, str]] = {
    "stage_run_support.py": stage_run_support.ENVIRONMENT,
    "wiring_support.py": wiring_support.ENVIRONMENT,
}
SCRIPTS = '{"PATH": "/opt/scripts:/usr/bin:/bin", "HOME": "/home/factory"}'


def environment_copies(source: str, environment: Mapping[str, str]) -> list[str]:
    """The top-level names that `source` assigns a dict literal equal to `environment`."""
    names: list[str] = []
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        else:
            continue
        if isinstance(value, ast.Dict) and _literal(value) == dict(environment):
            names.extend(target.id for target in targets if isinstance(target, ast.Name))
    return names


def _literal(value: ast.Dict) -> object:
    # A dict that holds a name, such as `{"PATH": PATH}`, is no literal and copies no value.
    try:
        return ast.literal_eval(value)
    except ValueError:
        return None


@pytest.fixture
def scripts_environment() -> dict[str, str]:
    """The environment the guard's own cases are read against, written inside a function."""
    return {"PATH": "/opt/scripts:/usr/bin:/bin", "HOME": "/home/factory"}


@pytest.mark.parametrize(
    ("module", "value", "expected"),
    [
        pytest.param(
            "stage_run_support.py",
            {"PATH": "/usr/local/bin:/usr/bin", "HOME": "/home/factory"},
            ["stage_run_support.py"],
            id="stage_run_support.py",
        ),
        pytest.param(
            "wiring_support.py",
            {"PATH": "/opt/scripts:/usr/bin:/bin", "HOME": "/home/factory"},
            ["wiring_support.py"],
            id="wiring_support.py",
        ),
    ],
)
def test_each_shared_environment_is_assigned_in_one_module(
    module: str, value: dict[str, str], expected: list[str]
) -> None:
    holding = sorted(
        path.relative_to(TESTS).as_posix()
        for path in TESTS.rglob("*.py")
        if environment_copies(path.read_text(encoding="utf-8"), SHARED[module])
    )

    assert (SHARED[module], holding) == (value, expected)


@pytest.mark.parametrize(
    ("source", "names"),
    [
        pytest.param(f"ENVIRONMENT = {SCRIPTS}\n", ["ENVIRONMENT"], id="plain"),
        pytest.param(f"HANDLER_ENV = {SCRIPTS}\n", ["HANDLER_ENV"], id="other-name"),
        pytest.param(f"ENVIRONMENT: dict[str, str] = {SCRIPTS}\n", ["ENVIRONMENT"], id="annotated"),
        pytest.param(
            'ENVIRONMENT = {"HOME": "/home/factory", "PATH": "/opt/scripts:/usr/bin:/bin"}\n',
            ["ENVIRONMENT"],
            id="home-first",
        ),
        pytest.param(
            'ENVIRONMENT = {"PATH": "/opt/guard", "HOME": "/home/factory"}\n', [], id="other-value"
        ),
        pytest.param(
            'ENVIRONMENT = {"PATH": "/opt/scripts:/usr/bin:/bin", "HOME": "/home/factory",'
            ' "LANG": "C.UTF-8"}\n',
            [],
            id="one-more-key",
        ),
        pytest.param("ENVIRONMENT = OTHER\n", [], id="name-as-value"),
        pytest.param(
            'ENVIRONMENT = dict(PATH="/opt/scripts:/usr/bin:/bin", HOME="/home/factory")\n',
            [],
            id="a-call",
        ),
        pytest.param(f"def f():\n    ENVIRONMENT = {SCRIPTS}\n", [], id="in-function"),
        pytest.param(f"class C:\n    ENVIRONMENT = {SCRIPTS}\n", [], id="in-class"),
    ],
)
def test_the_guard_counts_a_top_level_assignment_of_the_environment(
    scripts_environment: dict[str, str], source: str, names: list[str]
) -> None:
    assert environment_copies(source, scripts_environment) == names
