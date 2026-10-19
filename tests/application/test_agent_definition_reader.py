"""The agent definition reader is an abstract interface the boundaries hand out."""

import ast
import inspect
from abc import ABC
from pathlib import Path

import pytest

from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.application.agent_runtime import AgentDefinitionReader
from factory.application.boundaries import Boundaries
from factory.domain.errors import (
    AgentDefinitionError,
    AgentDefinitionInvalid,
    AgentDefinitionMissing,
    FactoryError,
)


def _class_source(cls: type[object]) -> ast.ClassDef:
    path = Path(inspect.getfile(cls))
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == cls.__name__
    )


def test_agent_definition_errors_carry_name_fault_and_key() -> None:
    error = AgentDefinitionError("coder", "no agent file x")
    missing = AgentDefinitionMissing("nobody", "no agent file y")
    invalid = AgentDefinitionInvalid("coder", "missing key: model", "model")

    assert issubclass(AgentDefinitionError, FactoryError)
    assert issubclass(AgentDefinitionMissing, AgentDefinitionError)
    assert issubclass(AgentDefinitionInvalid, AgentDefinitionError)
    assert (error.name, error.fault) == ("coder", "no agent file x")
    assert (missing.name, missing.fault) == ("nobody", "no agent file y")
    assert (invalid.name, invalid.fault, invalid.key) == ("coder", "missing key: model", "model")


def test_agent_definition_reader_is_abstract_with_names_and_read() -> None:
    interface: type[object] = AgentDefinitionReader

    assert issubclass(AgentDefinitionReader, ABC)
    assert AgentDefinitionReader.__abstractmethods__ == {"names", "parse", "read"}
    with pytest.raises(TypeError):
        interface()


def test_agent_definition_reader_methods_are_their_docstrings_alone() -> None:
    functions = [
        node
        for node in _class_source(AgentDefinitionReader).body
        if isinstance(node, ast.FunctionDef)
    ]

    assert sorted(function.name for function in functions) == ["names", "parse", "read"]
    for function in functions:
        assert len(function.body) == 1, function.name
        statement = function.body[0]
        assert isinstance(statement, ast.Expr), function.name
        assert isinstance(statement.value, ast.Constant), function.name
        assert isinstance(statement.value.value, str), function.name


def test_frontmatter_reader_implements_the_agent_definition_reader() -> None:
    assert issubclass(FrontmatterAgentDefinitionReader, AgentDefinitionReader)


def test_boundaries_hand_out_a_frontmatter_reader_on_the_agent_home(
    boundaries: Boundaries, agent_home: Path
) -> None:
    agents = agent_home / "agents"
    agents.mkdir(parents=True)
    (agents / "coder.md").write_text(
        "---\nmodel: sonnet\ntools: []\nbudget_usd: 1\n---\nCode.\n", encoding="utf-8"
    )

    assert isinstance(boundaries.agent_definitions, FrontmatterAgentDefinitionReader)
    assert boundaries.agent_definitions.names() == ["coder"]
