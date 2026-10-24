"""The four interfaces are abstract base classes whose operations are all abstract."""

import ast
import inspect
from abc import ABC
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path
from typing import get_type_hints

import pytest

from application.test_git_interface import OPERATIONS as GIT_OPERATIONS
from application.test_hosting_interface import OPERATIONS as HOSTING_OPERATIONS
from factory.application.agent_runtime import AgentRuntime
from factory.application.containers import ContainerRuns
from factory.application.git import Git
from factory.application.hosting import HostingService
from factory.application.project_commands import ProjectCommands
from factory.application.snapshots import Snapshots
from factory.domain.checks import CheckResult

INTERFACES: list[type[object]] = [
    Git,
    HostingService,
    ProjectCommands,
    AgentRuntime,
    Snapshots,
    ContainerRuns,
]
INTERFACE_IDS = [
    "git",
    "hosting",
    "project-commands",
    "agent-runtime",
    "snapshots",
    "container-runs",
]
TESTS = Path(__file__).parent.parent


def _source(interface: type[object]) -> ast.Module:
    path = Path(inspect.getfile(interface))
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _is_abstract(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any(
        (isinstance(decorator, ast.Name) and decorator.id == "abstractmethod")
        or (isinstance(decorator, ast.Attribute) and decorator.attr == "abstractmethod")
        for decorator in function.decorator_list
    )


@pytest.mark.parametrize("interface", INTERFACES, ids=INTERFACE_IDS)
def test_each_interface_is_an_abstract_base_class(interface: type[object]) -> None:
    assert issubclass(interface, ABC)


@pytest.mark.parametrize("interface", INTERFACES, ids=INTERFACE_IDS)
def test_no_class_in_the_interface_modules_derives_from_protocol(
    interface: type[object],
) -> None:
    bases = [
        base
        for node in ast.walk(_source(interface))
        if isinstance(node, ast.ClassDef)
        for base in node.bases
        if (isinstance(base, ast.Name) and base.id == "Protocol")
        or (isinstance(base, ast.Attribute) and base.attr == "Protocol")
    ]

    assert bases == []


def test_git_abstract_methods_are_exactly_its_twenty_five_operations() -> None:
    assert Git.__abstractmethods__ == GIT_OPERATIONS


def test_hosting_abstract_methods_are_its_ten_operations_with_their_return_types() -> None:
    assert HostingService.__abstractmethods__ == set(HOSTING_OPERATIONS)
    for name, expected in HOSTING_OPERATIONS.items():
        assert get_type_hints(getattr(HostingService, name))["return"] == expected, name


def test_project_commands_and_agent_runtime_have_exactly_their_operations_abstract() -> None:
    assert ProjectCommands.__abstractmethods__ == {"run"}
    assert AgentRuntime.__abstractmethods__ == {"run", "version"}
    assert Snapshots.__abstractmethods__ == {"mount_point", "reset", "advance", "changed_paths"}
    assert ContainerRuns.__abstractmethods__ == {"launch", "run"}


@pytest.mark.parametrize("interface", INTERFACES, ids=INTERFACE_IDS)
def test_an_interface_has_no_public_member_but_its_abstract_operations(
    interface: type[object],
) -> None:
    public = {name for name in dir(interface) if not name.startswith("_")}

    assert public == set(getattr(interface, "__abstractmethods__", frozenset()))


@pytest.mark.parametrize("interface", INTERFACES, ids=INTERFACE_IDS)
def test_every_abstract_method_body_is_its_docstring_alone(interface: type[object]) -> None:
    functions = [
        node
        for node in ast.walk(_source(interface))
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and _is_abstract(node)
    ]

    assert functions != []
    for function in functions:
        assert len(function.body) == 1, function.name
        statement = function.body[0]
        assert isinstance(statement, ast.Expr), function.name
        assert isinstance(statement.value, ast.Constant), function.name
        assert isinstance(statement.value.value, str), function.name


@pytest.mark.parametrize("interface", INTERFACES, ids=INTERFACE_IDS)
def test_an_interface_cannot_be_instantiated(interface: type[object]) -> None:
    with pytest.raises(TypeError):
        interface()


def test_a_subclass_must_implement_every_operation_to_be_constructed() -> None:
    class Incomplete(ProjectCommands):
        pass

    class Complete(ProjectCommands):
        def run(self, command: str, *, time_limit: timedelta) -> CheckResult:
            raise AssertionError((command, time_limit))

    incomplete: Callable[[], object] = Incomplete
    with pytest.raises(TypeError):
        incomplete()
    assert isinstance(Complete(), ProjectCommands)


def test_no_test_asserts_an_interface_is_absent_from_an_mro() -> None:
    found: list[str] = []
    for path in sorted(TESTS.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        found.extend(
            f"{path.relative_to(TESTS)}:{node.lineno}"
            for node in ast.walk(tree)
            if isinstance(node, ast.Compare)
            for operator, right in zip(node.ops, node.comparators, strict=True)
            if isinstance(operator, ast.NotIn)
            and isinstance(right, ast.Attribute)
            and right.attr == "__mro__"
        )

    assert found == []
