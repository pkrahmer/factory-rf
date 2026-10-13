"""The pipeline definition reader is an abstract interface the boundaries hand out."""

import ast
import inspect
from abc import ABC
from pathlib import Path

import pytest

from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.application.boundaries import Boundaries
from factory.application.files import PipelineDefinitionReader


def _class_source(cls: type[object]) -> ast.ClassDef:
    path = Path(inspect.getfile(cls))
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == cls.__name__
    )


def test_pipeline_definition_reader_is_abstract_with_parse_alone() -> None:
    interface: type[object] = PipelineDefinitionReader

    assert issubclass(PipelineDefinitionReader, ABC)
    assert PipelineDefinitionReader.__abstractmethods__ == {"parse"}
    with pytest.raises(TypeError):
        interface()


def test_pipeline_definition_reader_parse_body_is_its_docstring_alone() -> None:
    functions = [
        node
        for node in _class_source(PipelineDefinitionReader).body
        if isinstance(node, ast.FunctionDef)
    ]

    assert [function.name for function in functions] == ["parse"]
    statement = functions[0].body
    assert len(statement) == 1
    assert isinstance(statement[0], ast.Expr)
    assert isinstance(statement[0].value, ast.Constant)
    assert isinstance(statement[0].value.value, str)


def test_ruamel_reader_implements_the_pipeline_definition_reader() -> None:
    assert issubclass(RuamelPipelineDefinitionReader, PipelineDefinitionReader)


def test_boundaries_hand_out_the_ruamel_pipeline_reader(boundaries: Boundaries) -> None:
    assert isinstance(boundaries.pipeline_reader, RuamelPipelineDefinitionReader)
