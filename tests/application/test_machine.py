"""The clock, the factory log and the health status store are abstract base classes."""

import ast
import inspect
from abc import ABC
from pathlib import Path

import pytest

from factory.adapters.clock import ManualClock, SystemClock
from factory.adapters.factory_log import TimestampedFactoryLog
from factory.adapters.health_file import JsonHealthStatusFile
from factory.application.machine import Clock, FactoryLog, HealthStatusStore

INTERFACES: list[tuple[type[object], set[str], list[type[object]]]] = [
    (Clock, {"now"}, [SystemClock, ManualClock]),
    (FactoryLog, {"line"}, [TimestampedFactoryLog]),
    (HealthStatusStore, {"read", "write"}, [JsonHealthStatusFile]),
]
IDS = ["clock", "factory-log", "health-status-store"]


def _abstract_functions(interface: type[object]) -> list[ast.FunctionDef]:
    path = Path(inspect.getfile(interface))
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[ast.FunctionDef] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == interface.__name__:
            found.extend(
                function
                for function in node.body
                if isinstance(function, ast.FunctionDef)
                and any(
                    (isinstance(decorator, ast.Name) and decorator.id == "abstractmethod")
                    or (isinstance(decorator, ast.Attribute) and decorator.attr == "abstractmethod")
                    for decorator in function.decorator_list
                )
            )
    return found


@pytest.mark.parametrize(("interface", "operations", "implementations"), INTERFACES, ids=IDS)
def test_each_machine_interface_is_an_abstract_base_class_of_its_operations(
    interface: type[object], operations: set[str], implementations: list[type[object]]
) -> None:
    assert issubclass(interface, ABC)
    assert set(getattr(interface, "__abstractmethods__", frozenset())) == operations
    with pytest.raises(TypeError):
        interface()

    functions = _abstract_functions(interface)
    assert {function.name for function in functions} == operations
    for function in functions:
        assert len(function.body) == 1, function.name
        statement = function.body[0]
        assert isinstance(statement, ast.Expr), function.name
        assert isinstance(statement.value, ast.Constant), function.name
        assert isinstance(statement.value.value, str), function.name

    for implementation in implementations:
        assert issubclass(implementation, interface), implementation.__name__
