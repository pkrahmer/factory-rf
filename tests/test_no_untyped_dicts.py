"""No function under `src/factory` takes or returns a mapping to `Any`."""

import ast
from pathlib import Path

import factory

SRC = Path(factory.__file__).parent
MAPPINGS = {"dict", "Dict", "Mapping", "MutableMapping"}


def _name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _is_any_mapping(node: ast.Subscript) -> bool:
    if _name(node.value) not in MAPPINGS:
        return False
    if not isinstance(node.slice, ast.Tuple) or len(node.slice.elts) != 2:
        return False
    return _name(node.slice.elts[1]) == "Any"


def _has_any_mapping(annotation: ast.expr | None) -> bool:
    if annotation is None:
        return False
    if isinstance(annotation, ast.Constant) and isinstance(annotation.value, str):
        return _has_any_mapping(ast.parse(annotation.value, mode="eval").body)
    for node in ast.walk(annotation):
        if isinstance(node, ast.Subscript) and _is_any_mapping(node):
            return True
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node is not annotation
            and _has_any_mapping(node)
        ):
            return True
    return False


def _offenders(source: str, filename: str) -> list[str]:
    found: list[str] = []
    for node in ast.walk(ast.parse(source, filename=filename)):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        arguments = node.args
        parameters = [
            *arguments.posonlyargs,
            *arguments.args,
            *arguments.kwonlyargs,
            *([arguments.vararg] if arguments.vararg else []),
            *([arguments.kwarg] if arguments.kwarg else []),
        ]
        annotations = [parameter.annotation for parameter in parameters] + [node.returns]
        if any(_has_any_mapping(annotation) for annotation in annotations):
            found.append(f"{filename}:{node.lineno} {node.name}")
    return found


def test_the_search_finds_a_mutable_mapping_to_any() -> None:
    source = (
        "from collections.abc import MutableMapping\n"
        "from typing import Any\n"
        "def f(x: int, y: MutableMapping[str, Any]) -> None: ...\n"
    )

    assert _offenders(source, "snippet.py") == ["snippet.py:3 f"]


def test_the_search_finds_nested_and_qualified_mappings_to_any() -> None:
    source = (
        "import typing, collections.abc\n"
        "def a() -> list[dict[str, Any]]: ...\n"
        "def b(x: typing.Mapping[str, typing.Any]) -> None: ...\n"
        "def c(x: 'collections.abc.Mapping[str, Any] | None') -> None: ...\n"
        "class K:\n"
        "    def d(self, *, x: tuple[int, dict[str, Any]]) -> None: ...\n"
        "def ok(x: dict[str, int], y: Mapping[Any, str]) -> dict[str, object]: ...\n"
    )

    assert [entry.split()[1] for entry in _offenders(source, "snippet.py")] == ["a", "b", "c", "d"]


def test_no_function_in_the_package_has_a_mapping_to_any() -> None:
    found: list[str] = []
    for path in sorted(SRC.rglob("*.py")):
        found.extend(_offenders(path.read_text(encoding="utf-8"), str(path.relative_to(SRC))))

    assert found == []
